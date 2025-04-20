#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# vim: set tabstop=2 shiftwidth=2 textwidth=80 expandtab :
#
#
"""
测试： 时间日期工具

@author: cyhfvg
@date: 2025/04/20
"""

import re

from fkin_anfu.utils.datetime_utils import get_date_str, get_datetime_str


def test_get_datetime_str_format():
    """
    测试 get_datetime_str() 返回的时间格式是否符合 YYYYMMDD_HHMM_SS 格式。

    场景：
        - 调用函数
        - 检查正则匹配 ^\\d{8}_\\d{4}_\\d{2}$
    """
    value = get_datetime_str()
    assert re.match(r'^\d{8}_\d{4}_\d{2}$', value), f"Invalid datetime format: {value}"


def test_get_date_str_format():
    """
    测试 get_date_str() 返回的日期格式是否符合 YYYYMMDD 格式。

    场景：
        - 调用函数
        - 检查正则匹配 ^\\d{8}$
    """
    value = get_date_str()
    assert re.match(r'^\d{8}$', value), f"Invalid date format: {value}"
