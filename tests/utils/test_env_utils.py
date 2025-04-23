#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# vim: set tabstop=2 shiftwidth=2 textwidth=100 expandtab :
#
"""
测试 env_utils 环境变量读取逻辑与结构化组识别能力

@author: cyhfvg
@date: 2025/04/23
"""

import os

import pytest

from fkin_anfu.utils.env_utils import get_env_bool, get_env_groups_structured, get_env_int, get_env_str


@pytest.fixture(autouse=True)
def setup_env(monkeypatch):
    """
    自动设置测试环境变量
    """
    # 基础变量
    monkeypatch.setenv("TEST_KEY", "value")
    monkeypatch.setenv("INT_KEY", "123")
    monkeypatch.setenv("BOOL_KEY_TRUE", "true")
    monkeypatch.setenv("BOOL_KEY_FALSE", "no")

    # MYSQL 第1组
    monkeypatch.setenv("MYSQL_1_HOST", "127.0.0.1")
    monkeypatch.setenv("MYSQL_1_PORT", "3306")
    monkeypatch.setenv("MYSQL_1_USER", "root")
    monkeypatch.setenv("MYSQL_1_PASSWORD", "rootpwd")

    # MYSQL 第2组
    monkeypatch.setenv("MYSQL_2_HOST", "192.168.1.1")
    monkeypatch.setenv("MYSQL_2_PORT", "3307")
    monkeypatch.setenv("MYSQL_2_USER", "admin")
    monkeypatch.setenv("MYSQL_2_PASSWORD", "adminpwd")

    yield


def test_get_env_str_basic():
    """测试字符串类型环境变量获取"""
    assert get_env_str("TEST_KEY") == "value"
    assert get_env_str("NON_EXIST", default="abc") == "abc"
    with pytest.raises(EnvironmentError):
        get_env_str("NON_EXIST", strict=True)


def test_get_env_int_basic():
    """测试整数类型环境变量获取"""
    assert get_env_int("INT_KEY") == 123
    assert get_env_int("NON_EXIST", default=456) == 456
    with pytest.raises(EnvironmentError):
        get_env_int("NON_EXIST", strict=True)
    os.environ["BAD_INT"] = "not_a_number"
    with pytest.raises(ValueError):
        get_env_int("BAD_INT")


def test_get_env_bool_basic():
    """测试布尔类型环境变量获取"""
    assert get_env_bool("BOOL_KEY_TRUE") is True
    assert get_env_bool("BOOL_KEY_FALSE") is False
    assert get_env_bool("NON_EXIST", default=True) is True
    with pytest.raises(EnvironmentError):
        get_env_bool("NON_EXIST", strict=True)


def test_get_env_groups_structured_success():
    """测试多组配置自动识别"""
    result = get_env_groups_structured("MYSQL", ["HOST", "PORT", "USER", "PASSWORD"])
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["host"] == "127.0.0.1"
    assert result[1]["user"] == "admin"


def test_get_env_groups_structured_missing_field():
    """测试配置字段缺失时报错"""
    os.environ["MYSQL_3_HOST"] = "10.0.0.10"
    with pytest.raises(EnvironmentError) as e:
        get_env_groups_structured("MYSQL", ["HOST", "PORT", "USER", "PASSWORD"])
    assert "MYSQL_3_" in str(e.value)
