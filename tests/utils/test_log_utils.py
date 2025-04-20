#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# vim: set tabstop=2 shiftwidth=2 textwidth=80 expandtab :
#
#
"""
测试：日志封装(colorama + logging + Lock)

@author: cyhfvg
@date: 2025/04/20
"""

from fkin_anfu.utils.log_utils import debug_print


def test_debug_print_all_levels():
    """
    验证 debug_print 在不同日志等级下能够正确调用并输出，不抛异常。
    包括已知等级：debug, info, success, warning, error，以及未知等级 fallback。
    """
    levels = ["debug", "info", "success", "warning", "error", "unknown"]
    for lvl in levels:
        debug_print(lvl, f"Test message for level: {lvl}")
