# -*- coding: utf-8 -*-
"""
桌面应用入口：pywebview 内嵌 Flask，所有逻辑在本机执行，不对外开放端口。
运行: python desktop.py
"""
import os
import sys

import webview

if getattr(sys, "frozen", False):
    # PyInstaller 打包后：资源在 sys._MEIPASS，下载目录放在 exe 旁边
    _base = sys._MEIPASS
    _app_dir = os.path.dirname(sys.executable)
else:
    _base = os.path.dirname(os.path.abspath(__file__))
    _app_dir = _base

os.environ.setdefault("BILI_AUDIO_APP_ROOT", _base)

from app import app  # noqa: E402

if __name__ == "__main__":
    webview.create_window("B 站视频 → 音频", app, width=520, height=560, resizable=True)
    webview.start()
