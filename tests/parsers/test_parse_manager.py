#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# vim: set tabstop=2 shiftwidth=2 textwidth=80 expandtab :
#
#
"""
测试： parse_manager test

@author: cyhfvg
@date: 2025/07/13
"""
import json
from pathlib import Path

import pytest

from fkin_anfu.common.enums import ParseType
from fkin_anfu.parsers.models.finding_result import FindingResult
from fkin_anfu.parsers.parse_manager import dispatch_parsers


@pytest.fixture
def afrog_vuln_json(tmp_path: Path) -> Path:
    """
    构建合法的 Afrog 漏洞结果 JSON 文件（finding_type = vuln）
    """
    content = [
        {
            "fulltarget": "http://192.168.1.10:8080",
            "pocinfo": {"infoname": "jenkins unauthorized access", "infoseg": "high"},
        }
    ]
    path = tmp_path / "afrog_vuln.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(content, f, indent=2)
    return path


@pytest.fixture
def afrog_asset_json(tmp_path: Path) -> Path:
    """
    构建合法的 Afrog 资产识别 JSON 文件（finding_type = asset）
    """
    content = [
        {"fulltarget": "http://192.168.1.20:8443", "pocinfo": {"infoname": "nginx fingerprint", "infoseg": "info"}}
    ]
    path = tmp_path / "afrog_asset.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(content, f, indent=2)
    return path


def test_dispatch_single_afrog_vuln(afrog_vuln_json: Path):
    """
    测试 dispatch_parsers 能正确解析 Afrog 漏洞结果并保留 finding_type = vuln 的记录
    """
    tasks = [("afrog", afrog_vuln_json, False)]
    results = dispatch_parsers(tasks, parse_type=ParseType.VULN)

    assert isinstance(results, list)
    assert len(results) == 1
    item: FindingResult = results[0]
    assert item.ip == "192.168.1.10"
    assert item.port == 8080
    assert item.product == "jenkins"
    assert item.finding_type == "vuln"
    assert item.severity == "high"


def test_dispatch_filters_by_type(afrog_asset_json: Path):
    """
    测试 dispatch_parsers 过滤掉 finding_type != vuln 的记录
    """
    tasks = [("afrog", afrog_asset_json, False)]
    results = dispatch_parsers(tasks, parse_type=ParseType.VULN)

    assert isinstance(results, list)
    assert len(results) == 0
