#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# vim: set tabstop=2 shiftwidth=2 textwidth=80 expandtab :
#
#
"""
fkin_anfu cli 主入口

@author: cyhfvg
@date: 2025/05/17
"""
import argparse

from fkin_anfu import __version__


def main() -> None:
    """
    fkin-anfu CLI 主入口，支持 --help 和 --version 参数。
    """
    parser = argparse.ArgumentParser(
        prog="fkin-anfu",
        description="fkin-anfu - Network Security Automation Toolkit",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}", help="显示当前版本号")

    # 默认行为打印帮助
    args = parser.parse_args()
    if not vars(args):  # 没有任何参数时
        parser.print_help()
