#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WorkBuddy 每日签到助手（宿主通道版，无需解密本地令牌）

为什么是这一版：
  WorkBuddy 桌面端 v5.3.8+ 把本地登录态从「明文 JSON」改成了系统级加密信封
  （auth.accessToken = {suite,keyId,nonce,authTag,ciphertext}）。因此所有
  「读明文 token 再直连接口」的旧脚本都会崩在读取阶段。

  正确做法是走客户端自带的宿主通道（WBIPC）：skill 只提交 method + path，
  **鉴权头由 WorkBuddy 客户端注入**，脚本进程内完全不接触 accessToken。

流程：
  1. 通过 workbuddy_ipc.connect() 连接宿主，取 wb.request 管道的 http.fetch
  2. POST /v2/billing/meter/checkin-activity-status 查询状态
  3. 今日未签则 POST /v2/billing/meter/daily-checkin 领取（幂等）
  4. 领取后再查一次状态复核，确认真的签上（防「假成功」）
  5. 输出结构化 JSON，并追加写入运行日志

用法：
  python checkin.py                 # 查询 + 必要时领取（推荐）
  python checkin.py --check-only    # 仅查询，不领取
  python checkin.py --diagnose      # 环境自检（模块 / 宿主通道 / 接口连通性）
  python checkin.py --version

