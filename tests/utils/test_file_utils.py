#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# vim: set tabstop=2 shiftwidth=2 textwidth=80 expandtab :
#
#
"""
测试：文件工具

@author: cyhfvg
@date: 2025/04/22
"""
from pathlib import Path

import pytest

from fkin_anfu.utils.file_utils import (
    append_to_file,
    copy_file,
    delete_file,
    is_file_exists,
    read_file,
    safe_read_lines,
    write_file,
)


@pytest.fixture
def sample_file():
    """创建一个临时文件并在测试后删除"""
    file_path = Path("sample_test_file.txt")
    content = ["Line 1", "Line 2", "Line 3"]
    write_file(file_path, content)
    yield file_path
    file_path.unlink(missing_ok=True)  # 删除临时文件


@pytest.fixture
def sample_directory():
    """创建一个临时目录并在测试后删除"""
    dir_path = Path("sample_test_directory")
    dir_path.mkdir(parents=True, exist_ok=True)
    yield dir_path
    if dir_path.exists():
        for file in dir_path.glob("*"):
            file.unlink()  # 删除目录中的所有文件
        dir_path.rmdir()  # 删除目录


@pytest.fixture
def utf8_file(tmp_path: Path) -> Path:
    """
    构造 UTF-8 编码的测试文件
    """
    content = ["第一行", "第二行", "第三行"]
    file_path = tmp_path / "utf8.txt"
    file_path.write_text("\n".join(content), encoding="utf-8")
    return file_path


@pytest.fixture
def gbk_file(tmp_path: Path) -> Path:
    """
    构造 GBK 编码的测试文件
    """
    content = ["测试一行", "测试第二行"]
    file_path = tmp_path / "gbk.txt"
    file_path.write_text("\n".join(content), encoding="gbk")
    return file_path


@pytest.fixture
def binary_file(tmp_path: Path) -> Path:
    """
    构造包含非法 UTF-8 字节的测试文件（模拟乱码或非文本文件）
    """
    file_path = tmp_path / "binary.txt"
    file_path.write_bytes(b"\xff\xfe\nabc\n\xe4\xb8\xad\xe6\x96\x87\n")
    return file_path


def test_is_file_exists(sample_file):
    """
    测试 is_file_exists() 方法，检查文件是否存在。
    """
    assert is_file_exists(sample_file) is True  # 文件应存在
    assert is_file_exists("non_existing_file.txt") is False  # 文件不存在


def test_read_file(sample_file):
    """
    测试 read_file() 方法，检查文件内容读取。
    """
    content = read_file(sample_file)
    assert content == ["Line 1\n", "Line 2\n", "Line 3\n"]  # 返回的内容应与写入内容匹配


def test_write_file():
    """
    测试 write_file() 方法，写入内容到文件。
    """
    file_path = Path("write_test_file.txt")
    content = ["First line", "Second line"]
    write_file(file_path, content)

    # 检查文件内容
    with file_path.open('r', encoding='utf-8') as file:
        lines = file.readlines()
        assert lines == ["First line\n", "Second line\n"]

    file_path.unlink()  # 删除测试文件


def test_append_to_file(sample_file):
    """
    测试 append_to_file() 方法，将内容追加到文件。
    """
    content_to_append = ["Line 4", "Line 5"]
    append_to_file(sample_file, content_to_append)

    content = read_file(sample_file)
    assert content == ["Line 1\n", "Line 2\n", "Line 3\n", "Line 4\n", "Line 5\n"]  # 内容应该被追加


def test_copy_file(sample_file):
    """
    测试 copy_file() 方法，复制文件。
    """
    copied_file = Path("copied_sample_file.txt")
    copy_file(sample_file, copied_file)

    # 验证文件复制
    assert is_file_exists(copied_file) is True
    content = read_file(copied_file)
    assert content == ["Line 1\n", "Line 2\n", "Line 3\n"]  # 内容应一致

    copied_file.unlink()  # 删除复制的文件


def test_delete_file(sample_file, sample_directory):
    """
    测试 delete_file() 方法，删除文件和目录。
    """
    # 删除文件
    delete_file(sample_file)
    assert is_file_exists(sample_file) is False  # 文件应被删除

    # 创建一个目录并删除
    sample_subfile = sample_directory / "subfile.txt"
    write_file(sample_subfile, ["Test content"])
    delete_file(sample_subfile)
    assert is_file_exists(sample_subfile) is False  # 子文件应被删除

    # 删除目录
    delete_file(sample_directory)
    assert is_file_exists(sample_directory) is False  # 目录应被删除


def test_file_not_found_exception():
    """
    测试文件不存在时的方法行为（例如删除或读取文件）。
    """
    with pytest.raises(FileNotFoundError):
        read_file("non_existing_file.txt")

    with pytest.raises(FileNotFoundError):
        copy_file("non_existing_file.txt", "new_file.txt")


def test_safe_read_lines_utf8(utf8_file: Path) -> None:
    """
    验证 safe_read_lines 能正确读取 UTF-8 编码文件
    """
    result = safe_read_lines(utf8_file)
    assert result == ["第一行", "第二行", "第三行"]


def test_safe_read_lines_gbk(gbk_file: Path) -> None:
    """
    验证 safe_read_lines 能在 UTF-8 解码失败时自动回退到 GBK 并成功读取内容
    """
    result = safe_read_lines(gbk_file)
    assert result == ["测试一行", "测试第二行"]


def test_safe_read_lines_binary(binary_file: Path) -> None:
    """
    验证 safe_read_lines 能容错处理非 UTF-8 合法字节流并返回部分可解析文本
    """
    result = safe_read_lines(binary_file)
    assert isinstance(result, list)
    assert any("abc" in line or "中文" in line for line in result)
