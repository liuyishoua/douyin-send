# 独立运行

推荐使用根目录 `python3 start.py`，默认启动演示模式。首次启动自动准备 `.venv`，
依赖变化后自动重装；仅准备环境可用 `python3 start.py --setup-only`。

## 服务入口

- 演示：`.venv/bin/python -m web --demo`。
- 真实：`.venv/bin/python -m web`。
- 默认地址：`http://127.0.0.1:8765`，可用 `--port` 修改。
- `--data-dir /absolute/path` 指定独立数据目录。
- `--host` 默认 `127.0.0.1`；容器内使用 `0.0.0.0`，宿主端口映射到回环地址。
- 就绪探测：`GET /.well-known/bifrost/ready`，返回 `{"ready": true}`。

页面静态资源随仓库提供，无 npm 构建。SQLite 首次启动自动建库。
演示和真实数据目录不可混用。真实模式需要 Node.js；Web 默认不读全局 `.env` 来绑定账号。

## 从 Bifrost 提取的范围

复制了 `applications/douyin` 中当前受 Git 管理的源文件，不复制运行中的数据库、凭证、日志或缓存。
原 Bifrost 服务继续使用原目录，此独立项目不改它的进程或启动配置。
旧 AGENTS.md 中部分历史设计和测试文档未出现在源仓库，不能作为此版本的现存文件引用。
当前实际提供的测试是 `web/test_origin.py` 和 `web/test_process_lock.py`。

## 回归命令

```bash
.venv/bin/python -m unittest web.test_origin web.test_process_lock
node --check web/static/app.js
```

Python 回归使用临时数据和演示适配器。启动验证应在独立演示数据目录执行。
本地演示、HTTP 探测或模拟测试均不等于真实账号联调。

## 此次提取验证

2026-10-04，在全新项目虚拟环境中安装控制台依赖，pip check 通过；
8 项现存 unittest 回归通过，前端 app.js 与 Bash 启动器语法检查通过。
一键启动器在临时演示数据目录启动成功，首页、静态资源、账号/用户/任务/总览 API 均返回 200，
数据库与凭证加密密钥自动生成。未执行真实账号登录或发送，也未构建 Docker 镜像。
GitHub Actions 配置已提供，但远程仓库尚未创建，因此未运行远程 CI。


## 2026-10-14 项目改名

原目录整体移至 `/home/ubuntu/leo-project/douyin-send`，包含原 Git 历史、未提交修改、数据、凭证及虚拟环境。正式 `douyin-web.service` 工作目录和启动路径已更新，网站仍为 https://d.58nft.net:9445/，模式仍为原演示模式。原 14 项回归通过，HTTPS 首页通过检查。相邻的新 douyin 使用独立服务、端口、数据及 Channel 来源。Git 远程仓库仍保留原地址，未执行远程仓库改名。
