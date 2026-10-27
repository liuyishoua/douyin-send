# douyin-send

[![License: PolyForm Noncommercial 1.0.0](https://img.shields.io/badge/License-PolyForm%20Noncommercial%201.0.0-orange)](LICENSE)

独立运行的抖音用户与消息管理控制台，从 `bifrost/applications/douyin` 提取。
包含账号管理、用户搜索与入库、标签、话术、任务调度、会话记录、发送记录及统计总览。
Python 后端、原生 HTML/JS 前端、SQLite 数据库，无需 Bifrost 或前端编译。

## 界面预览

以下均为本项目实际运行截图，使用模拟账号和演示数据。

### 总览大盘

任务概况、执行时间轴和账号统计集中展示。

![总览大盘：演示任务和账号统计](docs/images/overview.png)

### 用户管理

查看搜索入库的用户，按指标和标签筛选，选择联系人创建任务。

![用户管理：演示用户列表和标签筛选](docs/images/users.png)

### 任务管理

任务创建后保持未开始，可查看配置并手动开始、暂停或恢复。

![任务管理：演示任务列表](docs/images/tasks.png)

### 账号管理

查看账号状态，管理账号发送节奏、工作时间和共享池。

![账号管理：模拟账号与执行设置](docs/images/accounts.png)

## 一键启动

先安装 **Python 3.10+**，克隆仓库后运行：

```bash
git clone https://github.com/liuyishoua/douyin-send.git douyin-send
cd douyin-send
```

```bash
python3 start.py
```

Windows 可双击 `start.bat`；macOS 可双击 `start.command`；Linux 可运行 `./start.sh`。
首次启动自动创建 `.venv`、安装依赖，成功后尝试打开 **http://127.0.0.1:8765**。
首次安装需要联网，后续依赖不变时直接启动。按 Ctrl+C 停止。

默认是**演示模式**，账号、搜索及发送均为模拟，不需要 Cookie 或扫码。
在账号管理添加一个账号，点击扫码并完成页面中的模拟授权，即可体验搜索、入库和任务流程。

端口被占用时：

```bash
python3 start.py --port 8875
```

服务器或无需自动打开浏览器时：

```bash
python3 start.py --no-browser
```

## 真实账号模式

额外安装 **Node.js 18+**（用于扫码辅助代码），然后运行：

```bash
python3 start.py --real
```

在账号管理中添加并扫码绑定自己的账号。任务创建后处于未开始状态，手动开始后才执行。
真实平台能力受登录状态和接口返回影响；演示启动成功不代表真实扫码和发送已经联调。
Web 控制台不要求预先填写 `.env`；`.env.example` 供原有接口脚本参考。

## 数据与备份

- 演示数据：`datas/web-demo/`。
- 真实数据：`datas/web/`。
- 首次运行自动建库，同一数据目录只能启动一个服务。
- 备份时先停止服务，再复制整个数据目录，包括数据库、凭证加密密钥和媒体。
- 数据、Cookie、密钥、`.env` 和虚拟环境不提交 Git。

这个独立副本不包含原 Bifrost 服务中的账号和业务数据。
运行细节见 [docs/run.md](docs/run.md)，功能需求见 [docs/requirements.md](docs/requirements.md)。

## 手动安装与验证

```bash
python3 -m venv .venv
# Linux / macOS；Windows 使用 .venv\Scripts\python.exe
.venv/bin/python -m pip install -r requirements-web.txt
.venv/bin/python -m web --demo
.venv/bin/python -m unittest web.test_origin web.test_process_lock
node --check web/static/app.js
```

`requirements-web.txt` 是控制台依赖；旧 `requirements.txt` 为媒体/直播等脚本依赖，控制台不需要安装它。
不要用 `main.py` 或 `quick_publish.py` 作为控制台启动入口，它们包含真实平台操作示例。

## Docker（可选）

```bash
docker build -t douyin-send .
docker run --rm -p 127.0.0.1:8765:8765 -v douyin-send-data:/app/datas douyin-send
```

默认演示模式。真实模式运行：

```bash
docker run --rm -p 127.0.0.1:8765:8765 -v douyin-send-data:/app/datas douyin-send python -m web --host 0.0.0.0
```

## 目录

- `web/`：Web 服务、业务逻辑、前端和回归测试。
- `dy_apis/`、`builder/`、`utils/`、`static/`：原有接口、鉴权和协议资源。
- `docs/`：需求与独立运行说明。
- `start.py`、`start.sh`、`start.command`、`start.bat`：一键启动入口。
- `app.yaml`：保留的 Bifrost 接入配置，独立启动不使用。

原有接口项目来源与说明保存在 [docs/upstream-readme.md](docs/upstream-readme.md)。

## 使用许可

**本项目仅供学习、研究、测试及其他非商业用途，不得用于商业目的。**
对本仓库中版权所有者拥有权利的代码，沿用 Bifrost 的
[PolyForm Noncommercial License 1.0.0](LICENSE)；商业使用须事先取得版权所有者的单独授权。
本项目属于**源码可见、限制商用**，不应标为 MIT 或 OSI 意义上的开源许可证。

第三方代码、素材和依赖仍受其各自许可条件约束；原抖音接口项目来源及许可核对范围见
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
Bifrost 先前以 MIT 发布的历史版本不受后续许可变更追溯限制，本仓库不重新解释那些历史版本的许可。
