#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# vim: set tabstop=2 shiftwidth=2 textwidth=80 expandtab :
#
#
"""
测试： afrog_parser

@author: cyhfvg
@date: 2025/07/13
"""
import json
from pathlib import Path

import pytest

from fkin_anfu.parsers.afrog_parser import AfrogParser
from fkin_anfu.parsers.models.finding_result import FindingResult


@pytest.fixture
def sample_afrog_json(tmp_path: Path) -> Path:
    """
    构建一个合法 Afrog JSON 文件，包含一条漏洞记录
    """
    content = [
        {
            "fulltarget": "http://192.168.1.10:8080",
            "pocinfo": {"infoname": "jenkins unauthorized access", "infoseg": "high"},
        }
    ]
    json_path = tmp_path / "afrog_sample.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(content, f, indent=2)
    return json_path


@pytest.fixture
def invalid_json_file(tmp_path: Path) -> Path:
    """
    构建一个格式非法的 JSON 文件
    """
    path = tmp_path / "bad.json"
    path.write_text("{ invalid json }", encoding="utf-8")
    return path


@pytest.fixture
def non_array_json_file(tmp_path: Path) -> Path:
    """
    构建一个顶层为 dict 的 JSON 文件，应触发类型错误
    """
    data = {"results": []}
    path = tmp_path / "non_array.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f)
    return path


def test_parse_valid_afrog_file(sample_afrog_json: Path):
    """
    测试解析单个合法 Afrog JSON 文件，验证字段提取与产品命中
    """
    parser = AfrogParser()
    results = parser.parse(sample_afrog_json, recursive=False)
    assert isinstance(results, list)
    assert len(results) == 1
    result: FindingResult = results[0]
    assert result.ip == "192.168.1.10"
    assert result.port == 8080
    assert result.product == "jenkins"
    assert result.severity == "high"


def test_parse_invalid_json_raises_valueerror(invalid_json_file: Path):
    """
    测试解析非法 JSON 文件应抛出 ValueError
    """
    parser = AfrogParser()
    with pytest.raises(ValueError):
        parser.parse(invalid_json_file, recursive=False)


def test_parse_non_array_json_raises_valueerror(non_array_json_file: Path):
    """
    测试顶层非数组结构的 JSON 文件应抛出 ValueError
    """
    parser = AfrogParser()
    with pytest.raises(ValueError):
        parser.parse(non_array_json_file, recursive=False)


@pytest.fixture
def recoverable_json_file(tmp_path: Path) -> Path:
    """
    构建一个末尾缺失 ] 的 Afrog JSON 文件，测试容错修复逻辑
    """
    broken_json = """
    [
        {
            "fulltarget": "http://10.0.0.1:8080",
            "pocinfo": {
                "infoname": "weak password",
                "title": "admin panel exposed",
                "infoseg": "high"
            }
        }
    """  # 注意此处缺少结尾的 ]
    path = tmp_path / "broken.json"
    path.write_text(broken_json, encoding="utf-8")
    return path


def test_parse_recoverable_missing_bracket(recoverable_json_file: Path):
    """
    测试尾部缺失 ] 的 Afrog JSON 文件可被容错修复并成功解析
    """
    parser = AfrogParser()
    results = parser.parse(recoverable_json_file, recursive=False)
    assert isinstance(results, list)
    assert len(results) == 1
    result = results[0]
    assert result.ip == "10.0.0.1"
    assert result.port == 8080
    assert result.name == "weak password"
    assert result.severity == "high"
