<p align="center">
  <img src="assets/icon.png" width="96" alt="BiliAudio 图标">
</p>

<h1 align="center">BiliAudio</h1>

<p align="center"><strong>把视频里的声音，保存到你的电脑。</strong></p>
<p align="center">音频提取 · 视频下载 · 分 P / 播放列表批量保存<br>支持 Windows 与 macOS · 中文界面 · 本地运行</p>

<p align="center">
  <a href="#开始使用">开始使用</a> ·
  <a href="#支持哪些功能">功能介绍</a> ·
  <a href="#常见问题">常见问题</a> ·
  <a href="https://github.com/Bougainvillea-Gilbert/BiliAudio/issues">反馈问题</a>
</p>

BiliAudio 是一个在电脑上运行的音视频下载小工具。粘贴视频链接，预览标题和分集，选择需要的内容，即可提取音频或保存视频。

音频支持 **MP3 / M4A / AAC**，视频支持 **MP4**；通过 yt-dlp 尝试解析 B 站及其他受支持网站，也支持部分网页内嵌视频。

> **下载前请看：** 当前仓库提供源码，尚未发布包含运行环境的 Windows / Mac 安装包。通过 **Code → Download ZIP** 下载后，需要先安装 Python 和 FFmpeg，再按下方对应系统的步骤启动。

## 开始使用

### 1. 下载并解压

