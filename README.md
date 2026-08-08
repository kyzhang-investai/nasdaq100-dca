# 纳斯达克100动态定投信号工具（云端版）

基于 **CME 纳指100期货（NQ）实时行情**，每天定时计算纳指定投信号并通过 **Server酱** 推送到微信。
本仓库为 **GitHub Actions 云端版本**——由 GitHub 云端服务器 24 小时运行，与你的电脑开关机无关。

## 工作原理

```
每天 14:45 (北京时间) → GitHub Actions 定时触发
    → 抓取纳指期货行情(新浪) + ETF行情(腾讯)
    → 按"逆势加倍"分档计算当日建议申购金额
    → 推送 Server酱 → 微信收到信号
```

## 快速开始

1. **Fork / Clone 本仓库**
2. 在仓库 **Settings → Secrets and variables → Actions** 添加 Secret：
   - `SENDKEY` = 你的 Server酱 SendKey（[sct.ftqq.com](https://sct.ftqq.com) 登录后复制）
3. 到 **Actions** 页面手动运行一次 **Nasdaq100 DCA Signal**，验证微信能收到推送
4. 之后每天 14:45 自动运行，无需任何人工干预

## 配置修改

编辑 `cloud/cloud_dca.py` 顶部常量：

| 常量 | 默认 | 说明 |
|---|---|---|
| `BASE_AMOUNT` | 100 | 基准金额（正常档申购金额，元） |
| `DAILY_CAP` | 300 | 单日申购上限 |
| `TIERS` | 五档 | 逆势加倍分档（跌3%→×2.0、跌1%→×1.5、±1%→×1.0、涨1%→×0.75、涨3%→×0.5） |

改完 Commit 即生效。

## 定时时间调整

编辑 `.github/workflows/dca-signal.yml` 中 `cron` 字段（UTC 时间，北京 = UTC+8）：

- 当前：`45 6 * * *` = 每天北京时间 14:45

## 免责声明

本工具输出仅为参考信号，不构成投资建议。市场有风险，投资需谨慎。
