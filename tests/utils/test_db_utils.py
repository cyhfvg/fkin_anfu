#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# vim: set ts=2 sw=2 et:

"""
单元测试: fkin_anfu.utils.db_utils

说明：
- 采用 unittest.mock 替代真实数据库连接
- 保障 CI 环境中无依赖真实数据库即可执行

@author: cyhfvg
@date: 2025/04/24
"""

from unittest.mock import MagicMock, patch

import pytest
from pandas import DataFrame
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from fkin_anfu.utils.db_utils import (
    check_mysql_connection,
    get_mysql_engine,
    is_table_exists,
    safe_scalar,
    truncate_table,
    write_df_to_mysql,
)


def test_safe_scalar_with_value():
    """测试 safe_scalar 正常提取 scalar 值"""
    mock_result = MagicMock()
    mock_result.scalar.return_value = "123"
    assert safe_scalar(mock_result, convert=int) == 123


def test_safe_scalar_with_none():
    """测试 safe_scalar 返回默认值"""
    mock_result = MagicMock()
    mock_result.scalar.return_value = None
    assert safe_scalar(mock_result, default=0) == 0


def test_safe_scalar_exception():
    """测试 safe_scalar 异常处理"""
    bad_result = MagicMock()
    bad_result.scalar.side_effect = Exception("scalar error")
    with pytest.raises(RuntimeError):
        safe_scalar(bad_result)


def test_check_mysql_connection_success():
    """测试 check_mysql_connection 成功连接"""
    mock_conn = MagicMock()
    mock_conn.execute.return_value = None
    mock_engine = MagicMock()
    mock_engine.connect.return_value.__enter__.return_value = mock_conn
    assert check_mysql_connection(mock_engine) is True


def test_check_mysql_connection_failure():
    """测试 check_mysql_connection 异常返回 False"""
    mock_engine = MagicMock()
    mock_engine.connect.side_effect = SQLAlchemyError("mock error")
    assert check_mysql_connection(mock_engine) is False


@pytest.mark.parametrize("scalar_value,expected", [(1, True), (0, False)])
def test_is_table_exists_variants(scalar_value, expected):
    """测试 is_table_exists 返回 True / False"""
    mock_result = MagicMock()
    mock_result.scalar.return_value = scalar_value
    mock_conn = MagicMock()
    mock_conn.execute.return_value = mock_result
    mock_engine = MagicMock()
    mock_engine.connect.return_value.__enter__.return_value = mock_conn
    assert is_table_exists("any_table", mock_engine) is expected


def test_truncate_table_table_not_exist():
    """测试 truncate_table 跳过不存在的表"""
    engine = MagicMock(spec=Engine)
    with patch("fkin_anfu.utils.db_utils.is_table_exists", return_value=False):
        truncate_table("not_exists", engine)


# Mock出来的engine不符合df.to_sql的engine参数类型，生产不影响，忽略告警
@pytest.mark.filterwarnings("ignore::UserWarning")
def test_write_df_to_mysql_append_only():
    """测试 write_df_to_mysql 覆盖模式为 False"""
    engine = MagicMock(spec=Engine)
    df = DataFrame({"id": [1, 2], "name": ["a", "b"]})
    with patch("fkin_anfu.utils.db_utils.sql_table") as mock_table:
        mock_table.return_value.name = "mock_table"
        write_df_to_mysql(df, "mock_table", engine, overwrite=False)


# Mock出来的engine不符合df.to_sql的engine参数类型，生产不影响，忽略告警
@pytest.mark.filterwarnings("ignore::UserWarning")
def test_write_df_to_mysql_with_overwrite():
    """测试 write_df_to_mysql 覆盖模式为 True"""
    engine = MagicMock(spec=Engine)
    df = DataFrame({"id": [1], "name": ["x"]})
    with patch("fkin_anfu.utils.db_utils.sql_table") as mock_table:
        mock_table.return_value.name = "test_table"
        write_df_to_mysql(df, "test_table", engine, overwrite=True)


def test_get_mysql_engine_missing_key():
    """测试 get_mysql_engine 缺失字段异常"""
    invalid_env = {"user": "root", "password": "pwd", "port": "3306", "db": "test"}
    with pytest.raises(ValueError) as exc:
        get_mysql_engine(invalid_env)
    assert "数据库配置缺失字段" in str(exc.value)
