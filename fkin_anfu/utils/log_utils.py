#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# vim: set tabstop=2 shiftwidth=2 textwidth=80 expandtab :
#
#
"""
日志封装(colorama + logging + Lock)

@author: cyhfvg
@date: 2025/04/20
"""

import logging
import random
import shutil
from threading import Lock
from typing import Callable, Dict, Literal, Tuple, Union

from colorama import Style
from pyfiglet import Figlet

from fkin_anfu.utils.color_utils import _COLOR_MAP, BLUE, CYAN, GREEN, RED, YELLOW

__all__ = ['debug_print']

# 线程锁，保证日志打印不穿插
_log_lock = Lock()

# 创建一个独立的 logger, 避免污染 root logger
logger = logging.getLogger("fkin_anfu_log_utils")
logger.setLevel(logging.DEBUG)
# 不希望日志冒泡到父 logger，防止重复输出log
logger.propagate = False

# 如果没有 handler，主动加上
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# 默认 fallback设置
_DEFAULT_LOG_FUNC: Callable[[str], None] = logger.info
_DEFAULT_COLOR_FUNC: Callable[[str], str] = CYAN

# 日志级别与颜色函数的映射表
_LEVEL_MAP: Dict[str, Tuple[Callable[[str], None], Callable[[str], str]]] = {
    "debug": (logger.debug, BLUE),
    "info": (logger.info, CYAN),
    "success": (logger.info, GREEN),
    "warning": (logger.warning, YELLOW),
    "error": (logger.error, RED),
}


def debug_print(level: str, msg: str) -> None:
    """
    线程安全的统一日志输出接口，支持彩色控制台输出。

    :param level: 日志级别，如 "debug", "info", "success", "error", "warning"
    :param msg: 要输出的信息内容
    """
    level = level.lower()
    log_func, color_func = _LEVEL_MAP.get(level, (_DEFAULT_LOG_FUNC, _DEFAULT_COLOR_FUNC))
    tag = color_func(f"[{level.upper()}]")

    with _log_lock:
        log_func(f"{tag} {msg}")


def print_ascii(
    text: str,
    justify: Literal["left", "center", "right"],
    color_code: str,
    width: Union[int, Literal["auto"]] = "auto",
) -> None:
    """
    打印 ASCII 艺术字；使用 print 输出，并通过 _log_lock 保证原子性。

    颜色策略:
      - color_code == "random": 从 _COLOR_MAP.values() 随机取色。
      - color_code 命中 _COLOR_MAP: 使用对应颜色。
      - 其他值: 不加颜色，直接渲染文字。

    宽度策略:
      - width == "auto": 使用 shutil.get_terminal_size 跨平台获取终端宽度；失败回退 100，并限制在 [10, 240]。
      - width 为正整数: 直接使用；非正或异常则回退 100。

    Args:
        text (str): 待输出文本。
        justify (Literal["left", "center", "right"]): 对齐方式。
        color_code (str): 颜色代码或 "random"。
        width (int | Literal["auto"]): 渲染宽度，默认 "auto" 自适应。
    """
    # 1) 解析宽度，自适应跨平台终端
    try:
        if width == "auto":
            cols = shutil.get_terminal_size(fallback=(100, 24)).columns
            render_width = max(10, min(cols, 240))
        else:
            render_width = int(width)
            if render_width <= 0:
                render_width = 100
    except Exception:
        render_width = 100

    # 2) 选择颜色；未命中则不着色
    try:
        if color_code.lower() == "random":
            color_prefix = random.choice(list(_COLOR_MAP.values()))
        else:
            color_prefix = _COLOR_MAP.get(color_code, "")  # 未命中为空串
    except Exception:
        color_prefix = ""  # 颜色选择异常时不着色

    # 3) 渲染 ASCII（强依赖 pyfiglet）
    try:
        fig = Figlet(width=render_width, justify=justify)
        art = fig.renderText(text)
    except Exception:
        # 强依赖场景下，渲染异常直接抛出
        raise

    # 4) 原子输出
    try:
        with _log_lock:
            if color_prefix:
                # 注意: art 末尾通常自带换行；使用 end="" 避免重复换行
                print(f"{Style.BRIGHT}{color_prefix}{art}{Style.RESET_ALL}", end="")
            else:
                print(art, end="")
    except Exception:
        raise
