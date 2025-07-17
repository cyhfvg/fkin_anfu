#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# vim: set tabstop=2 shiftwidth=2 textwidth=80 expandtab :
#
#
"""
测试： output_utils

@author: cyhfvg
@date: 2025/07/17
"""
import json
from pathlib import Path

import pandas as pd
import pytest

from fkin_anfu.parsers.models.finding_result import FindingResult
from fkin_anfu.utils.output_utils import export_findings_to_excel, export_findings_to_json


@pytest.fixture
def sample_findings() -> list[FindingResult]:
    """
    构造示例 FindingResult 列表
    """
    return [
        FindingResult(
            ip="1.1.1.1",
            port=8080,
            protocol="http",
            url="http://1.1.1.1:8080",
            name="Jenkins Unauthorized",
            severity="high",
            source_tool="afrog",
            raw_path="afrog_result.json",
            extra={"detail": "unauthorized access"},
        )
    ]


def test_export_findings_to_json(tmp_path: Path, sample_findings: list[FindingResult]) -> None:
    """
    测试 JSON 导出功能是否成功，并验证内容结构
    """
    output_file = tmp_path / "result.json"
    export_findings_to_json(sample_findings, output_file)

    assert output_file.exists()
    with output_file.open(encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, list)
    assert data[0]["ip"] == "1.1.1.1"
    assert data[0]["severity"] == "high"
    assert data[0]["extra"]["detail"] == "unauthorized access"


def test_export_findings_to_excel(tmp_path: Path, sample_findings: list[FindingResult]) -> None:
    """
    测试 Excel 导出功能是否成功，并验证 DataFrame 内容
    """
    output_file = tmp_path / "result.xlsx"
    export_findings_to_excel(sample_findings, output_file)

    assert output_file.exists()
    df = pd.read_excel(output_file)

    assert not df.empty
    assert "ip" in df.columns
    assert df.iloc[0]["ip"] == "1.1.1.1"
    assert df.iloc[0]["severity"] == "high"
