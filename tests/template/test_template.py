#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# vim: set tabstop=2 shiftwidth=2 textwidth=80 expandtab :
#
#
"""
测试：测试模板

@author: cyhfvg
@date: YYYY/MM/DD
"""


def test_feature_behavior():
    """
    [功能点说明]:
      测试某函数在正常输入下的返回值是否正确。

    场景：
      - 输入:x = 1, y = 2
      - 操作:调用 func(x, y)

    期望：
      - 返回值为 3
      - 无异常抛出
    """
    result = 1 + 2
    assert result == 3
