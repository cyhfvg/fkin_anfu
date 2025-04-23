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
from threading import Lock
from typing import Callable, Dict, Tuple

from colorama import Fore, Style
from colorama import init as colorama_init

__all__ = ['debug_print']

# 初始化 colorama 自动复位颜色
colorama_init(autoreset=True)

# 线程锁，保证日志打印不穿插
_log_lock = Lock()

# 日志配置
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s", handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)
# 不希望日志冒泡到父 logger，防止重复输出log
logger.propagate = False

# 类型注解：日志方法 + color 字符串
_LEVEL_MAP: Dict[str, Tuple[Callable[[str], None], str]] = {
    "debug": (logging.getLogger(__name__).debug, Fore.BLUE),
    "info": (logging.getLogger(__name__).info, Fore.CYAN),
    "success": (logging.getLogger(__name__).info, Fore.GREEN),
    "warning": (logging.getLogger(__name__).warning, Fore.YELLOW),
    "error": (logging.getLogger(__name__).error, Fore.RED),
}


def debug_print(level: str, msg: str) -> None:
    """
    线程安全的统一日志输出接口，支持彩色控制台输出。

    :param level: 日志级别，如 "debug", "info", "success", "error", "warning"
    :param msg: 要输出的信息内容
    """
    level = level.lower()
    log_func, color = _LEVEL_MAP.get(level, (logger.info, Fore.CYAN))
    tag = f"{color}[{level.upper()}]{Style.RESET_ALL}"

    with _log_lock:
        log_func(f"{tag} {msg}")
