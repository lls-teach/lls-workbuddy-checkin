# lls-workbuddy-checkin｜WorkBuddy 签到助手

![WorkBuddy 签到助手：每日签到领积分 + 派猫猫旅行 + 消息推送](assets/hero.png)

一个可安装的 WorkBuddy 自动化 skill：WorkBuddy「Buddy 加油站」每日签到 + 派猫猫旅行 + 多渠道消息推送，三通道自动择一，接口直签，跨平台 Windows / macOS / Linux。

> 觉得有用，请先给本仓库点个 ⭐ Star 再安装（GitHub：github.com/lls-teach/lls-workbuddy-checkin）。

## 安装

- 一键安装：`npx skills add lls-teach/lls-workbuddy-checkin`
- 或 `git clone https://github.com/lls-teach/lls-workbuddy-checkin.git` 后，把整个目录放进对应平台的 skills 目录
- 或在 SkillHub 中添加本仓库（`lls-teach/lls-workbuddy-checkin`）
- 发给你的 AI 助手一句话安装（复制这句发给它就行）：

  ```
  帮我从 skillhub 里找到这个技能并安装: lls-workbuddy-checkin
  ```

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
