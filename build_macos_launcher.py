"""构建当前源码项目的 Mac 双击入口（不是独立安装包）。"""
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys
import tempfile


SCRIPT = r'''
on run
    set bundlePath to POSIX path of (path to me)
    set projectPath to do shell script "/usr/bin/dirname " & quoted form of (text 1 thru -2 of bundlePath)
    set launcherPath to projectPath & "/启动.command"
    try
        do shell script "/bin/test -f " & quoted form of launcherPath
        do shell script "/usr/bin/open -a Terminal " & quoted form of launcherPath
    on error errorMessage number errorNumber
        display alert "无法启动 BiliAudio" message ("启动脚本：" & launcherPath & return & "错误 " & errorNumber & "：" & errorMessage) as critical
    end try
end run
'''


def main():
    if sys.platform != 'darwin':
        raise SystemExit('此入口需要在 macOS 上构建')
    root = Path(__file__).resolve().parent
    target = root / 'BiliAudio.app'
    # 先在临时目录成功构建，再替换本脚本生成的入口。
    with tempfile.TemporaryDirectory() as tmp:
        bundle = Path(tmp) / 'BiliAudio.app'
        subprocess.run(['osacompile', '-o', str(bundle), '-'], input=SCRIPT, text=True, check=True)
        icon = bundle / 'Contents/Resources/BiliAudio.icns'
        shutil.copy2(root / 'assets/icon.icns', icon)
        # osacompile 的资源目录默认含 applet 图标目录，IconName 优先于 IconFile。
        # 移除该目录并同步旧资源，避免 Finder / Dock 继续显示脚本图标。
        (bundle / 'Contents/Resources/Assets.car').unlink(missing_ok=True)
        shutil.copy2(icon, bundle / 'Contents/Resources/applet.icns')
        plist_path = bundle / 'Contents/Info.plist'
        with plist_path.open('rb') as f:
            info = plistlib.load(f)
        info.pop('CFBundleIconName', None)
        info.update(CFBundleIconFile='BiliAudio.icns', CFBundleIdentifier='local.biliaudio.launcher', CFBundleName='BiliAudio', CFBundleDisplayName='BiliAudio')
        with plist_path.open('wb') as f:
            plistlib.dump(info, f)
        subprocess.run(['codesign', '--force', '--sign', '-', str(bundle)], check=True)
        subprocess.run(['codesign', '--verify', '--deep', '--strict', str(bundle)], check=True)
        if target.exists():
            with (target / 'Contents/Info.plist').open('rb') as f:
                existing = plistlib.load(f)
            if existing.get('CFBundleIdentifier') != 'local.biliaudio.launcher':
                raise SystemExit('已有同名应用，不覆盖：' + str(target))
            shutil.rmtree(target)
        shutil.copytree(bundle, target)
    subprocess.run([
        '/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister',
        '-f', str(target),
    ], check=True)
    target.touch()
    print('已创建', target)


if __name__ == '__main__':
    main()
