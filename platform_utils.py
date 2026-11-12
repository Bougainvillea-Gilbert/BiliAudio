"""操作系统相关功能；macOS 对话框使用系统 AppleScript，无需 Tk。"""
import os
import subprocess
import sys


def config_directory():
    if sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    elif os.name == "nt":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(base, "BiliAudio")


def _mac_dialog(expression, *args):
    # 用户路径通过 argv 传入，避免文件名中的引号被作为脚本执行。
    script = '''on run argv
try
return POSIX path of (''' + expression + ''')
on error messageText number errorNumber
if errorNumber is -128 then return ""
error messageText number errorNumber
end try
end run'''
    result = subprocess.run(
        ["osascript", "-e", script, "--", *args],
        capture_output=True, text=True,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "无法打开系统对话框")
    return result.stdout.rstrip("\n") or None


def pick_directory(initial):
    if sys.platform == "darwin":
        return _mac_dialog(
            'choose folder with prompt "选择下载保存位置" default location (POSIX file (item 1 of argv))',
            initial,
        )
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        return filedialog.askdirectory(initialdir=initial, title="选择下载保存位置") or None
    finally:
        root.destroy()


def save_zip_dialog(initial_file, initial_dir):
    if sys.platform == "darwin":
        return _mac_dialog(
            'choose file name with prompt "打包另存为 ZIP" default name (item 1 of argv) default location (POSIX file (item 2 of argv))',
            initial_file, initial_dir,
        )
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        return filedialog.asksaveasfilename(
            title="打包另存为 ZIP", defaultextension=".zip",
            initialfile=initial_file, initialdir=initial_dir,
            filetypes=[("ZIP 压缩包", "*.zip")],
        ) or None
    finally:
        root.destroy()


def open_in_file_manager(target, select=False):
    if sys.platform == "darwin":
        command = ["open", "-R", target] if select else ["open", target]
    elif os.name == "nt":
        command = ["explorer", "/select,", target] if select else ["explorer", target]
    else:
        command = ["xdg-open", os.path.dirname(target) if select else target]
    subprocess.Popen(command)
