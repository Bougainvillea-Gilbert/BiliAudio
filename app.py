# -*- coding: utf-8 -*-
"""
本地 Web 后端：接收链接 → 后台线程提取 → 前端轮询进度 → 下载文件。
桌面模式（desktop.py）下由 pywebview 内嵌加载，不对外开端口。
"""
import os
import json
import re
import sys
import threading
import uuid

from flask import Flask, jsonify, render_template, request, send_file

from platform_utils import config_directory, pick_directory, save_zip_dialog, open_in_file_manager

from extract import (
    detect_proxy,
    extract_audio,
    fetch_info,
    is_supported_url,
    resolve_ffmpeg_path,
)

_ANSI_RE = re.compile(r"\x1b?\[[0-9;]*m")


def _clean_error(msg: str) -> str:
    """剥掉 yt-dlp 报错里的 ANSI 颜色码，前端直接显示。"""
    return _ANSI_RE.sub("", msg)

app = Flask(__name__)
if os.environ.get("BILI_AUDIO_APP_ROOT"):
    app.root_path = os.environ["BILI_AUDIO_APP_ROOT"]

# ---------------------------------------------------------------- 下载目录配置
# 优先级：环境变量(调试用) > 用户选择(持久化到 %APPDATA%/BiliAudio/config.json) > 系统下载文件夹
def _config_file():
    d = config_directory()
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "config.json")


