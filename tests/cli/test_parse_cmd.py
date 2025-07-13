#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# vim: set tabstop=2 shiftwidth=2 textwidth=80 expandtab :
#
#
"""
测试： parse_cmd test

@author: cyhfvg
@date: 2025/07/13
"""
import argparse
import json
from pathlib import Path

import pandas as pd
import pytest

from fkin_anfu.cli.parse_cmd import run_parse_command
from fkin_anfu.common.enums import OutputType, ParseType


@pytest.fixture
def sample_afrog_json(tmp_path: Path) -> Path:
    """
    构建合法的 Afrog JSON 文件，包含一条漏洞记录
    """
    content = [{"fulltarget": "http://127.0.0.1:8081", "pocinfo": {"infoname": "test vuln", "infoseg": "low"}}]
    json_path = tmp_path / "afrog_sample.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(content, f, indent=2)
    return json_path


def test_parse_cmd_json_output(tmp_path: Path, sample_afrog_json: Path):
    """
    测试 parse 子命令生成 JSON 文件
    """
    output_file = tmp_path / "result.json"

    args = argparse.Namespace(
        tool=["afrog"],
        path=[sample_afrog_json],
        recursive=[False],
        type=ParseType.VULN,
        output_file=output_file,
        output_type=OutputType.JSON,
    )

    run_parse_command(args)

    assert output_file.exists()
    with output_file.open("r", encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["ip"] == "127.0.0.1"
    assert data[0]["port"] == 8081


def test_parse_cmd_xlsx_output(tmp_path: Path, sample_afrog_json: Path):
    """
    测试 parse 子命令生成 Excel 文件
    """
    output_file = tmp_path / "result.xlsx"

    args = argparse.Namespace(
        tool=["afrog"],
        path=[sample_afrog_json],
        recursive=[False],
        type=ParseType.VULN,
        output_file=output_file,
        output_type=OutputType.XLSX,
    )

    run_parse_command(args)

    assert output_file.exists()
    df = pd.read_excel(output_file)
    assert not df.empty
    assert "ip" in df.columns
    assert df.iloc[0]["ip"] == "127.0.0.1"


def test_parse_cmd_tool_path_mismatch_should_raise(tmp_path: Path, sample_afrog_json: Path):
    """
    测试 tool、path、recursive 参数数量不一致时应抛出 ValueError
    """
    args = argparse.Namespace(
        tool=["afrog", "afrog"],
        path=[sample_afrog_json],
        recursive=[False],
        type=ParseType.VULN,
        output_file=tmp_path / "dummy.json",
        output_type=OutputType.JSON,
    )

    with pytest.raises(ValueError):
        run_parse_command(args)
