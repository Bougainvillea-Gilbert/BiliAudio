# -*- coding: utf-8 -*-
"""
启动器：启动本地 Flask 服务，并用系统默认浏览器打开界面。
窗口最小化即可；关闭本窗口 = 退出程序。
"""
import os
import json
import urllib.request
import sys
import threading
import time
import webbrowser

if getattr(sys, "frozen", False):
    _base = sys._MEIPASS            # PyInstaller 资源目录
    _app_dir = os.path.dirname(sys.executable)
else:
    _base = os.path.dirname(os.path.abspath(__file__))
    _app_dir = _base

os.environ.setdefault("BILI_AUDIO_APP_ROOT", _base)
# 下载目录不再固定到程序目录：由 app.py 决定（默认系统「下载」，用户可改并持久化）

from app import app  # noqa: E402

PORT = 23331  # 只绑定本机回环，不对外开放


def _open_browser():
    time.sleep(1.2)
    webbrowser.open(f"http://127.0.0.1:{PORT}/")


def _already_running():
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(f"http://127.0.0.1:{PORT}/api/check-env", timeout=1) as response:
            info = json.load(response)
        return isinstance(info, dict) and "ffmpeg_path" in info and "proxy_detected" in info
    except Exception:
        return False


if __name__ == "__main__":
    if _already_running():
        webbrowser.open(f"http://127.0.0.1:{PORT}/")
        print("BiliAudio 已在运行，已打开页面。")
        sys.exit(0)
    threading.Thread(target=_open_browser, daemon=True).start()
    print("=" * 46)
    print("  BiliAudio 已启动")
    print(f"  界面地址: http://127.0.0.1:{PORT}/")
    print("  浏览器会自动打开；没打开就手动复制上面地址")
    print("  本窗口最小化即可，关闭窗口 = 退出程序")
    print("=" * 46)
    app.run(host="127.0.0.1", port=PORT, debug=False)
