# lls-workbuddy-checkin｜WorkBuddy 签到助手

![WorkBuddy 签到助手：每日签到领积分](assets/hero.png)

一个可安装的 WorkBuddy 自动化 skill：WorkBuddy「Buddy 加油站」每日签到领积分。经客户端自带的宿主通道（WBIPC）直连接口——无需打开界面、无需点击按钮、无需读取或解密本机登录令牌，鉴权头由客户端注入，脚本进程内不接触任何 accessToken，兼容桌面端 v5.3.8+ 的系统级加密登录态。

> 觉得有用，请先给本仓库点个 ⭐ Star 再安装（GitHub：github.com/lls-teach/lls-workbuddy-checkin）。

## 安装

- 一键安装：`npx skills add lls-teach/lls-workbuddy-checkin`
- 或 `git clone https://github.com/lls-teach/lls-workbuddy-checkin.git` 后，把整个目录放进对应平台的 skills 目录
- 或在 SkillHub 中添加本仓库（`lls-teach/lls-workbuddy-checkin`）
- 发给你的 AI 助手一句话（复制整段发给它，它会装好、并带你把签到一次跑通）：

  ```
  帮我从 skillhub 里找到这个技能并安装: lls-workbuddy-checkin
  装完后不要停，请按这个技能的搭建流程带我一次走完：先帮我跑通第一次签到，再帮我建好每天 10:00 的自动签到，最后提醒我在微信里建一个每天 10:00 的提醒。
  ```

## 装完之后要做的事

装上只是第一步。下面几步走完，才算真正能每天自动签到（AI 助手会主导全程，你只需要在它喊你时配合一下）：

1. **先跑通第一次签到**：AI 会先自检宿主通道是否连通，再帮你签今天的到，签完还会复核一次确认真签上。成功后去 WorkBuddy 的「Buddy 加油站」看一眼积分到账，就算跑通了。
2. **建好每天 10:00 的自动签到**：AI 会在 WorkBuddy 里建一个每天 10:00 的自动化。以后只要这个时间点你的电脑开着、WorkBuddy 开着，它就自己签到，不用你再操心。
3. **（Windows 可选）开机自启兜底**：重启电脑后自动补签一次，防断签。AI 会先问你，要的话它帮你注册好。
4. **在微信里建一个每天 10:00 的提醒**：AI 会提醒你这一步。提醒内容就是叫你打开电脑——电脑开着，自动化会自己签；电脑没开，这一天就签不了，这条提醒是专门防忘的。

两个前提先说清：① 只支持电脑（Windows / Mac / Linux），手机上用不了，也没有云端版；② 哪天早上没赶上也不用慌，当天内任何时候打开电脑让它跑一次，照样能签上。

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

## 前提与安全

- 前提：本机已安装并登录 WorkBuddy 桌面客户端（v5.3.8+），开机联网。
- 安全：不读取、不解密、不落盘任何登录令牌；网络访问仅限经宿主通道转发的 WorkBuddy 官方接口；除运行日志外不写任何文件，不上传数据到第三方。

> 更早的版本（三通道授权 + 派猫猫旅行 + 多渠道推送）已归档在 tag `archive/v3.2.1`，可通过 `git checkout archive/v3.2.1` 查看。因桌面端 v5.3.8+ 已将本地登录态改为系统级加密，旧版的读令牌路线不再可用，故自 v3.3.0 起改走宿主通道。

---

## 出品：刘老师

本 skill 由「刘老师（Liu Lao Shi）」（刘洪光，安徽合肥）出品，归属 [lls-teach](https://github.com/lls-teach)，是《WorkBuddy 从零基础到入门》系列课程的配套技能包。

- GitHub 主页：https://github.com/lls-teach —— 刘老师系列课程与技能包都在此，欢迎 star
- 视频号 / 抖音：搜「刘老师讲AI实战」
- 微信：lhgsmsw