点击页面上方绿色 **Code → Download ZIP**，或 [直接下载源码 ZIP](https://github.com/Bougainvillea-Gilbert/BiliAudio/archive/refs/heads/main.zip)。将整个文件夹解压到电脑上，保留里面的文件和目录。

Windows 和 Mac 使用同一份源码，但启动方式不同：

| 系统 | 第一次使用 | 之后如何启动 |
| --- | --- | --- |
| **Windows** | 安装 Python、FFmpeg，执行下方 Windows 初始化步骤 | 在项目文件夹打开 PowerShell，执行 `.\.venv\Scripts\python.exe run.py` |
| **macOS** | 安装 Python、FFmpeg，双击 `启动.command` | 双击 `启动.command`；已生成图标入口时也可打开 `BiliAudio.app` |

### 2. 按你的系统启动

#### Windows

先安装 **Python 3.10 或更高版本**（包含 Tkinter）和 **FFmpeg**，并确保它们可以在终端中运行。

打开解压后的项目文件夹，在地址栏输入 `powershell` 并回车。首次运行时，依次执行：

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
ffmpeg -version
.\.venv\Scripts\python.exe run.py
```

如果 `ffmpeg -version` 提示找不到命令，请先完成 FFmpeg 安装、将其加入 PATH，再重新打开 PowerShell。

以后启动只需执行最后一行。仓库中的 `build.bat` 用于打包 EXE，日常使用请按上面的方式启动。

#### macOS

先安装 **Python 3.10 或更高版本**和 **FFmpeg**。如果已经安装 Homebrew，可以在终端执行：

```bash
brew install python ffmpeg
```

双击项目文件夹里的 **`启动.command`**。首次启动会自动创建运行环境并安装依赖，需要联网。

如果提示脚本没有执行权限，可在项目目录的终端中执行：

```bash
bash 启动.command
```

想使用带图标的启动入口，可在项目目录运行：

```bash
python3 build_macos_launcher.py
```

生成的 `BiliAudio.app` 可以拖入 Dock，但应用本体要留在项目文件夹里。这个入口依赖源码和运行环境。

### 3. 粘贴链接，选择内容，保存

启动后，浏览器会自动打开 **http://127.0.0.1:23331**。如果没有自动打开，可以复制这个地址到浏览器。

1. 粘贴完整的视频链接，点击 **解析链接**。
2. 查看标题、封面和分集，勾选需要下载的内容。
3. 选择音频格式，或选择 MP4 视频及可用清晰度。
4. 点击下载，等待进度完成；多集内容也可以选择合集下载。
5. 在保存目录查看文件，多个文件还可以打包另存为 ZIP。

**使用时请保持启动终端运行。** 关闭终端或按 `Ctrl+C` 会停止服务；关闭浏览器页面不会退出程序。

## 支持哪些功能

| 功能 | 说明 |
| --- | --- |
| **提取音频** | 将视频音轨保存为 MP3、M4A 或 AAC |
| **保存视频** | 下载并合并为 MP4，可选择片源提供的清晰度 |
| **先预览再下载** | 解析后展示标题、封面、时长和分集列表 |
| **批量下载** | 分 P / 播放列表支持部分勾选、全选和合集下载，单集失败不阻塞后续 |
| **分享短链** | 支持尝试解析 b23.tv 等分享短链；BV / av 号请使用完整视频链接 |
| **下载管理** | 显示下载与转码进度，保留中文标题，支持选择目录和 ZIP 另存为 |
| **网络重试** | B 站默认直连，超时或连接中断会自动重试；其他站点按环境检测代理 |
| **本地界面** | 服务仅监听本机地址 `127.0.0.1`，浏览器作为操作界面 |

网站能否解析取决于片源、登录限制、网络条件和 yt-dlp 的支持情况，不能保证所有链接可用。

## 文件保存在哪里

默认保存到当前用户的 **下载 / Downloads** 文件夹，可在软件界面点击 **更改** 选择其他位置。

保存目录设置会在本机记住：

- **Windows：** `%APPDATA%\BiliAudio\config.json`
- **macOS：** `~/Library/Application Support/BiliAudio/config.json`

## 常见问题

**下载 ZIP 后，为什么没有可以直接打开的 EXE / APP？**

当前 ZIP 是源码包。需要按上面的步骤安装环境并启动；独立安装包尚未发布。

**Mac 的 `.app` 能在 Windows 上打开吗？**

不能。两端共用源码，但应用入口和运行环境分别属于各自系统。复制 Mac 的 `.venv` 或 `.app` 到 Windows 无法直接运行，需要在 Windows 上重新建立环境。

**提示网络超时怎么办？**

程序会自动重试。如果仍然失败，先确认该链接能在本机浏览器正常打开，再检查网络或代理。B 站默认直连；设置 `BILI_AUDIO_PROXY` 环境变量可以指定代理，其他站点会尝试使用检测到的代理。

**提示找不到 FFmpeg 怎么办？**

确认 FFmpeg 已安装并能运行 `ffmpeg -version`，然后重新启动软件。也可将环境变量 `FFMPEG_PATH` 设置为 FFmpeg 可执行文件的完整路径。

**需要登录、会员或受保护的视频能下载吗？**

目前没有提供 Cookie 登录配置入口。需要登录 / 会员的内容可能无法获取；不支持 DRM 加密内容。

**打不开保存目录，或提示没有写入权限？**

在界面中更换保存目录。如果 Windows 安全软件拦截写入，请检查拦截记录和文件夹保护设置。

## 开发与打包

<details>
<summary>查看命令行、桌面窗口、打包和验证方式</summary>

### 命令行

在已安装依赖的 Python 环境中运行：

```bash
python extract.py "https://www.bilibili.com/video/BVxxxxx" -o ./output -f mp3
python extract.py "https://b23.tv/abc123" -o ./output -f m4a
python extract.py "https://www.bilibili.com/video/BVxxxxx" -o ./output --video
```

### 可选桌面窗口

默认通过浏览器使用，也可以安装 pywebview 后运行桌面窗口：

```bash
python -m pip install -r requirements-desktop.txt
python desktop.py
```

桌面窗口的依赖需在对应操作系统安装。

### Windows 打包

在已完成初始化的 Windows 项目目录中执行：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\build.bat
```

输出位于 `dist\BiliAudio\BiliAudio.exe`。分发时需要保留整个 `dist\BiliAudio` 文件夹；当前打包脚本未捆绑 FFmpeg，使用者仍需安装 FFmpeg。

### 图标

`assets/` 包含原图、PNG、Windows ICO 和 Mac ICNS。需要重新生成图标时，安装构建依赖后运行 `python make_icon.py`；Mac 图标入口由 `build_macos_launcher.py` 生成。

### 自检

```bash
python -m unittest discover -s tests -v
```

macOS 已验证解析、MP4 下载和 MP3 转码。Windows 的完整流程仍需实机验证，包括下载、转码、目录选择和 ZIP 保存。

</details>

## 致谢与许可

架构参考 [c0sc0s/BiliMusicDownloader](https://github.com/c0sc0s/BiliMusicDownloader)，代码重新实现；音视频解析与下载基于 [yt-dlp](https://github.com/yt-dlp/yt-dlp)，转码依赖 [FFmpeg](https://ffmpeg.org/)。

项目采用 [MIT License](LICENSE)。仅供个人学习及有权保存的内容备份，请尊重内容版权和平台规则。本项目与 Bilibili 官方无关联。
