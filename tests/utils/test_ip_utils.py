#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# vim: set ts=2 sw=2 et:

"""
单元测试: fkin_anfu.utils.ip_utils

说明：
测试ip_utils功能正常、测试ip边界

@author: cyhfvg
@date: 2025/07/09
"""
import pytest

from fkin_anfu.utils.ip_utils import (
    extract_ipv4s_from_text,
    find_continuous_ranges,
    format_ip_range,
    group_ips_by_c_segment,
    is_ip_in_network,
    is_valid_ipv4,
    normalize_ipv4_string,
    omni_extend_ip_list,
    parse_ip_range,
    shrink_ip_list,
)


@pytest.mark.parametrize(
    "ip,expected",
    [
        ("127.0.0.1", True),
        ("256.0.0.1", False),
        ("abc.def", False),
    ],
)
def test_is_valid_ipv4(ip: str, expected: bool):
    """参数化测试 is_valid_ipv4 判断合法性"""
    assert is_valid_ipv4(ip) is expected


@pytest.mark.parametrize(
    "ip,cidr,expected",
    [
        ("192.168.1.1", "192.168.1.0/24", True),
        ("192.168.2.1", "192.168.1.0/24", False),
    ],
)
def test_is_ip_in_network(ip: str, cidr: str, expected: bool):
    """参数化测试 is_ip_in_network 的网段包含关系"""
    assert is_ip_in_network(ip, cidr) is expected


def test_extract_ipv4s_from_text():
    """测试 extract_ipv4s_from_text 从文本中提取 IP 的能力"""
    text = "invalid 10.0.0.1 and 999.999.999.999 and 192.168.1.1"
    result = extract_ipv4s_from_text(text)
    assert result == ["10.0.0.1", "192.168.1.1"]


@pytest.mark.parametrize(
    "input_ip,expected",
    [
        (" １．２．３．４ ", ""),
        (" 1．2．3．4 ", "1.2.3.4"),
        ("1。2。3。4", "1.2.3.4"),
    ],
)
def test_normalize_ipv4_string(input_ip: str, expected: str):
    """参数化测试 normalize_ipv4_string 对异常字符的清洗效果"""
    assert normalize_ipv4_string(input_ip) == expected


@pytest.mark.parametrize(
    "ip_range,expected",
    [
        ("127.0.0.1-127.0.0.3", ["127.0.0.1", "127.0.0.2", "127.0.0.3"]),
        ("127.0.0.1-3", ["127.0.0.1", "127.0.0.2", "127.0.0.3"]),
        ("127.0.0.3-127.0.0.1", []),
        ("invalid", []),
    ],
)
def test_parse_ip_range(ip_range: str, expected: list[str]):
    """参数化测试 parse_ip_range 展开范围的正确性"""
    assert parse_ip_range(ip_range) == expected


def test_omni_extend_ip_list():
    """测试 omni_extend_ip_list 能正确识别单 IP、CIDR、范围"""
    assert omni_extend_ip_list("127.0.0.1") == ["127.0.0.1"]
    assert omni_extend_ip_list("127.0.0.1-127.0.0.2") == ["127.0.0.1", "127.0.0.2"]
    r = omni_extend_ip_list("192.168.1.0/30")
    assert set(r) == {"192.168.1.1", "192.168.1.2"}


def test_group_ips_by_c_segment():
    """测试 group_ips_by_c_segment 的分段能力"""
    ip_list = ["10.0.0.1", "10.0.0.2", "10.0.1.1"]
    result = group_ips_by_c_segment(ip_list)
    assert result == {
        "10.0.0": ["10.0.0.1", "10.0.0.2"],
        "10.0.1": ["10.0.1.1"],
    }


def test_group_ips_by_c_segment_mixed():
    """测试 group_ips_by_c_segment 对乱序与非法 IP 的过滤能力"""
    ip_list = ["10.0.0.2", "not.an.ip", "10.0.1.1", "10.0.0.1"]
    result = group_ips_by_c_segment(ip_list)
    assert result == {
        "10.0.0": ["10.0.0.2", "10.0.0.1"],
        "10.0.1": ["10.0.1.1"],
    }


def test_find_continuous_ranges():
    """测试 find_continuous_ranges 能正确识别连续 IP 段"""
    ip_list = ["10.0.0.1", "10.0.0.2", "10.0.0.3", "10.0.0.5"]
    ranges = find_continuous_ranges(ip_list)
    assert ranges == [("10.0.0.1", "10.0.0.3"), ("10.0.0.5", "10.0.0.5")]


@pytest.mark.parametrize(
    "start_ip,end_last,expected",
    [
        ("10.0.0.1", 5, "10.0.0.1-5"),
        ("invalid", 5, ""),
    ],
)
def test_format_ip_range(start_ip: str, end_last: int, expected: str):
    """参数化测试 format_ip_range 输出格式"""
    assert format_ip_range(start_ip, end_last) == expected


@pytest.mark.parametrize(
    "ip_list,expected",
    [
        (["10.0.0.1", "10.0.0.2", "10.0.0.3", "10.0.0.5"], ["10.0.0.1-3", "10.0.0.5"]),
        (["10.0.0.1"], ["10.0.0.1"]),
        ([], []),
    ],
)
def test_shrink_ip_list(ip_list: list[str], expected: list[str]):
    """参数化测试 shrink_ip_list 是否能将 IP 合并成范围"""
    assert shrink_ip_list(ip_list) == expected
