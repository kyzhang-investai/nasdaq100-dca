# 云端部署指南（GitHub Actions）

把定投信号工具部署到 GitHub Actions 后，**由 GitHub 云端服务器每天定时运行并推送，与你的电脑是否开机完全无关**。

## 前提

- 一个 GitHub 账号（github.com 免费注册）

## 部署步骤（约 10 分钟，只需做一次）

### 第 1 步：创建仓库

1. 打开 github.com 并登录
2. 点右上角 `+` → **New repository**
3. Repository name 填 `nasdaq100-dca`（可自定义）
4. **Public**（公开，免费额度无限；私有仓库免费额度也够每天1次，但建议公开）
5. 点 **Create repository**

### 第 2 步：上传文件

在网页上直接上传（无需装 Git）：

1. 进入刚创建的仓库页面
2. 点 **Add file** → **Upload files**
3. 把以下两个文件/目录拖进去：
   - `cloud/cloud_dca.py`（云端运行脚本）
   - `.github/workflows/dca-signal.yml`（定时配置）
4. 点 **Commit changes** 提交

> 只需要传这两个，不需要传本地其他文件（本地 config.json 里的 SendKey 也**不要**传上去）。

### 第 3 步：配置 SendKey 密钥

代码仓库公开时，SendKey 绝不能明文写在代码里。GitHub 用 Secrets 加密存储：

1. 仓库页面 → **Settings** → 左侧 **Secrets and variables** → **Actions**
2. 点 **New repository secret**
3. Name 填：`SENDKEY`
4. Secret 填：**你自己的 Server酱 SendKey**（登录 sct.ftqq.com 复制，形如 `SCTxxxxxxxxxxxx`）
5. 点 **Add secret**

### 第 4 步：手动触发一次，验证链路

1. 仓库页面 → **Actions** 标签
2. 左侧选中 **Nasdaq100 DCA Signal**
3. 右侧点 **Run workflow** → 绿色按钮
4. 等待几十秒，看到绿色 ✅ 表示成功
5. 此时你的微信会收到一条信号推送 → 云端链路打通 ✅

### 第 5 步：确认自动定时生效

- 定时任务在 `dca-signal.yml` 中已配置：**每天北京时间 14:45** 自动运行
- Actions 页面会显示"下一次运行"的时间（页面显示为 UTC，北京时间 14:45 = UTC 06:45）
- 以后每天 14:45 左右你都会收到微信推送，**电脑可以随时关机**

## 常见问题

| 问题 | 解决 |
|---|---|
| Actions 运行失败，日志报 SSL 错误 | 云端 Ubuntu 自带新证书，一般不会出现；若出现请在 workflow 里加一步 `pip install certifi` |
| 定时到了但没推送 | 进 Actions 看运行日志：`[错误]` 开头说明数据源异常（如周末/节假日接口无数据），工作日正常 |
| 想改推送时间 | 编辑 `dca-signal.yml` 的 `cron: "45 6 * * *"`，前两位是 UTC 时:分（北京 = UTC+8，即北京 14:45 = UTC 06:45） |
| 想改金额/分档 | 编辑 `cloud_dca.py` 顶部的 `BASE_AMOUNT` / `TIERS`，改完 Commit 即可 |

## 云端版与本地版差异

| 项目 | 本地版 | 云端版 |
|---|---|---|
| 运行地点 | 你的电脑 | GitHub 云端服务器 |
| 电脑关机 | ❌ 停 | ✅ 照常运行 |
| 定时方式 | Windows 任务计划程序 | GitHub Actions cron |
| 配置位置 | config.json | cloud_dca.py 顶部常量 + Secrets |
| 推送 | Server酱 | Server酱（相同） |
