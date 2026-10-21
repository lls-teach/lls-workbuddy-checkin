#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WorkBuddy 开机/重启后自动签到（登录自启动兜底）

用途：登录后立刻尝试领取「Buddy 加油站」当日积分，与每日定时自动化任务
      互相兜底，避免断签。

为什么需要等待：刚开机/重启时 WorkBuddy 客户端尚未启动完毕，宿主通道
（WBIPC，端点在 %USERPROFILE%\\.workbuddy\\wbipc\\endpoint.json）还没就绪。
因此本脚本会轮询等待，直到通道可连再执行签到；超时则静默放弃，
交给每日定时任务。

特性：
  - 单实例锁：避免开机自启与手动/定时执行并发重复触发。
  - 只等待，不硬失败：超时后安静退出，不打扰用户。
  - 日志写入同目录 logs/start-checkin.log。

退出码：0 = 已尝试或正常放弃；1 = 异常。
"""

import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_SCRIPT = os.path.join(HERE, "checkin.py")
LOG_DIR = os.path.join(HERE, "logs")
LOG_FILE = os.path.join(LOG_DIR, "start-checkin.log")
LOCK_FILE = os.path.join(LOG_DIR, "start-checkin.lock")

PYTHON = sys.executable or "python"

# 等待客户端就绪的上限（秒）：重启后客户端启动 + 登录通常 1~3 分钟，留足余量
WAIT_TIMEOUT_S = int(os.environ.get("WB_START_WAIT_SECONDS", "1200"))
POLL_INTERVAL_S = 15
ENDPOINT = os.path.join(os.path.expanduser("~"), ".workbuddy", "wbipc", "endpoint.json")


def log(msg):
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write("%s | %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg))
    except Exception:
        pass


def acquire_lock():
    """单实例锁；陈旧锁（>30 分钟）自动清理。"""
    os.makedirs(LOG_DIR, exist_ok=True)
    for _ in range(2):
        try:
            fd = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            return fd
        except FileExistsError:
            try:
                if time.time() - os.path.getmtime(LOCK_FILE) > 1800:
                    os.remove(LOCK_FILE)
                    continue
            except Exception:
                pass
            return None
        except Exception:
            return None
    return None


def release_lock(fd):
    try:
        if fd is not None:
            os.close(fd)
        os.remove(LOCK_FILE)
    except Exception:
        pass


def _add_module_path():
    cands = []
    env = os.environ.get("CODEBUDDY_BUILTIN_SKILLS_DIR", "").strip()
    if env:
        cands.append(os.path.join(env, "library"))
    cands.append(os.path.join(
        r"C:\Program Files\WorkBuddy\resources\app.asar.unpacked",
        "resources", "plugins", "workbuddy-builtin", "skills", "library"))
    for d in cands:
        if os.path.isdir(os.path.join(d, "workbuddy_ipc")):
            if d not in sys.path:
                sys.path.insert(0, d)
            return d
    return None


def _ipc_ready():
    """探测宿主通道是否真正可连（能握手且 http.fetch 可用）。"""
    _add_module_path()
    try:
        from workbuddy_ipc import connect  # type: ignore
        with connect(client_id="wb-start-checkin", client_kind="skill") as wb:
            pipe = wb.get_pipe("wb.request")
            return "http.fetch" in getattr(pipe, "methods", [])
    except Exception:
        return False


def wait_for_client():
    deadline = time.time() + WAIT_TIMEOUT_S
    while time.time() < deadline:
        if os.path.isfile(ENDPOINT) and _ipc_ready():
            return True
        time.sleep(POLL_INTERVAL_S)
    return False


def main():
    fd = acquire_lock()
    if fd is None:
        log("已有实例在运行，跳过")
        return 0
    try:
        log("启动兜底开始，等待 WorkBuddy 客户端与宿主通道就绪…")
        if not os.path.isfile(SKILL_SCRIPT):
            log("未找到签到脚本: %s" % SKILL_SCRIPT)
            return 1
        if not wait_for_client():
            log("等待超时（%ds），客户端未就绪，交给每日定时任务" % WAIT_TIMEOUT_S)
            return 0
        log("客户端就绪，开始签到")
        try:
            proc = subprocess.run(
                [PYTHON, SKILL_SCRIPT], capture_output=True, text=True, timeout=120)
            out = (proc.stdout or "").strip()
        except Exception as e:
            log("调用签到脚本异常: %s" % e)
            return 1
        try:
            res = json.loads(out)
            log("签到结果: status=%s action=%s streak=%s balance=%s msg=%s" % (
                res.get("status"), res.get("action"),
                res.get("streak_days"), res.get("balance"), res.get("msg")))
        except Exception:
            log("签到脚本输出无法解析: %s" % out[:300])
        return 0
    finally:
        release_lock(fd)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        log("未捕获异常: %s" % e)
        sys.exit(1)