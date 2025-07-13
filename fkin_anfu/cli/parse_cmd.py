#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# vim: set tabstop=2 shiftwidth=2 textwidth=80 expandtab :
#
#
"""
子命令 parse: 调用指定工具解析扫描结果，并导出为统一格式。

@author: cyhfvg
@date: 2025/07/12
"""
import argparse
import json
from pathlib import Path

import pandas as pd

from fkin_anfu.common.enums import OutputType, ParseType
from fkin_anfu.parsers.parse_manager import dispatch_parsers
from fkin_anfu.utils.log_utils import debug_print


def register_parse_subcommand(subparsers: argparse._SubParsersAction) -> None:
    """
    注册 parse 子命令及其参数

    Args:
        subparsers (argparse._SubParsersAction): 主命令的子命令注册器
    """
    parser = subparsers.add_parser("parse", help="解析扫描结果并导出")

    parser.add_argument("--tool", required=True, action="append", help="扫描工具名称，如 afrog")
    parser.add_argument("--path", required=True, action="append", type=Path, help="扫描结果路径，文件或目录")
    parser.add_argument(
        "--recursive",
        required=True,
        action="append",
        type=lambda x: x.lower() == "true",
        help="是否递归目录解析,True/False",
    )
    parser.add_argument(
        "--type", required=True, type=ParseType, choices=list(ParseType), help="解析结果类型: vuln 或 asset"
    )
    parser.add_argument("--output-file", required=True, type=Path, help="导出结果的目标文件路径")
    parser.add_argument(
        "--output-type", required=True, type=OutputType, choices=list(OutputType), help="输出类型: xlsx 或 json"
    )
    parser.set_defaults(func=run_parse_command)


def run_parse_command(args: argparse.Namespace) -> None:
    """
    运行 parse 子命令逻辑：调用解析器，导出结果。

    Args:
        args (argparse.Namespace): 解析后的命令行参数
    """
    tools = args.tool
    paths = args.path
    recursives = args.recursive

    if not (len(tools) == len(paths) == len(recursives)):
        raise ValueError("[parse_cmd] --tool、--path、--recursive 参数数量必须一致")

    task_list = list(zip(tools, paths, recursives))
    debug_print("INFO", f"[parse_cmd] 解析任务数: {len(task_list)}")

    # 调用解析器调度器
    results = dispatch_parsers(task_list, parse_type=args.type)

    if not results:
        debug_print("INFO", "[parse_cmd] 无解析结果，跳过输出")
        return

    output_path = args.output_file
    output_type = args.output_type

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 转换为结构化数据列表
    dict_rows = [item.to_dict() for item in results]

    # TODO: output
    try:
        if output_type == OutputType.JSON:
            with output_path.open("w", encoding="utf-8") as f:
                json.dump(dict_rows, f, indent=2, ensure_ascii=False)
            debug_print("INFO", f"[parse_cmd] 结果已保存为 JSON: {output_path}")

        elif output_type == OutputType.XLSX:
            df = pd.DataFrame(dict_rows)
            df.to_excel(output_path, index=False)
            debug_print("INFO", f"[parse_cmd] 结果已保存为 Excel: {output_path}")
    except Exception as why:
        debug_print("ERROR", f"[parse_cmd] 输出结果失败: {why}")
        raise
