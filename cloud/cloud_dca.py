# -*- coding: utf-8 -*-
"""
纳指100动态定投信号 - 云端版（GitHub Actions 定时运行）
========================================================
与本地版逻辑完全一致，但作为单文件独立运行，适用于 GitHub Actions。

运行方式：
  SENDKEY=xxx python cloud_dca.py

环境变量：
  SENDKEY  Server酱 SendKey（在 GitHub 仓库 Settings -> Secrets 中配置，
           代码仓库公开时绝不能明文写在代码里）
"""
import json
import os
import re
import ssl
import urllib.parse
import urllib.request

# ---------- 配置（与本地 config.json 保持一致） ----------
BASE_AMOUNT = 100          # 基准金额（每周定投预算）
DAILY_CAP = 300            # 单日上限
DAILY_FLOOR = 0            # 单日下限
PREMIUM_LIMIT = 2.5        # 溢价率上限 %
PREMIUM_STOP = 5.0         # 溢价率暂停线 %
TIERS = [
    (-99.0, -3.0, 2.00, "期货跌超3% → 2倍买入(大跌手动加投)"),
    (-3.0, -1.0, 1.50, "跌1%~3% → 1.5倍买入"),
    (-1.0, 1.0, 1.00, "涨跌幅1%以内 → 正常定投"),
    (1.0, 3.0, 0.75, "涨1%~3% → 0.75倍买入"),
    (3.0, 99.0, 0.50, "期货涨超3% → 0.5倍买入"),
]

SINA_URL = "https://hq.sinajs.cn/list=hf_NQ"
TENCENT_URL = "https://qt.gtimg.cn/q=sz159501"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://finance.sina.com.cn",
}

try:
    import certifi
    _SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except Exception:
    _SSL_CONTEXT = ssl.create_default_context()


def _fetch(url, headers=None):
    req = urllib.request.Request(url, headers=headers or HEADERS)
    with urllib.request.urlopen(req, timeout=15, context=_SSL_CONTEXT) as resp:
        return resp.read().decode("gbk", errors="ignore")


def _num(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def fetch_futures():
    """新浪纳指期货：0当前价 4最高 5最低 6时间 7昨收 8今开"""
    text = _fetch(SINA_URL)
    m = re.search(r'"(.*)"', text)
    if not m:
        raise RuntimeError("新浪期货接口异常")
    f = m.group(1).split(",")
    price, prev_close = _num(f[0]), _num(f[7])
    if price is None or prev_close is None or prev_close == 0:
        raise RuntimeError("期货数据不完整")
    return {
        "price": price,
        "prev_close": prev_close,
        "pct": (price - prev_close) / prev_close * 100,
        "time": f[6] if len(f) > 6 else "",
    }


def fetch_etf():
    """腾讯ETF行情：1名称 3现价 32涨跌幅%；IOPV在索引85附近(容错82-88)"""
    text = _fetch(TENCENT_URL)
    m = re.search(r'="(.*)"', text)
    if not m:
        raise RuntimeError("腾讯ETF接口异常")
    f = m.group(1).split("~")
    name = f[1]
    price = _num(f[3])
    if price is None:
        raise RuntimeError("ETF行情不完整")
    iopv = None
    if len(f) > 85:
        for idx in range(82, min(89, len(f))):
            cand = _num(f[idx])
            if cand and 0 < cand and 0 < abs(cand / price - 1) < 0.15:
                iopv = cand
                break
    premium = (price / iopv - 1) * 100 if iopv else None
    return {"name": name, "price": price, "premium_pct": premium}


def calc_signal(fut_pct):
    """逆势加倍分档（区间左开右闭）"""
    for low, high, coef, _ in TIERS:
        if fut_pct > low and fut_pct <= high:
            return coef
    if fut_pct <= TIERS[0][0]:
        return TIERS[0][2]
    return TIERS[-1][2]


def build_message(fut, etf, coef):
    amount = round(BASE_AMOUNT * coef)
    if amount > DAILY_CAP:
        amount = DAILY_CAP
    if amount < DAILY_FLOOR:
        amount = 0

    warn = ""
    premium = etf["premium_pct"]
    if premium is not None:
        if premium > PREMIUM_STOP:
            amount = 0
            warn = f"\n⚠ 参考ETF溢价率 {premium:.2f}% 超过暂停线 {PREMIUM_STOP}%，建议暂停"
        elif premium > PREMIUM_LIMIT:
            amount = round(amount / 2)
            warn = f"\n⚠ 参考ETF溢价率 {premium:.2f}% 超过上限 {PREMIUM_LIMIT}%，金额减半"

    lines = [
        f"📊 纳指100动态定投信号（{etf['name']}）",
        "-" * 28,
        f"纳指期货: {fut['price']:.2f}  ({fut['pct']:+.2f}%)",
        f"ETF现价:  {etf['price']:.3f}",
        f"定投系数: ×{coef:.2f}",
        f"基准金额: {BASE_AMOUNT} 元",
        f"建议申购: {amount} 元",
        "操作: 买入" if amount > 0 else "操作: 暂停/不投",
    ]
    if premium is not None:
        lines.append(f"ETF溢价:  {premium:+.2f}%")
    if warn:
        lines.append(warn)
    lines.append("-" * 28)
    lines.append("场外申购：支付宝/天天基金搜『纳斯达克100』QDII联接基金，按金额申购")
    return "\n".join(lines), amount


def push_serverchan(sendkey, title, text):
    payload = urllib.parse.urlencode({
        "title": title, "desp": text.replace("\n", "\n\n"),
    }).encode("utf-8")
    req = urllib.request.Request(f"https://sctapi.ftqq.com/{sendkey}.send", data=payload)
    with urllib.request.urlopen(req, timeout=15, context=_SSL_CONTEXT) as resp:
        r = json.loads(resp.read().decode("utf-8"))
        if r.get("code") != 0:
            raise RuntimeError(f"Server酱推送失败: {r}")
    return True


def main():
    sendkey = os.environ.get("SENDKEY", "").strip()
    if not sendkey:
        raise SystemExit("缺少 SENDKEY 环境变量")

    fut = fetch_futures()
    etf = fetch_etf()
    coef = calc_signal(fut["pct"])
    msg, amount = build_message(fut, etf, coef)

    print(msg)
    push_serverchan(sendkey, f"纳指定投信号 {amount}元", msg)
    print("\n[推送成功] Server酱")


if __name__ == "__main__":
    main()
