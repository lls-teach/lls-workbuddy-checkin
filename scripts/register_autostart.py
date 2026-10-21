#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
注册/注销「WorkBuddy 开机后自动签到」的登录自启项

机制：写入当前用户的注册表 Run 键（纯 winreg，不调用外部 reg.exe）
  HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run
    值名：WorkBuddyDailyCheckin
    值  ：「<pythonw.exe>」 「<checkin_on_start.py>」

为什么不用计划任务：部分环境将 schtasks.exe / reg.exe 列入程序黑名单，
无法创建 Windows 计划任务或调用 reg 命令行；改用用户级 Run 键 —— 效果等同
「登录后立即执行」，且完全在用户范围内、随时可撤销。

用法：
  python register_autostart.py --install     # 注册（默认）
  python register_autostart.py --uninstall   # 注销
  python register_autostart.py --status      # 查看当前状态
"""

import os
import sys

RUN_SUBKEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "WorkBuddyDailyCheckin"

PYTHONW = os.path.join(
    os.path.dirname(os.path.abspath(sys.executable)), "pythonw.exe")
WRAPPER = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "checkin_on_start.py")


def _command():
    return '"%s" "%s"' % (PYTHONW, WRAPPER)


def status():
    try:
        import winreg
    except ImportError:
        print("非 Windows 环境，winreg 不可用")
        return 0
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_SUBKEY, 0,
                            winreg.KEY_READ) as k:
            val, _ = winreg.QueryValueEx(k, VALUE_NAME)
            print("已注册：")
            print("  " + val)
    except FileNotFoundError:
        print("未注册（Run 键中无 %s）" % VALUE_NAME)
    except Exception as e:
        print("查询失败：%s: %s" % (type(e).__name__, e))
    return 0


def install():
    if not os.path.isfile(WRAPPER):
        print("错误：未找到启动脚本 %s" % WRAPPER)
        return 1
    if not os.path.isfile(PYTHONW):
        print("错误：未找到 pythonw.exe %s" % PYTHONW)
        return 1
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_SUBKEY, 0,
                            winreg.KEY_SET_VALUE) as k:
            winreg.SetValueEx(k, VALUE_NAME, 0, winreg.REG_SZ, _command())
        print("注册成功，登录后会自动执行签到兜底：")
        print("  " + _command())
        return 0
    except Exception as e:
        print("注册失败：%s: %s" % (type(e).__name__, e))
        return 1


def uninstall():
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_SUBKEY, 0,
                            winreg.KEY_SET_VALUE) as k:
            winreg.DeleteValue(k, VALUE_NAME)
        print("已注销开机自启项 %s" % VALUE_NAME)
        return 0
    except FileNotFoundError:
        print("本就未注册，无需注销")
        return 0
    except Exception as e:
        print("注销失败：%s: %s" % (type(e).__name__, e))
        return 1


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--install"
    if mode == "--status":
        return status()
    if mode == "--uninstall":
        return uninstall()
    return install()


if __name__ == "__main__":
    sys.exit(main())