退出码：0 = 成功或今日已签；1 = 失败（便于定时任务判断是否告警）
"""

import base64
import json
import os
import sys
import time

if sys.version_info < (3, 6):
    sys.stderr.write("WorkBuddy 每日签到：需要 Python 3.6+\n")
    sys.exit(2)

VERSION = "3.3.0"
CALL_TIMEOUT = 30.0

STATUS_PATH = "/v2/billing/meter/checkin-activity-status"
CHECKIN_PATH = "/v2/billing/meter/daily-checkin"

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")

# workbuddy_ipc 所在的内置技能目录（宿主通道客户端模块随客户端分发）
_MODULE_FALLBACK_DIRS = (
    r"C:\Program Files\WorkBuddy\resources\app.asar.unpacked\resources\plugins\workbuddy-builtin\skills",
    "/Applications/WorkBuddy.app/Contents/Resources/app.asar.unpacked/resources/plugins/workbuddy-builtin/skills",
    os.path.expanduser("~/.workbuddy/plugins/workbuddy-builtin/skills"),
)


def _ensure_module_path():
    """把内置技能目录加入 sys.path，使 workbuddy_ipc 可导入。"""
    roots = []
    env = os.environ.get("CODEBUDDY_BUILTIN_SKILLS_DIR", "").strip()
    if env:
        roots.append(env)
    roots.extend(_MODULE_FALLBACK_DIRS)
    cands = []
    for r in roots:
        if not r:
            continue
        # 模块可能直接在某技能目录下，也可能在 builtin-skills/library/ 下
        cands.append(r)
        cands.append(os.path.join(r, "library"))
    for d in cands:
        if d and os.path.isdir(os.path.join(d, "workbuddy_ipc")):
            if d not in sys.path:
                sys.path.insert(0, d)
            return d
    return None


def _load_ipc():
    _ensure_module_path()
    from workbuddy_ipc import connect, WbipcError  # type: ignore
    return connect, WbipcError


def _fetch(pipe, method, path, body=None):
    """经宿主通道发起一次 http.fetch；鉴权由客户端注入。返回 (status, dict)。"""
    params = {"method": method.upper(), "path": path}
    if body is not None:
        params["headers"] = {"Content-Type": "application/json"}
        params["body_b64"] = base64.b64encode(
            json.dumps(body, ensure_ascii=False).encode("utf-8")).decode("ascii")
    resp = pipe.invoke("http.fetch", params, timeout=CALL_TIMEOUT)
    status = int(resp.get("status") or 0)
    raw = base64.b64decode(resp.get("body_b64") or "")
    try:
        parsed = json.loads(raw.decode("utf-8", "replace"))
    except Exception:
        parsed = {}
    return status, parsed


def _data(body):
    d = body.get("data") if isinstance(body, dict) else None
    return d if isinstance(d, dict) else {}


def _run(check_only=False):
    result = {"status": "unknown", "action": None, "points": None,
              "balance": None, "streak_days": None, "msg": "", "detail": {}}
    try:
        connect, WbipcError = _load_ipc()
    except Exception as e:
        result.update(status="error",
                      msg="无法加载宿主通道模块（workbuddy_ipc）: %s" % e)
        return result

    try:
        with connect(client_id="buddy-checkin", client_kind="skill") as wb:
            pipe = wb.get_pipe("wb.request")
            result["detail"]["pipe_methods"] = pipe.methods

            # 1. 查询状态
            code, body = _fetch(pipe, "POST", STATUS_PATH, {})
            d = _data(body)
            result["detail"]["status_http"] = code
            result["detail"]["activity"] = d.get("activity_name")
            result["detail"]["season"] = d.get("season")
            result["balance"] = d.get("total_credits")
            result["streak_days"] = d.get("streak_days")

            if code >= 300:
                result.update(status="error", msg="状态查询失败: HTTP %s %s"
                              % (code, body.get("msg", "")))
                return result
            if d.get("active") is False:
                result.update(status="error", action="inactive",
                              msg="签到活动当前未开启（active=false），无需领取")
                return result

            signed = d.get("today_checked_in") is True
            result["detail"]["today_checked_in"] = signed

            if check_only:
                result.update(status="ok", action="skip_check_only",
                              msg="状态查询成功（未领取），今日%s"
                                  % ("已签" if signed else "未签"))
                return result

            if signed:
                result.update(status="ok", action="skip_already_signed",
                              msg="今日已签到，无需重复领取")
                return result

            # 2. 领取
            ccode, cbody = _fetch(pipe, "POST", CHECKIN_PATH, {})
            result["detail"]["checkin_http"] = ccode
            bcode = str(cbody.get("code", "")) if isinstance(cbody, dict) else ""
            cmsg = cbody.get("msg", "") if isinstance(cbody, dict) else ""
            already = (bcode == "10001") or ("已签到" in str(cmsg))
            ok = already or (200 <= ccode < 300 and bcode in ("", "0", "200"))

            # 3. 复核
            verified = None
            try:
                vcode, vbody = _fetch(pipe, "POST", STATUS_PATH, {})
                vd = _data(vbody)
                verified = vd.get("today_checked_in") is True
                result["detail"]["verified"] = verified
                if vd.get("total_credits") is not None:
                    result["balance"] = vd.get("total_credits")
                if vd.get("streak_days") is not None:
                    result["streak_days"] = vd.get("streak_days")
            except Exception as e:
                result["detail"]["verify_error"] = str(e)

            if verified is False and not already:
                result.update(status="error", action="verify_failed",
                              msg="领取接口返回成功，但复核发现今日仍未签到（%s）" % cmsg)
                return result

            if ok or verified:
                credit = d.get("daily_credit") or d.get("today_credit")
                bal_txt = ("，当前积分余额 %s" % result["balance"]) if result["balance"] is not None else ""
                result.update(
                    status="ok",
                    action="skip_already_signed" if already else "clicked",
                    points=credit,
                    msg=("今日已签到（接口幂等保护）" if already else "签到成功")
                        + (("，+%s 积分" % credit) if credit else "")
                        + (("，连续第 %s 天" % result["streak_days"]) if result["streak_days"] else "")
                        + bal_txt,
                )
                return result

            result.update(status="error", action="failed",
                          msg="领取失败: HTTP %s %s" % (ccode, cmsg))
            return result
    except Exception as e:
        result.update(status="error", msg="宿主通道调用异常: %s" % e)
        return result


def _diagnose():
    rep = {"version": VERSION, "python": sys.version.split()[0]}
    d = _ensure_module_path()
    rep["module_dir"] = d
    rep["module_found"] = d is not None
    try:
        connect, WbipcError = _load_ipc()
        with connect(client_id="buddy-checkin", client_kind="skill") as wb:
            rep["pipes"] = wb.list_pipes()
            pipe = wb.get_pipe("wb.request")
            rep["methods"] = pipe.methods
            code, body = _fetch(pipe, "POST", STATUS_PATH, {})
            rep["status_http"] = code
            rep["today_checked_in"] = _data(body).get("today_checked_in")
            rep["total_credits"] = _data(body).get("total_credits")
    except Exception as e:
        rep["error"] = "%s: %s" % (type(e).__name__, e)
    return rep


def _write_log(res):
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        line = "%s | status=%s | action=%s | streak=%s | balance=%s | msg=%s\n" % (
            time.strftime("%Y-%m-%d %H:%M:%S"), res.get("status"), res.get("action"),
            res.get("streak_days"), res.get("balance"), res.get("msg"))
        with open(os.path.join(LOG_DIR, "checkin.log"), "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if "--version" in sys.argv:
        print("buddy-checkin %s" % VERSION)
        sys.exit(0)
    if "--diagnose" in sys.argv:
        print(json.dumps(_diagnose(), ensure_ascii=False, indent=2))
        sys.exit(0)
    res = _run(check_only="--check-only" in sys.argv)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    _write_log(res)
    sys.exit(0 if res.get("status") == "ok" else 1)


if __name__ == "__main__":
    main()
