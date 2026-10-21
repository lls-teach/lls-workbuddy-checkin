---
name: buddy-checkin
display_name: Buddy 签到
display_name_en: Buddy Check-in
description: "WorkBuddy「Buddy 加油站」每日积分签到，经客户端宿主通道（WBIPC）直连接口，无需点击 GUI、无需解密本地令牌。兼容桌面端 v5.3.8+ 的加密登录态。支持每日定时、开机/重启后自动补签、状态查询、领取后二次复核与运行日志。当用户说「签到」「领积分」「Buddy 加油站」「每日签到」「自动签到」时使用。"
description_zh: "WorkBuddy「Buddy 加油站」每日积分自动签到。经客户端宿主通道（WBIPC）直连接口，无需打开界面或点击按钮，也无需解密本地登录令牌；适配桌面端 v5.3.8+ 的加密登录态。支持仅查询、自动领取、领取后复核、开机自启补签与运行日志。"
description_en: "Automated daily check-in for WorkBuddy Buddy Gas Station credits, via the client's host IPC channel (WBIPC) with direct API calls — no GUI clicking, no local token decryption. Compatible with the encrypted login state of desktop v5.3.8+. Supports scheduled runs, auto check-in right after restart, status-only query, post-claim verification, and run logs."
category: productivity
author: GTH
version: 3.1.1
last_updated: 2026-09-29 12:48
changelog: "v3.1.1 补充「图标与署名约定」：图标由 Pillow 矢量绘制生成，右下角固定 GTH 署名，并按内切圆安全区自校验（市场头像为圆形裁切，避免署名被切掉）；v3.1.0 首版发布：基于客户端宿主通道（WBIPC）实现每日积分签到，兼容桌面端 v5.3.8+ 加密登录态；支持定时签到、开机自启补签、状态查询与领取后复核"
examples_zh:
  - 帮我领取今天 Buddy 加油站的积分
  - 设置每天自动签到领积分
  - 看看我连续签到多少天了
examples_en:
  - claim today's Buddy Gas Station credits for me
  - set up a daily auto check-in for credits
  - check my current check-in streak
agent_created: true
---

# Buddy 签到

经 WorkBuddy 客户端自带的宿主通道完成每日积分签到，全程无需打开界面、无需点击按钮，也**无需读取或解密本机登录令牌**。

> **为什么需要这一版**：桌面端 v5.3.8+ 已把本地登录态从明文 JSON 改为系统级加密信封
> （`auth.accessToken = {suite,keyId,nonce,authTag,ciphertext}`）。因此所有
> 「读明文 token 再直连接口」的旧脚本都会在读取阶段崩掉（典型报错：`slice(None, 6, None)`）。
> 本版改走客户端官方宿主通道，鉴权头由客户端注入，从根上绕开令牌问题。

## 快速开始

```bash
python scripts/checkin.py                # 查询 + 必要时领取（推荐）
python scripts/checkin.py --check-only   # 仅查询，不领取
python scripts/checkin.py --diagnose     # 环境自检（模块 / 宿主通道 / 接口连通性）

python scripts/checkin_on_start.py       # 开机兜底（等待客户端就绪后签到）
python scripts/register_autostart.py --install   # 注册开机自启（见文末）
```

Windows 上若 `python` 命令不可用，可用 WorkBuddy 自带的托管 Python
（位于 `~/.workbuddy/binaries/python/`，版本号以实际安装为准）。

## 文件结构

```
buddy-checkin/
├── SKILL.md
└── scripts/
    ├── checkin.py               # 主逻辑：状态查询 + 领取 + 复核
    ├── checkin_on_start.py      # 开机/重启后兜底（等待客户端就绪再签到）
    ├── register_autostart.py    # 管理登录自启项（注册/查看/注销）
    └── logs/                    # 运行日志（自动创建）
```

## 输出说明

JSON 结果，关键字段：

| 字段 | 含义 |
| --- | --- |
| `status` | `ok` 成功 / `error` 失败 |
| `action` | `clicked` 本次新签 / `skip_already_signed` 今日已签 / `skip_check_only` 仅查询 / `inactive` 活动未开启 / `verify_failed` 领取后复核未通过 |
| `points` | 本次领取积分数 |
| `balance` | 当前积分余额（`total_credits`） |
| `streak_days` | 连续签到天数 |
| `msg` | 人类可读结果 |

退出码：`0` 成功或今日已签；`1` 失败（定时任务可据此判断是否告警）。

## 汇报口径

- `clicked`：签到成功，说明 +N 积分、连续第几天、当前积分余额。
- `skip_already_signed`：今日已签到，无需重复操作，附余额。
- `skip_check_only`：仅查询完成，汇报今日是否已签与余额。
- `inactive`：签到活动当前未开启，不是脚本故障。
- `verify_failed`：领取接口返回成功但复核发现未签上 —— 需人工确认，不得按成功汇报。
- `error`：如实报告 `msg` 中的原因，绝不谎报成功。

