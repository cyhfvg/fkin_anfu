#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# vim: set tabstop=2 shiftwidth=2 textwidth=80 expandtab :
#
#
"""
测试：路径工具

@author: cyhfvg
@date: 2025/04/22
"""
from pathlib import Path

from fkin_anfu.utils.path_utils import (
    create_directory,
    get_file_extension,
    get_parent_directory,
    is_dir,
    is_file,
    is_path_exists,
    join_paths,
)


def test_is_file():
    """
    测试 is_file() 函数，检查给定路径是否是文件。

    场景：
        - 使用真实的文件路径进行测试
        - 使用不存在的文件路径进行测试
    """
    # 使用实际文件路径和不存在的文件路径
    assert not is_file("test.txt")
    assert not is_file(Path("test.txt"))


def test_is_dir():
    """
    测试 is_dir() 函数，检查给定路径是否是目录。

    场景：
        - 使用实际的目录路径进行测试
        - 使用不存在的目录路径进行测试
    """
    assert not is_dir("some_folder")
    assert not is_dir(Path("some_folder"))


def test_is_path_exists():
    """
    测试 is_path_exists() 函数，检查路径是否存在。

    场景：
        - 使用存在的路径进行测试
        - 使用不存在的路径进行测试
    """
    assert not is_path_exists("existing_folder")
    assert not is_path_exists(Path("existing_folder"))


def test_get_file_extension():
    """
    测试 get_file_extension() 函数，获取文件的扩展名。

    场景：
        - 使用实际文件路径测试扩展名提取
    """
    assert get_file_extension("test.txt") == ".txt"
    assert get_file_extension(Path("test.csv")) == ".csv"


def test_get_parent_directory():
    """
    测试 get_parent_directory() 函数，获取路径的父目录。

    场景：
        - 使用实际文件路径测试获取父目录
        - 测试文件路径无父目录的情况
    """
    assert get_parent_directory("folder/subfolder/test.txt") == Path("folder/subfolder")
    assert get_parent_directory("test.txt") == Path('./')


def test_create_directory():
    """
    测试 create_directory() 函数，确保目录创建正常。

    场景：
        - 创建新目录
        - 尝试创建已存在的目录（应抛出 FileExistsError）
    """
    try:
        create_directory("new_folder")
        assert is_dir("new_folder")
    except Exception as e:
        assert False, f"Unexpected error: {e}"

    try:
        create_directory("new_folder")
    except FileExistsError:
        pass  # 正确的行为


def test_join_paths():
    """
    测试 join_paths() 函数，检查路径拼接是否正确。

    场景：
        - 拼接多个路径片段
    """
    assert join_paths("folder", "subfolder", "file.txt") == Path("folder/subfolder/file.txt")
    assert join_paths("folder", "file.txt") == Path("folder/file.txt")
