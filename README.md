# lls-workbuddy-checkin · Buddy 签到 skill

WorkBuddy「Buddy 加油站」每日积分自动签到 skill（v3.1.1，作者 GTH）。

> 一键安装：`npx skills add lls-teach/lls-workbuddy-checkin`

经 WorkBuddy 客户端自带的宿主通道（WBIPC）直连接口完成签到——无需打开界面、无需点击按钮、无需读取或解密本机登录令牌，兼容桌面端 v5.3.8+ 的系统级加密登录态。鉴权头由客户端注入，脚本进程内不接触任何 accessToken。

## 快速开始

```bash
python scripts/checkin.py                # 查询 + 必要时领取（推荐，幂等可重复跑）
python scripts/checkin.py --check-only   # 仅查询，不领取
python scripts/checkin.py --diagnose     # 环境自检（模块 / 宿主通道 / 接口连通性）

python scripts/checkin_on_start.py       # 开机/重启后兜底（等待客户端就绪再签到）
python scripts/register_autostart.py --install   # 注册登录自启（Windows 专属）
```

仅用 Python 标准库，零第三方依赖，适用 Windows / macOS / Linux。

## 工作原理

1. `workbuddy_ipc.connect()` 连接客户端宿主，取 `wb.request` 管道的 `http.fetch`；
2. 查询签到状态（是否已签、连续天数、累计积分、活动是否开启）；
3. 今日未签则提交领取（幂等：已签同样视为成功）；
4. **领取后再查一次状态复核**，确认真的签上，防止「假成功」；
5. 输出 JSON 结果并写入 `scripts/logs/checkin.log`。

## 文件结构

```
├── SKILL.md                     # skill 主文件（安装后被加载）
├── scripts/checkin.py           # 主逻辑：状态查询 + 领取 + 复核
├── scripts/checkin_on_start.py  # 开机/重启后兜底签到
├── scripts/register_autostart.py # 登录自启项管理（Windows）
├── icon.png / _icon.png         # skill 图标
└── mcp.json / _skillhub_meta.json # skill 元数据
```

## 前提与安全

- 前提：本机已安装并登录 WorkBuddy 桌面客户端（v5.3.8+），开机联网。
- 安全：不读取、不解密、不落盘任何登录令牌；网络访问仅限经宿主通道转发的 WorkBuddy 官方接口；除运行日志外不写任何文件，不上传数据到第三方。

> 旧版本（WorkBuddy签到助手 v3.2.1，三通道授权 + 派猫猫旅行 + 多渠道推送）已归档在 tag `archive/v3.2.1`，可通过 `git checkout archive/v3.2.1` 查看。