## 工作原理

1. `workbuddy_ipc.connect()` 连接客户端宿主，取 `wb.request` 管道的 `http.fetch`。
2. `POST /v2/billing/meter/checkin-activity-status` 查询签到状态（是否已签、连续天数、累计积分、活动是否开启）。
3. 今日未签则 `POST /v2/billing/meter/daily-checkin` 领取（幂等：`code=10001` 表示今天已签，同样视为成功）。
4. **领取后再查一次状态复核**，确认真的签上 —— 防止「假成功」。
5. 输出 JSON 并追加写入 `scripts/logs/checkin.log`。

关键点：**脚本只提交 method 与 path，鉴权头由客户端注入**，进程内不接触任何 accessToken。

## 定时自动签到

由 WorkBuddy 自动化任务调度，建议每天固定时间执行（脚本幂等，重复运行无副作用）：

```bash
python scripts/checkin.py
```

注意：电脑需开机、联网、WorkBuddy 客户端已登录且未退出。

## 开机 / 重启后自动执行（登录自启兜底）

除每日定时任务外，可注册一个「登录后立即执行」的兜底项，重启当天也能第一时间补签：

```bash
python scripts/register_autostart.py --install     # 注册（默认）
python scripts/register_autostart.py --status      # 查看当前状态
python scripts/register_autostart.py --uninstall   # 注销
```

机制：写入用户级注册表 `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`
（值名 `WorkBuddyDailyCheckin`），指向 `pythonw.exe scripts/checkin_on_start.py`，全程无窗口。

`checkin_on_start.py` 的行为：

- **轮询等待客户端就绪**（默认最长 20 分钟，`WB_START_WAIT_SECONDS` 可调）——
  刚重启时客户端尚未启动完毕，宿主通道还没就绪，脚本会等到通道可连再签到。
- **单实例锁** —— 避免与定时任务或手动执行并发重复触发；陈旧锁自动清理。
- 超时后静默放弃，交给每日定时任务，不打扰用户。
- 日志写入 `scripts/logs/start-checkin.log`。

> 若环境允许，也可改用 Windows 计划任务（`schtasks`）；部分环境将
> `schtasks.exe` / `reg.exe` 列入程序黑名单，此时注册表 Run 键是等效替代方案。

前提：WorkBuddy 客户端需随开机自启（否则重启后通道一直不可用，会等到超时）。
可在「设置 → 常规」中开启自启，或确认 Run 键中存在 `WorkBuddy.WorkBuddy` 项。

## 安全约定

- **不读取、不解密、不落盘任何登录令牌** —— 凭据完全由客户端持有。
- 不修改本机登录态文件，不写入除运行日志外的任何文件，不上传数据到第三方。
- 网络访问仅限 WorkBuddy 官方接口（经宿主通道转发）。

## 常见问题

| 现象 | 排查 |
| --- | --- |
| `无法加载宿主通道模块（workbuddy_ipc）` | 必须在 WorkBuddy 客户端环境内运行（客户端自带该模块）；跑 `--diagnose` 看 `module_dir` |
| `宿主通道调用异常` / 连接失败 | 确认 WorkBuddy 客户端已登录且未退出；必要时重启客户端刷新通道 |
| `inactive` | `active=false`，签到活动未开启，等下一期活动开始 |
| 提示登录态相关错误 | 打开客户端刷新登录即可 |
| 余额显示 null | 接口未返回余额字段，属正常；不影响签到结果 |
| 开机后没签到 | 确认 WorkBuddy 客户端已随开机自启；查 `scripts/logs/start-checkin.log` |

## 图标与署名约定

本技能图标由 `_assets/make_icon.py` 用 Pillow 矢量绘制生成（512×512 PNG），非 AI 出图，便于按需重生成：

- **右下角固定署名 `GTH`**（开发者署名，与 `author` 字段一致）。
- 署名须完整落在**内切圆安全区**内 —— 技能市场的头像是圆形裁切，靠角落的署名会被切掉。
  脚本按 `CIRCLE_SAFE` 比例自动求解沿 45° 的最大偏移，并打印 `inside=True/False` 自校验。
- 改图后重跑 `make_icon.py`，它会同时导出 `_assets/_circle_preview.png` 用于肉眼复核圆形裁切效果。

## 适用平台与免责

- 适用平台：Windows / macOS / Linux，需 Python 3.6+（仅用标准库，无第三方依赖）；
  开机自启管理（`register_autostart.py`）为 Windows 专属。
- 适用前提：本机已安装并登录 WorkBuddy 桌面客户端（v5.3.8+ 亦可）。
- 本技能调用的是 WorkBuddy 客户端自有的签到接口，不涉及任何逆向或越权操作；
  签到规则、积分额度与活动周期由官方决定，本技能不保证任何积分收益。