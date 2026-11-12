"""从选定原图导出各平台图标；安装 requirements-build.txt 后运行。"""
from pathlib import Path
import sys
from PIL import Image


def main():
    assets = Path(__file__).resolve().parent / 'assets'
    with Image.open(assets / 'icon-source.png') as source:
        image = source.convert('RGBA')
        if image.width != image.height:
            raise ValueError('图标原图需要为正方形')
        image.resize((512, 512), Image.Resampling.LANCZOS).save(assets / 'icon.png')
        image.resize((256, 256), Image.Resampling.LANCZOS).save(
            assets / 'icon.ico', sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
        )
        # ICNS 由 Pillow 调用本机 macOS 的 iconutil 导出。
        if sys.platform == 'darwin':
            image.resize((1024, 1024), Image.Resampling.LANCZOS).save(assets / 'icon.icns')
    print('图标已导出到', assets)


if __name__ == '__main__':
    main()
