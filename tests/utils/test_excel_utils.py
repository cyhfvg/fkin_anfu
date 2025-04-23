#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# vim: set tabstop=2 shiftwidth=2 textwidth=100 expandtab :
#
"""
Excel 工具函数单元测试：读取 / 写入 / 合并单元格填充

依赖 pytest 自动执行
"""

from collections import OrderedDict
from pathlib import Path

from pandas import DataFrame

from fkin_anfu.utils.excel_utils import fill_merged_cells, read_excel, write_excel


def test_fill_merged_cells() -> None:
    """
    测试 fill_merged_cells 能正确对合并单元格空值列进行向下填充。
    """
    df = DataFrame(
        {
            "IP": ["192.168.1.1", "", "", "10.0.0.1", ""],
            "端口": ["80", "", "443", "", ""],
            "说明": ["a", "b", "", "", "e"],
        }
    )

    filled_df = fill_merged_cells(df, ["IP", "端口"])

    assert filled_df.loc[1, "IP"] == "192.168.1.1"
    assert filled_df.loc[2, "端口"] == "443"
    assert filled_df.loc[4, "IP"] == "10.0.0.1"


def test_write_and_read_excel(tmp_path: Path) -> None:
    """
    测试 write_excel + read_excel 可正确读写多 Sheet 文件。

    使用 pytest 的 tmp_path 保证测试文件自动清理。
    """
    file_path = tmp_path / "test_excel_output.xlsx"

    sheets = OrderedDict(
        {
            "资产清单": DataFrame({"IP": ["1.1.1.1", "2.2.2.2"], "负责人": ["张三", "李四"]}),
            "漏洞明细": DataFrame({"名称": ["RCE", "XSS"], "等级": ["高", "中"]}),
        }
    )

    write_excel(sheets, file_path)
    assert file_path.exists()

    result = read_excel(file_path, sheet_name=["资产清单", "漏洞明细"])
    assert isinstance(result, dict)
    assert result["资产清单"].equals(sheets["资产清单"])
    assert result["漏洞明细"].equals(sheets["漏洞明细"])
