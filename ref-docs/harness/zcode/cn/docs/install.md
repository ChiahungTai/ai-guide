安装 | ZCode Docs
开始使用
ZCode for GLM-5.3
安装
连接模型
用户反馈与支持
核心功能
ZCode Agent
目标模式
浏览器自动化
任务与文件管理
Wiki
Memory
自动化
闲时任务
编辑历史对话
远程开发
Remote Control
Bot Channel
子智能体
Plugin
Skill
MCP
Command
Hooks
使用统计
深度集成
安全操作确认
智能体开发环境工具
帮助
快捷键表
常见问题解答 (Q&A)
开始使用复制全文
安装
下载并安装 ZCode 桌面应用，开始体验自研 ZCode Agent 驱动的端到端开发工作流。
1下载安装包
2完成安装
3首次启动
全程约 2 分钟
下载
立即下载 ZCode
适用于 macOS (Apple Silicon)
v3.14.3·最新版本
其他平台
macOSIntelWindowsx64WindowsARM64Linuxx64
支持 macOS（Apple Silicon / Intel）、Windows（x64 / ARM64）、Linux（x64 / ARM64，AppImage、DEB、RPM）。
安装步骤
当前系统
macOSApple Silicon / Intel
1打开下载的 ZCode.dmg 安装镜像。
2将 ZCode.app 拖动到 Applications 文件夹。
3在启动台中找到 ZCode 并启动。
当前系统
WindowsWindows x64
1下载 ZCode 安装程序。
2双击运行，按照安装向导完成安装。
3从开始菜单或桌面快捷方式启动 ZCode。
当前系统
LinuxLinux x64 / ARM64
1在下载区选择 Linux，下载 .AppImage、.deb 或 .rpm 安装文件。
2使用 AppImage 时，为文件添加可执行权限：chmod +x ZCode-*.AppImage；使用 .deb 或 .rpm 时，通过发行版的软件包管理器安装。
3双击文件或在终端中运行它启动 ZCode。
首次启动
首次启动会进入「首次启动设置」页面，完成后在左下角点击 连接使用 进入登录页面：
1
点击 开始使用 ZCode 直接进入。如需迁移历史数据，可选择 数据迁移向导：目前仅支持导入 Claude Code 和 旧版 ZCode 中 ZCode Agent 的对话记录，不支持其他工具；也可以先跳过，稍后在设置中继续迁移。
2
进入后选择一个项目目录作为工作区。
3
在对话框输入一句简单指令，比如让 Agent 列出当前目录的文件，确认响应正常。
如果还没有配置模型，点击左下角 连接使用 进入登录页面，引导你 连接 Z.ai、连接 BigModel 或 使用 API Key 完成接入，详见下一节 连接模型。
网络代理
如果你的网络需要走代理才能访问模型服务，在 设置 → 常规 里可以配置。这里有三个字段，填完点保存，需要重启应用才生效。
HTTP 代理：填入代理地址，例如 http://127.0.0.1:7890。
留空不等于跟随系统。 这个字段为空时 ZCode 直连，不会读取 HTTP_PROXY 等系统环境变量。这一点和很多命令行工具的默认行为相反，如果你发现终端里能联网而 ZCode 不行，多半就是这个原因。
配置后，模型请求、MCP 服务、Agent 执行的命令工具以及应用界面的网络请求都会走这个代理。
代理例外：不想走代理的地址，用英文逗号分隔，例如：
localhost,127.0.0.1,::1,.example.com,*.corp.com
主机名、.example.com 这样的域名后缀、*.corp.com 通配写法都支持，需要时还能带上端口。
自定义证书：填 PEM 格式根证书的本地文件路径。企业内网如果用了会解密 HTTPS 的安全网关，它签发的证书默认不被信任，把对应的根证书填在这里即可。注意这不是跳过证书校验——ZCode 只放行证书链里确实包含这张根证书的连接，其余照常校验。
Windows 专属设置
选择命令行环境。 在 设置 → 常规 → 终端 里可以指定 Agent 执行命令时用哪个 shell，可选 自动选择、CMD 和 Git Bash（检测到已安装时才出现）。默认是自动，优先用 Git Bash，找不到就回退到 cmd.exe。改动只对新建会话生效。
关闭窗口时最小化到托盘。 从 v3.4.0 起这是默认行为：点窗口的关闭按钮不会退出应用，而是收进系统托盘继续运行，定时任务和闲时任务也因此能在后台照常推进。托盘图标右键有新建任务、打开工作区、检查更新、退出等菜单项，左键点击可以把窗口叫回来。
想让关闭按钮直接退出，在 设置 → 常规 → 通知 里关掉「关闭窗口时隐藏到托盘」即可。这个开关只有 Windows 有。
从旧版本升级上来的用户请留意：这次默认值调整会把该开关 重置为开启一次，即使你之前手动关过。再关一次之后就会一直保持你的选择。
故障排查
macOS 提示「ZCode 已损坏，无法打开」
在终端执行以下命令解除隔离属性后重新打开：
xattr -dr com.apple.quarantine /Applications/ZCode.app
Windows 安装时被防火墙 / 杀软拦截
暂时关闭实时防护或将安装目录加入白名单后重试。
Linux 安装文件无法运行
确认已添加可执行权限（chmod +x）；部分发行版需要额外安装 fuse 依赖。更多 Linux / WSL 下的安装、登录与输入法问题，请参阅 Linux / WSL 排查指南。
了解更多
连接模型
为 Agent 接入 GLM 模型与 Coding Plan，开启对话与编程能力。
用户反馈与支持
遇到问题时，了解如何提供有效反馈。
常见问题解答 (Q&A)
查看安装、配置与使用中的常见疑问。
On this page
下载
安装步骤
首次启动
网络代理
Windows 专属设置
故障排查
了解更多
