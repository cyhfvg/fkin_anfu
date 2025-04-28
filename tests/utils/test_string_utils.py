#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# vim: set ts=2 sw=2 et:

"""
单元测试: fkin_anfu.utils.string_utils

@author: cyhfvg
@date: 2025/04/23
"""

from fkin_anfu.utils.string_utils import (
    is_blank,
    mask_string,
    normalize_spaces,
    regex_match,
    remove_all_whitespace,
    remove_all_whitespace_from_list,
    replace_wide_chars,
    replace_wide_chars_in_list,
    split_and_strip,
)


def test_is_blank():
    """测试 is_blank() 判断空白字符串"""
    assert is_blank(None) is True
    assert is_blank("") is True
    assert is_blank("   \t\n") is True
    assert is_blank("abc") is False


def test_remove_all_whitespace():
    """测试 remove_all_whitespace() 删除空白字符"""
    assert remove_all_whitespace("a b\tc\n") == "abc"
    assert remove_all_whitespace(" a\tb c ") == "abc"


def test_split_and_strip():
    """测试 split_and_strip() 分隔+清洗"""
    assert split_and_strip("a,b,c") == ["a", "b", "c"]
    assert split_and_strip(" a , b ,  c ") == ["a", "b", "c"]
    assert split_and_strip(" , , ") == []


def test_mask_string():
    """测试 mask_string() 字符串脱敏"""
    assert mask_string("abcdefg", keep=1) == "a*****g"
    assert mask_string("abc", keep=1) == "a*c"
    assert mask_string("ab", keep=1) == "**"
    assert mask_string("a", keep=1) == "*"


def test_normalize_spaces():
    """测试 normalize_spaces() 空格归一化"""
    assert normalize_spaces(" a   b c ") == "a b c"
    assert normalize_spaces("\ta\t\tb\n") == "a b"


def test_regex_match():
    """测试 regex_match() 正则完整匹配"""
    assert regex_match("abc123", r"[a-z]+[0-9]+") is True
    assert regex_match("abc123xyz", r"[a-z]+[0-9]+") is False


def test_replace_wide_chars():
    """测试 replace_wide_chars() 中文全角标点替换"""
    assert replace_wide_chars("你好，世界。") == "你好,世界."
    assert replace_wide_chars("【测试】《标题》。") == "[测试]<标题>."
    assert replace_wide_chars("【测试】《标题》。", exclude=["【", "】"]) == "【测试】<标题>."


# 测试 replace_wide_chars_in_list 方法
def test_replace_wide_chars_in_list():
    """
    测试基本的宽字符替换
    """
    input_data = ["你好，世界。", "【示例】《标题》。"]
    expected_output = ['你好,世界.', '[示例]<标题>.']
    assert replace_wide_chars_in_list(input_data) == expected_output

    # 测试排除指定字符不替换
    input_data = ["【示例】《标题》。"]
    expected_output = ['【示例】<标题>.']
    assert replace_wide_chars_in_list(input_data, exclude=["【", "】"]) == expected_output

    # 测试空列表
    input_data = []
    expected_output = []
    assert replace_wide_chars_in_list(input_data) == expected_output

    # 测试单个字符串
    input_data = ["你好，世界！"]
    expected_output = ['你好,世界!']
    assert replace_wide_chars_in_list(input_data) == expected_output


# 测试 remove_all_whitespace_from_list 方法
def test_remove_all_whitespace_from_list():
    """
    测试基本的空白字符移除
    """
    input_data = ["a b\tc\n", " d e f "]
    expected_output = ['abc', 'def']
    assert remove_all_whitespace_from_list(input_data) == expected_output

    # 测试空列表
    input_data = []
    expected_output = []
    assert remove_all_whitespace_from_list(input_data) == expected_output

    # 测试单个字符串
    input_data = ["  a b c  "]
    expected_output = ['abc']
    assert remove_all_whitespace_from_list(input_data) == expected_output

    # 测试带有多种空白字符的情况
    input_data = ["a b\tc\n", "  d e f  "]
    expected_output = ['abc', 'def']
    assert remove_all_whitespace_from_list(input_data) == expected_output
