# BiliAudio

当前用于个人跨设备使用与验证，暂未发布正式安装包。
Mac 已完成本地测试视频的解析、MP4 下载和 MP3 转码验证；Windows 仍待实机验证。
各平台真实网站的可用性取决于片源、登录限制、网络及 yt-dlp 的支持情况。

从视频网站提取音频（MP3 / M4A / AAC）或直接下载视频（MP4）的本地小工具。
架构参考 [c0sc0s/BiliMusicDownloader](https://github.com/c0sc0s/BiliMusicDownloader)（MIT），
代码为重新实现，并做了以下改进：

- **两步流程**：先「解析链接」→ 左侧逐集预览（封面/标题/时长），右侧选输出选项 → 再下载
- **多集选择**：分 P / 播放列表 / 一页多视频，支持勾选部分下载、全选、或一键「合集下载」；逐集下载，单集失败不阻塞
- **音频 / 视频分开选择**：音频 MP3/M4A/AAC；视频 MP4 可选清晰度（1080P/720P/480P/360P…以片源实际提供的为准）
- **普通网页内嵌视频**：博客/文章页里的 mp4 也能识别（通用解析器）
- **代理支持**：自动识别 Windows 系统代理，或使用 BILI_AUDIO_PROXY 环境变量（海外站需要）
- **多站点解析**：通过 yt-dlp 尝试解析 B 站及其他受支持网站；不保证每个站点或每条链接均可用
- 支持 **b23.tv / v.douyin.com 等短链**（APP 分享链接）（BV / av 请粘贴完整视频链接）
- **分 P 视频 / 播放列表**自动下载全部并分别保存
- 保留**中文标题**（原版 `restrict_filename` 会把中文名变成下划线）
- 下载/转码**实时进度条**
- Web 模式只绑 `127.0.0.1`，不对外开放端口

> 注意：需要登录/会员的内容需要 Cookie（暂未支持）；
> 爱优腾 VIP 的 DRM 加密内容无法也不应解析。
> 海外站点能否使用取决于你本机网络。

## macOS 使用（源码）

需要 Python 3.10 或更高版本和 FFmpeg。已安装 Homebrew 时可用 `brew install ffmpeg` 安装 FFmpeg。

本机已有 `BiliAudio.app`（猫耳少女图标）可双击启动；从仓库首次下载时双击 `启动.command`，浏览器会自动打开 http://127.0.0.1:23331 。
首次启动会创建 `.venv` 并安装浏览器模式所需依赖，需要联网。
关闭启动终端或按 Ctrl+C 即退出；下载过程中请保持终端运行。

macOS 使用 Finder 打开/定位下载文件，选择目录和 ZIP 另存为使用系统原生对话框。
默认保存到 `~/Downloads`，配置保存在 `~/Library/Application Support/BiliAudio/config.json`。
Windows 配置仍保存在 `%APPDATA%/BiliAudio/config.json`。

Windows 与 macOS 共用源码；`build.bat` 目前只用于 Windows 打包，尚未提供 Mac `.app` 安装包。

## Windows 首次使用与验证（源码）

先安装 Python 3.10 或更高版本（包含 Tkinter，用于原生目录对话框）和 FFmpeg。
在 GitHub 登录同一账号后，克隆私有仓库或下载 ZIP 并解压，进入项目文件夹。
Mac 的 `.venv` 和 `.app` 不会上传，需要在 Windows 重新建立运行环境。

在 PowerShell 中执行（不必激活虚拟环境）：

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
ffmpeg -version
.\.venv\Scripts\python.exe run.py
```

浏览器会打开 http://127.0.0.1:23331 。使用时保持终端开启，按 Ctrl+C 停止服务。
如果找不到 FFmpeg，请先安装并重新打开终端；也可设置 `FFMPEG_PATH` 为可执行文件的完整路径。

Windows 实机验证清单：

- 解析一个可公开访问的视频链接，确认标题、封面和清晰度。
- 分别下载 MP4、转出 MP3，确认文件能正常播放。
- 更改下载目录，并用“打开文件夹”定位结果。
- 下载多个条目，检查进度、完成数量和 ZIP 保存。
- 重新启动后检查保存目录是否记住。

源码自检：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Windows 打包（可选，验证后再使用）

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\build.bat
```

以下是自己构建出安装目录后的使用方法；仓库当前不包含预编译 EXE。


1. 确认已安装 FFmpeg：`winget install FFmpeg`（`ffmpeg -version` 能输出版本即可）
2. 运行 `dist\BiliAudio\BiliAudio.exe`
3. 浏览器会自动打开界面；粘贴链接 →「解析链接」→ 勾选集数 → 选输出选项 → 下载
4. **默认保存到系统「下载」文件夹**；点「更改」会弹 Windows 原生目录选择框，选择会被记住（`%APPDATA%/BiliAudio/config.json`）
5. 多文件任务完成后可点「打包另存为 ZIP…」，弹 Windows 原生保存对话框

> 首次运行如果火绒弹提示，选择允许/加入信任即可。
> 若火绒开启了「文件夹保护/勒索防护」，它可能拦截程序写入「下载」「文档」等目录：
> 把 `BiliAudio.exe` 和 `ffmpeg.exe` 加入信任，或在界面里把下载位置改到非保护目录。

## 使用（源码）

```bash
pip install -r requirements.txt

# 方式一：浏览器界面（推荐，任何机器都能跑）
python run.py          # 打开 http://127.0.0.1:23331

# 方式二：pywebview 桌面窗口（需要机器上 pythonnet 能工作）
pip install -r requirements-desktop.txt
python desktop.py

# 方式三：纯命令行
python extract.py "https://www.bilibili.com/video/BVxxxxx"
python extract.py "https://b23.tv/abc123" -o ./output -f m4a
```

## 免责声明

仅供个人学习与备份使用，请勿用于侵犯版权的行为。与 Bilibili 官方无任何关联。

## 图标与 Mac 启动入口

选定原图为 `assets/icon-source.png`。安装构建依赖后运行：

```bash
python make_icon.py               # 导出 PNG / Windows ICO；Mac 上也导出 ICNS
python build_macos_launcher.py     # 在 macOS 上创建 BiliAudio.app
```

`BiliAudio.app` 是本地源码的快捷启动入口，通过终端运行 `启动.command`，必须留在项目文件夹内。
可以把它拖入 Dock 方便启动。项目运行后，再次打开入口只会打开已有页面。
关闭运行服务的终端或按 Ctrl+C 即退出服务；关闭浏览器页面不会退出服务。
此入口依赖项目源码、Python、虚拟环境和 FFmpeg，不是可独立分发的 Mac 安装包。