def _load_config():
    try:
        with open(_config_file(), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


CONFIG = _load_config()


def get_download_dir():
    d = (
        os.environ.get("BILI_AUDIO_DOWNLOAD_DIR")
        or CONFIG.get("download_dir")
        or os.path.join(os.path.expanduser("~"), "Downloads")
    )
    os.makedirs(d, exist_ok=True)
    return d


def _save_config():
    try:
        with open(_config_file(), "w", encoding="utf-8") as f:
            json.dump(CONFIG, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def is_writable(d):
    """目标目录实际可写性探测（ACL/杀软/沙箱都以此为准）。"""
    try:
        p = os.path.join(d, ".biliaudio_write_test")
        with open(p, "wb") as f:
            f.write(b"1")
        os.remove(p)
        return True
    except Exception:
        return False


def _fallback_dir():
    """程序旁的 downloads，作为目标目录不可写时的兜底。"""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    d = os.path.join(base, "downloads")
    os.makedirs(d, exist_ok=True)
    return d


def _native_pick_directory(initial):
    return pick_directory(initial)


def _native_save_zip(initial_file):
    return save_zip_dialog(initial_file, get_download_dir())


# 任务表：task_id -> {status, percent, speed, eta, filename, paths, error}
TASKS = {}
TASKS_LOCK = threading.Lock()


def _update(task_id, **fields):
    with TASKS_LOCK:
        TASKS.setdefault(task_id, {}).update(fields)


def _run_task(task_id, urls, fmt, media_type, proxy, max_height):
    """按顺序下载一组 URL（勾选的若干集或整个合集）。
    单集失败不阻塞后续，最后汇总成功/失败。"""
    try:
        total = len(urls)
        all_paths, failures = [], []
        outdir = get_download_dir()
        note = None
        if not is_writable(outdir):
            fb = _fallback_dir()
            note = f"原目录无写入权限，已自动改存到 {fb}"
            outdir = fb
        for i, u in enumerate(urls, 1):
            _update(task_id, status="starting", item=f"{i}/{total}", percent=0.0, dir=outdir)

            def hook(d, i=i):
                d["item"] = f"{i}/{total}"
                _update(task_id, **d)

            try:
                paths = extract_audio(
                    u,
                    output_dir=outdir,
                    audio_format=fmt,
                    progress_hook=hook,
                    media_type=media_type,
                    proxy=proxy or None,
                    max_height=max_height,
                )
                all_paths.extend(paths)
            except Exception as e:
                msg = _clean_error(str(e))
                if "Permission denied" in msg or "WinError 5" in msg:
                    msg += "（写入被拒绝：可能是火绒等杀软的「文件夹保护」拦截，请把本程序加入信任，或点下方「更改」换个下载目录）"
                failures.append(f"第{i}集: {msg[:200]}")

        if not all_paths:
            _update(task_id, status="error",
                    error="全部失败；" + "；".join(failures[:3]))
            return
        _update(
            task_id,
            status="done",
            percent=100.0,
            filename=os.path.basename(all_paths[0]),
            paths=all_paths,
            count=len(all_paths),
            failures=failures,
            dir=outdir,
            note=note,
        )
    except Exception as e:
        _update(task_id, status="error", error=_clean_error(str(e)))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/icon.png")
def icon():
    return send_file(os.path.join(app.root_path, "assets", "icon.png"), mimetype="image/png")


@app.route("/api/check-env")
def check_env():
    path = resolve_ffmpeg_path()
    proxy = detect_proxy()
    return jsonify({
        "ffmpeg": path is not None,
        "ffmpeg_path": path,
        "proxy": proxy,
        "proxy_detected": proxy is not None,
    })


@app.route("/api/info", methods=["POST"])
def api_info():
    """只解析不下载：返回预览元数据 + 可用清晰度。"""
    url = (request.form.get("url") or "").strip()
    if not url:
        return jsonify({"error": "请输入视频链接"}), 400
    if not is_supported_url(url):
        return jsonify({"error": "不支持或无效的链接"}), 400
    proxy = (request.form.get("proxy") or "").strip() or None
    try:
        info = fetch_info(url, proxy=proxy)
        return jsonify(info)
    except Exception as e:
        return jsonify({"error": _clean_error(str(e))}), 500


@app.route("/api/extract", methods=["POST"])
def extract():
    url = (request.form.get("url") or "").strip()
    if not url:
        return jsonify({"error": "请输入视频链接"}), 400
    if not is_supported_url(url):
        return jsonify({"error": "不支持或无效的链接"}), 400

    fmt = request.form.get("format", "mp3")
    media_type = request.form.get("media_type", "audio")
    if fmt == "video":
        # 前端把「视频 MP4」放在 format 下拉里，这里转成 media_type
        media_type, fmt = "video", "mp3"
    if fmt not in ("mp3", "m4a", "aac"):
        fmt = "mp3"
    if media_type not in ("audio", "video"):
        media_type = "audio"
    proxy = (request.form.get("proxy") or "").strip()
    max_height = request.form.get("max_height", type=int)  # None=最高画质

    # 批量模式：前端把勾选的每集地址以 JSON 数组放在 urls 里；否则用单个 url
    urls = []
    urls_raw = (request.form.get("urls") or "").strip()
    if urls_raw:
        try:
            parsed = json.loads(urls_raw)
            if isinstance(parsed, list):
                urls = [str(u).strip() for u in parsed
                        if isinstance(u, str) and u.strip().lower().startswith(("http://", "https://"))]
        except (ValueError, TypeError):
            urls = []
    if not urls:
        urls = [url]
    urls = urls[:200]  # 上限保护

    task_id = uuid.uuid4().hex[:12]
    _update(task_id, status="queued", percent=0.0)
    threading.Thread(
        target=_run_task,
        args=(task_id, urls, fmt, media_type, proxy, max_height),
        daemon=True,
    ).start()
    return jsonify({"task_id": task_id})


@app.route("/api/task/<task_id>")
def task_status(task_id):
    with TASKS_LOCK:
        task = dict(TASKS.get(task_id) or {})
    if not task:
        return jsonify({"error": "任务不存在"}), 404
    task.pop("paths", None)  # 绝对路径列表仅供服务端使用
    if task.get("status") == "done" and task.get("filename"):
        task["download_url"] = "/api/task/" + task_id + "/download"
    return jsonify(task)


@app.route("/api/task/<task_id>/download")
def download(task_id):
    # 仅提供该任务的实际产物，支持备用目录和任务完成后更改保存位置。
    with TASKS_LOCK:
        task = dict(TASKS.get(task_id) or {})
    paths = task.get("paths") or []
    if task.get("status") != "done" or not paths or not os.path.isfile(paths[0]):
        return "文件不存在或已清理", 404
    return send_file(paths[0], as_attachment=True, download_name=os.path.basename(paths[0]))


@app.route("/api/config")
def api_config():
    return jsonify({"download_dir": get_download_dir()})


@app.route("/api/choose-dir", methods=["POST"])
def api_choose_dir():
    """弹 Windows 原生目录选择框，记住用户选择。"""
    try:
        chosen = _native_pick_directory(get_download_dir())
    except Exception as e:
        return jsonify({"error": _clean_error(str(e))}), 500
    if not chosen:
        return jsonify({"canceled": True, "download_dir": get_download_dir()})
    CONFIG["download_dir"] = chosen
    _save_config()
    return jsonify({
        "canceled": False,
        "download_dir": chosen,
        "writable": is_writable(chosen),
    })


@app.route("/api/open-folder", methods=["POST"])
def api_open_folder():
    """在资源管理器中打开下载目录；带 filename 时选中该文件。"""
    filename = (request.form.get("filename") or "").strip()
    base = os.path.normpath((request.form.get("dir") or "").strip() or get_download_dir())
    if not os.path.isdir(base):
        base = get_download_dir()
    target = base
    if filename:
        p = os.path.normpath(os.path.join(base, os.path.basename(filename)))
        if os.path.commonpath([p, base]) == base and os.path.isfile(p):
            target = p
    try:
        open_in_file_manager(target, select=target != base)
        return jsonify({"ok": True, "dir": base})
    except Exception as e:
        return jsonify({"error": _clean_error(str(e))}), 500


@app.route("/api/save-zip", methods=["POST"])
def api_save_zip():
    """把一次任务产出的全部文件打成 ZIP，用 Windows 原生另存为对话框选保存位置。"""
    import zipfile

    task_id = (request.form.get("task_id") or "").strip()
    with TASKS_LOCK:
        task = dict(TASKS.get(task_id) or {})
    paths = task.get("paths") or []
    if not paths:
        return jsonify({"error": "没有可打包的文件"}), 404

    first = os.path.splitext(os.path.basename(paths[0]))[0]
    default_name = f"{first[:40]} 等{len(paths)}个文件.zip" if len(paths) > 1 else first[:60] + ".zip"
    try:
        chosen = _native_save_zip(default_name)
    except Exception as e:
        return jsonify({"error": _clean_error(str(e))}), 500
    if not chosen:
        return jsonify({"canceled": True})

    try:
        with zipfile.ZipFile(chosen, "w", zipfile.ZIP_STORED) as zf:
            for p in paths:
                if os.path.isfile(p):
                    zf.write(p, arcname=os.path.basename(p))
        return jsonify({"canceled": False, "saved": chosen})
    except Exception as e:
        return jsonify({"error": _clean_error(str(e))}), 500


if __name__ == "__main__":
    # 仅供开发调试；日常使用请跑 run.py（只绑本机回环）
    app.run(host="127.0.0.1", port=5000, debug=False)
