# -*- coding: utf-8 -*-
"""
从 B 站视频提取纯音频。支持命令行和作为模块调用。
依赖: yt-dlp (https://github.com/yt-dlp/yt-dlp)
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import urllib.request

import yt_dlp


# 支持的链接形态（快速通道，校验用）：
#   https://www.bilibili.com/video/BV1xx411c7XX
#   https://www.bilibili.com/video/av170001
#   https://b23.tv/abc123          （APP 分享短链）
# 其它网站交给 yt-dlp 自己的 extractor 判断（支持 1800+ 站点）。
_BILI_VIDEO_PATTERN = re.compile(
    r"https?://(?:www\.)?bilibili\.com/video/(?:BV[\w]+|av\d+)",
    re.IGNORECASE,
)
# 各平台的 APP 分享短链域名，需要先跟随重定向拿真实地址
_SHORTLINK_PATTERN = re.compile(
    r"https?://(?:b23\.tv|v\.douyin\.com|xhslink\.com|t\.co|url\.cn)/[\w\-]+/?$",
    re.IGNORECASE,
)
_HTTP_PATTERN = re.compile(r"https?://\S+", re.IGNORECASE)

_EXTRACTORS = None


def _yt_dlp_supports(url: str) -> bool:
    """问 yt-dlp 自己有没有匹配的站点解析器（离线判断，不发请求）。
    排除 Generic 兜底解析器——它匹配任何 URL，会让我们失去校验意义。"""
    global _EXTRACTORS
    try:
        if _EXTRACTORS is None:
            _EXTRACTORS = [
                ie for ie in yt_dlp.extractor.gen_extractors()
                if ie.ie_key() not in ("Generic", "generic")
            ]
        return any(ie.suitable(url) for ie in _EXTRACTORS)
    except Exception:
        return True  # 判断不了就放行，让 yt-dlp 实际去尝试


def is_supported_url(url: str) -> bool:
    """任何 http(s) 链接都放行：
    - 已知站点由 yt-dlp 的专用解析器处理
    - 其它网页交给 Generic 通用解析器，自动发现页面里嵌入的 mp4/m3u8
      （找不到视频时会在解析阶段报错提示，而不是在这里误杀）
    """
    url = (url or "").strip()
    return bool(_HTTP_PATTERN.match(url))


def resolve_url(url: str) -> str:
    """把短链（b23.tv / v.douyin.com 等）解析成真实地址；解析不动就原样返回交给 yt-dlp。"""
    url = (url or "").strip()
    if not _SHORTLINK_PATTERN.search(url):
        return url
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            return resp.geturl()
    except Exception:
        return url


def _is_valid_ffmpeg(path: str) -> bool:
    if not path or not os.path.isfile(path):
        return False
    try:
        result = subprocess.run(
            [path, "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=3,
        )
        return result.returncode == 0
    except Exception:
        return False


def detect_proxy():
    """按优先级找可用代理：BILI_AUDIO_PROXY > HTTPS_PROXY > Windows 系统代理（启用时）。"""
    p = (
        os.environ.get("BILI_AUDIO_PROXY")
        or os.environ.get("HTTPS_PROXY")
        or os.environ.get("https_proxy")
    )
    if p:
        return p.strip()
    if os.name == "nt":
        try:
            import winreg

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
            )
            try:
                enabled, _ = winreg.QueryValueEx(key, "ProxyEnable")
                server, _ = winreg.QueryValueEx(key, "ProxyServer")
            finally:
                winreg.CloseKey(key)
            if enabled and server:
                server = str(server).strip().split(";")[0]
                if "=" not in server and "://" not in server:
                    server = "http://" + server
                return server
        except Exception:
            pass
    return None


def resolve_ffmpeg_path():
    """按优先级找 ffmpeg：环境变量 > PATH > 常见安装位置。"""
    env_path = os.environ.get("FFMPEG_PATH") or os.environ.get("BILI_AUDIO_FFMPEG")
    candidates = []
    if env_path:
        env_path = env_path.strip().strip('"').strip("'")
        if os.path.isdir(env_path):
            candidates.append(os.path.join(env_path, "ffmpeg.exe" if os.name == "nt" else "ffmpeg"))
        candidates.append(env_path)
    which_path = shutil.which("ffmpeg")
    if which_path:
        candidates.append(which_path)
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
        candidates.append(os.path.join(base, "ffmpeg.exe"))
        candidates.append(os.path.join(base, "bin", "ffmpeg.exe"))
    candidates.extend(
        [
            r"C:\ffmpeg\bin\ffmpeg.exe",
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
            r"C:\ProgramData\chocolatey\bin\ffmpeg.exe",
        ]
    )
    seen = set()
    for path in candidates:
        if not path:
            continue
        norm = os.path.normpath(path)
        if norm in seen:
            continue
        seen.add(norm)
        if _is_valid_ffmpeg(norm):
            return norm
    return None


def fetch_info(url: str, proxy=None):
    """
    只解析不下载：返回预览元数据和可用清晰度列表。
    返回 dict: title/uploader/thumbnail/duration/webpage_url/count/heights/has_audio
    heights 为降序的可用视频高度列表，如 [1080, 720, 480, 360]
    """
    if not is_supported_url(url):
        raise ValueError("不支持或无效的链接")
    url = resolve_url(url)
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }
    if proxy is None:
        proxy = detect_proxy()
    if proxy:
        opts["proxy"] = proxy

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    if not info:
        raise yt_dlp.utils.DownloadError("无法获取视频信息")

    entries = [e for e in (info.get("entries") or []) if e]
    count = len(entries) if entries else 1
    first = entries[0] if entries else info

    formats = first.get("formats") or info.get("formats") or []
    heights = sorted(
        {
            f.get("height")
            for f in formats
            if f.get("height") and (f.get("vcodec") or "none") != "none"
        },
        reverse=True,
    )

    # 每一集的独立信息，供前端勾选/合集下载
    page_url = info.get("webpage_url") or url
    items = []
    for i, e in enumerate(entries if entries else [info], 1):
        if not e:
            continue
        e_page = e.get("webpage_url")
        # 合集里每集的页面地址都不同（B站 ?p=N / YouTube watch）→ 用页面地址；
        # 通用网页解析出的多集共用同一个页面地址 → 用直链（mp4 等）
        if e_page and e_page != page_url:
            src = e_page
        elif not entries:
            src = page_url
        else:
            src = e.get("url") or e_page or page_url
        items.append({
            "index": i,
            "title": e.get("title") or f"第 {i} 集",
            "thumbnail": e.get("thumbnail") or info.get("thumbnail") or "",
            "duration": e.get("duration"),
            "url": src,
        })

    return {
        "title": first.get("title") or info.get("title") or "",
        "uploader": first.get("uploader") or info.get("uploader") or "",
        "thumbnail": first.get("thumbnail") or info.get("thumbnail") or "",
        "duration": first.get("duration") or info.get("duration"),
        "webpage_url": page_url,
        "count": len(items),
        "heights": heights,
        "has_audio": True,
        "items": items,
    }


def extract_audio(
    url: str,
    output_dir: str = ".",
    audio_format: str = "mp3",
    audio_quality: int = 0,
    progress_hook=None,
    media_type: str = "audio",
    proxy=None,
    max_height=None,
):
    """
    从视频页面提取音频（或下载视频），返回输出文件绝对路径列表。

    :param url: 视频页面 URL（BV / av / b23.tv / 其它 yt-dlp 支持的站点）
    :param output_dir: 输出目录
    :param audio_format: mp3 | m4a | aac（media_type="video" 时忽略）
    :param audio_quality: 0=最好 9=最小
    :param progress_hook: 可选，回调(dict)，字段: status/percent/speed/eta
    :param media_type: "audio"=仅音频转码  "video"=下载视频并合并为 mp4
    :return: 输出文件绝对路径列表（分 P / 播放列表会产出多个）
    """
    if not is_supported_url(url):
        raise ValueError("不支持或无效的链接（支持 B 站及 yt-dlp 覆盖的其它站点）")

    url = resolve_url(url)
    os.makedirs(output_dir, exist_ok=True)
    out_tmpl = os.path.join(output_dir, "%(title).80s [%(id)s].%(ext)s")

    def _hook(d):
        if not progress_hook:
            return
        try:
            if d.get("status") == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                downloaded = d.get("downloaded_bytes") or 0
                progress_hook({
                    "status": "downloading",
                    "percent": round(downloaded * 100.0 / total, 1) if total else None,
                    "speed": d.get("_speed_str", "").strip(),
                    "eta": d.get("_eta_str", "").strip(),
                })
            elif d.get("status") == "finished":
                progress_hook({"status": "converting", "percent": 100.0})
        except Exception:
            pass  # 进度回调不许影响下载

    def _pp_hook(d):
        if not progress_hook:
            return
        try:
            if d.get("status") == "started":
                progress_hook({"status": "converting"})
            elif d.get("status") == "finished":
                progress_hook({"status": "converting"})
        except Exception:
            pass

    opts = {
        "outtmpl": out_tmpl,
        # 不设 restrict_filename：默认保留中文标题，yt-dlp 自己会剔除 Windows 非法字符
        "progress_hooks": [_hook],
        "postprocessor_hooks": [_pp_hook],
        "quiet": True,
        "no_warnings": True,
    }
    if media_type == "video":
        if max_height:
            # 限定清晰度：优先不超过该高度的最高画质，兜底用任意最佳
            opts["format"] = (
                f"bv*[height<={max_height}]+ba/"
                f"b[height<={max_height}]/bv*+ba/b"
            )
        else:
            opts["format"] = "bv*+ba/b"
        opts["merge_output_format"] = "mp4"
    else:
        opts["format"] = "bestaudio/best"
        opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": audio_format,
                "preferredquality": str(audio_quality),
            }
        ]
    ffmpeg_path = resolve_ffmpeg_path()
    if ffmpeg_path:
        opts["ffmpeg_location"] = ffmpeg_path
    if proxy is None:
        proxy = detect_proxy()
    if proxy:
        opts["proxy"] = proxy

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if not info:
            raise yt_dlp.utils.DownloadError("无法获取视频信息")

        paths = []

        def _collect(entry):
            for rd in (entry.get("requested_downloads") or []):
                fp = rd.get("filepath")
                if fp and os.path.isfile(fp) and fp not in paths:
                    paths.append(fp)

        entries = info.get("entries") or []
        if entries:
            for entry in entries:
                if entry:
                    _collect(entry)
        else:
            _collect(info)

        if not paths:
            # 兜底：按视频 id 扫输出目录
            video_id = info.get("id", "")
            suffix = ".mp4" if media_type == "video" else f".{audio_format}"
            for f in sorted(os.listdir(output_dir)):
                if video_id and video_id in f and f.lower().endswith(suffix):
                    paths.append(os.path.join(output_dir, f))
        if not paths:
            raise yt_dlp.utils.DownloadError("未找到输出文件")
        return [os.path.abspath(p) for p in paths]


def main():
    parser = argparse.ArgumentParser(description="从视频网站提取音频/下载视频（B 站及 yt-dlp 支持的站点）")
    parser.add_argument("url", help="视频链接（BV / av / b23.tv / 其它站点）")
    parser.add_argument("-o", "--output-dir", default=".", help="输出目录（默认当前目录）")
    parser.add_argument("-f", "--format", default="mp3", choices=["mp3", "m4a", "aac"], help="音频格式")
    parser.add_argument("-q", "--quality", type=int, default=0, help="质量 0=最好 9=最小")
    parser.add_argument("--video", action="store_true", help="下载视频（mp4）而不是仅提取音频")
    args = parser.parse_args()

    def _print_progress(d):
        status = d.get("status")
        if status == "downloading":
            pct = d.get("percent")
            line = f"\r下载中 {pct if pct is not None else '?'}%  {d.get('speed', '')}  {d.get('eta', '')}"
            print(line.ljust(60), end="", flush=True)
        elif status == "converting":
            print("\r转码中...".ljust(60), end="", flush=True)

    try:
        paths = extract_audio(
            args.url,
            output_dir=args.output_dir,
            audio_format=args.format,
            audio_quality=args.quality,
            progress_hook=_print_progress,
            media_type="video" if args.video else "audio",
        )
        print()
        for p in paths:
            print(f"已保存: {p}")
        if len(paths) > 1:
            print(f"（分 P 视频，共 {len(paths)} 个文件）")
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n提取失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
