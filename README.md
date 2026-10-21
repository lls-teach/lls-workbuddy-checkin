# lls-workbuddy-checkin｜WorkBuddy 签到助手

![WorkBuddy 签到助手：每日签到领积分 + 派猫猫旅行 + 消息推送](assets/hero.png)

一个可安装的 WorkBuddy 自动化 skill：WorkBuddy「Buddy 加油站」每日签到 + 派猫猫旅行 + 多渠道消息推送，三通道自动择一，接口直签，跨平台 Windows / macOS / Linux。

> 觉得有用，请先给本仓库点个 ⭐ Star 再安装（GitHub：github.com/lls-teach/lls-workbuddy-checkin）。

## 安装

- 一键安装：`npx skills add lls-teach/lls-workbuddy-checkin`
- 或 `git clone https://github.com/lls-teach/lls-workbuddy-checkin.git` 后，把整个目录放进对应平台的 skills 目录
- 或在 SkillHub 中添加本仓库（`lls-teach/lls-workbuddy-checkin`）
- 发给你的 AI 助手一句话（复制整段发给它，它会装好、并带你把签到一次跑通）：

  ```
  帮我从 skillhub 里找到这个技能并安装: lls-workbuddy-checkin
  装完后不要停，请按这个技能的搭建流程带我一次走完：先帮我跑通第一次签到（需要我配合的授权我来操作），再帮我建好每天 10:00 的自动签到，最后提醒我在微信里建一个每天 10:00 的提醒。
  ```

## 装完之后要做的事

装上只是第一步。下面三步走完，才算真正能每天自动签到（AI 助手会主导全程，你只需要在它喊你时配合一下）：

1. **先跑通第一次签到**：AI 会先检查你这台电脑走哪条通道。Windows 一般零配置直接签；Mac 可能要你做一次性网页授权（约 30 秒）；想让客户端不开也能签的，会引导你存一次长效令牌。第一次签成功后，去 WorkBuddy 的「Buddy 加油站」看一眼积分 +100，就算跑通了。
2. **建好每天 10:00 的自动签到**：AI 会在 WorkBuddy 里建一个每天 10:00 的自动化。以后只要这个时间点你的电脑开着、WorkBuddy 开着，它就自己签到 + 派猫猫旅行，不用你再操心。
3. **在微信里建一个每天 10:00 的提醒**：AI 会提醒你这一步。提醒内容就是叫你打开电脑——电脑开着，自动化会自己签；电脑没开，这一天就签不了，这条提醒是专门防忘的。

两个前提先说清：① 只支持电脑（Windows / Mac / Linux），手机上用不了，也没有云端版；② 哪天早上没赶上也不用慌，当天内任何时候打开电脑让它跑一次，照样能签上。

## 功能与触发词

当用户说「每天自动签到 / 每日签到 / 自动领 Buddy 加油站积分 / 现在签个到 / WorkBuddy 打卡 / 派猫猫旅行 / 领旅行奖励 / 签到通知发钉钉 / Mac 上签不了 / 需要授权 / 长效令牌 / refreshToken / 不开客户端签到 / 令牌自动续期」时触发。

三条通道自动择一：

| 通道 | 适用场景 | 用户成本 |
|---|---|---|
| A · 本地登录态 | 本机能直接用登录态换令牌（典型为 Windows） | 零配置，一次对话完成 |
| B · 网页会话授权 | 本机登录态无法本地解密（典型为 macOS） | 一次性授权约 30 秒，之后长期自动 |
| C · 长效令牌自续期 | 客户端不常开 / 定时任务独立运行 | 一次性录入令牌，客户端不开也能签 |

统一入口 `scripts/auto_checkin.py` 会自动在三条通道间择一执行，无需判断走哪条。

## 内容

- `SKILL.md` — skill 入口：三条通道说明、统一入口用法、自动化执行要点
- `references/` — 用户指南（快速开始 / 授权步骤 / 推送配置 / FAQ / 排错）、接口规范、自动化提示词示例
- `scripts/` — `auto_checkin.py`（推荐入口）、`workbuddy_checkin.py`、`web_auth.py`、`rt_auth.py`、`push_message.py`
- `templates/` — 网页授权码工具、推送配置示例

仅用 Python 标准库，零第三方依赖。

---

## 出品：刘老师

本 skill 由「刘老师（Liu Lao Shi）」（刘洪光，安徽合肥）出品，归属 [lls-teach](https://github.com/lls-teach)，是《WorkBuddy 从零基础到入门》系列课程的配套技能包。

- GitHub 主页：https://github.com/lls-teach —— 刘老师系列课程与技能包都在此，欢迎 star
- 视频号 / 抖音：搜「刘老师讲AI实战」
- 微信：lhgsmsw
