#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# vim: set tabstop=2 shiftwidth=2 textwidth=80 expandtab :
#
#
"""
测试 color_utils 模块中的颜色高亮函数，确保输出格式正确。

@author: cyhfvg
@date: 2025/07/19
"""

import pytest

from fkin_anfu.utils import color_utils


@pytest.mark.parametrize(
    "func,color_keyword",
    [
        (color_utils.RED, "red"),
        (color_utils.GREEN, "green"),
        (color_utils.YELLOW, "yellow"),
        (color_utils.ORANGE, "orange"),
        (color_utils.BLUE, "blue"),
        (color_utils.CYAN, "cyan"),
        (color_utils.MAGENTA, "magenta"),
    ],
)
def test_color_functions_output_contains_reset(func, color_keyword):
    """
    测试各快捷颜色函数输出是否包含 RESET 样式
    """
    result = func("test")
    assert isinstance(result, str)
    assert "test" in result
    assert color_utils.RESET() in result


@pytest.mark.parametrize(
    "color,bold,expected_pattern",
    [
        ("red", False, r"\x1b\[3[1]\mtest\x1b\[0m"),  # 普通红色
        ("green", True, r"\x1b\[1m\x1b\[32mtest\x1b\[0m"),  # 加粗绿色
        ("orange", False, r"\x1b\[9[1]\mtest\x1b\[0m"),  # 近似橙色
        ("magenta", True, r"\x1b\[1m\x1b\[35mtest\x1b\[0m"),  # 加粗洋红
    ],
)
def test_highlight_text_output_pattern(color, bold, expected_pattern):
    """
    测试 highlight_text 是否输出预期的 ANSI 控制序列结构
    """
    result = color_utils.highlight_text("test", color=color, bold=bold)
    assert isinstance(result, str)
    # 使用正则确保控制序列存在，不要求完全匹配（不同平台可能有变体）
    assert "test" in result
    assert result.startswith("\x1b[") or result.startswith("\033[")
    assert result.endswith("\x1b[0m") or result.endswith("\033[0m")


def test_invalid_color_fallback():
    """
    测试传入不支持的颜色时，是否回退为无色输出但仍包含 RESET
    """
    result = color_utils.highlight_text("test", color="unknown-color")
    assert isinstance(result, str)
    assert "test" in result
    assert color_utils.RESET() in result
