#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# vim: set tabstop=2 shiftwidth=2 textwidth=80 expandtab :
#
#
"""
测试：日志封装(colorama + logging + Lock)

@author: cyhfvg
@date: 2025/04/20
"""
import os
import shutil
from typing import Dict

import pytest
from colorama import Fore, Style

import fkin_anfu.utils.log_utils as log_utils
from fkin_anfu.utils.log_utils import debug_print, print_ascii


def test_debug_print_all_levels():
    """
    验证 debug_print 在不同日志等级下能够正确调用并输出，不抛异常。
    包括已知等级：debug, info, success, warning, error，以及未知等级 fallback。
    """
    levels = ["debug", "info", "success", "warning", "error", "unknown"]
    for lvl in levels:
        debug_print(lvl, f"Test message for level: {lvl}")


class _StubFiglet:
    """
    pyfiglet.Figlet 的桩对象.
    仅记录参数并将其编码进返回结果, 以便测试断言.
    """

    def __init__(self, width: int, justify: str) -> None:
        self.width = width
        self.justify = justify

    def renderText(self, text: str) -> str:
        # 返回格式: "[{justify}:{width}]{text}\n"
        return f"[{self.justify}:{self.width}]{text}\n"


@pytest.fixture(autouse=True)
def patch_figlet(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    自动将被测模块中的 Figlet 替换为桩对象, 避免依赖真实渲染.
    """
    monkeypatch.setattr(log_utils, "Figlet", _StubFiglet)


@pytest.fixture
def patched_colormap(monkeypatch: pytest.MonkeyPatch) -> Dict[str, str]:
    """
    替换 _COLOR_MAP, 使颜色选择可控且可断言.
    """
    cmap = {"red": Fore.RED, "cyan": Fore.CYAN}
    # print_ascii 中通过 "from ... import _COLOR_MAP" 导入为模块内变量,
    # 因此需要替换 log_utils._COLOR_MAP.
    monkeypatch.setattr(log_utils, "_COLOR_MAP", cmap, raising=True)
    return cmap


def test_known_color_left_align_fixed_width(
    monkeypatch: pytest.MonkeyPatch,
    patched_colormap: Dict[str, str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """
    指定颜色与对齐, 固定宽度; 期望包含加亮色前缀与 RESET 后缀, 并带有编码的桩文本.
    """
    print_ascii("HELLO", justify="left", color_code="cyan", width=80)
    out = capsys.readouterr().out

    # 前缀包含加亮与 Fore.CYAN
    assert out.startswith(f"{Style.BRIGHT}{patched_colormap['cyan']}"), "应包含指定颜色前缀"
    # 内容应包含桩编码的对齐与宽度
    assert "[left:80]HELLO\n" in out
    # 结尾应包含 RESET
    assert out.endswith(Style.RESET_ALL), "应在末尾包含 RESET 转义码"


def test_unknown_color_no_color_output(
    monkeypatch: pytest.MonkeyPatch,
    patched_colormap: Dict[str, str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """
    未命中颜色码时, 不应上色; 输出中不应包含 BRIGHT 或 RESET.
    """
    print_ascii("WORLD", justify="center", color_code="unknown_color", width=100)
    out = capsys.readouterr().out

    assert "[center:100]WORLD\n" in out
    assert Style.BRIGHT not in out
    assert Style.RESET_ALL not in out
    # 也不应包含任一已知 Fore 前缀
    for v in patched_colormap.values():
        assert v not in out


def test_random_color_choice_stabilized(
    monkeypatch: pytest.MonkeyPatch,
    patched_colormap: Dict[str, str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """
    随机颜色时, 固定 random.choice 的返回值, 以保证可断言.
    """
    # 固定随机返回 Fore.RED
    monkeypatch.setattr(log_utils.random, "choice", lambda seq: Fore.RED)
    print_ascii("RANDOM", justify="right", color_code="random", width=120)
    out = capsys.readouterr().out

    assert out.startswith(f"{Style.BRIGHT}{Fore.RED}")
    assert "[right:120]RANDOM\n" in out
    assert out.endswith(Style.RESET_ALL)


def test_width_auto_uses_terminal_size(
    monkeypatch: pytest.MonkeyPatch,
    patched_colormap: Dict[str, str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """
    width='auto' 时应读取终端列宽; 使用 fallback 并限幅.
    """
    # 将 get_terminal_size 固定为 130 列
    monkeypatch.setattr(
        shutil,
        "get_terminal_size",
        lambda fallback=(100, 24): os.terminal_size((130, 24)),  # type: ignore[call-arg]
    )
    print_ascii("AUTO", justify="left", color_code="red", width="auto")
    out = capsys.readouterr().out

    # 应编码为 130 列
    assert "[left:130]AUTO\n" in out
    # 有色输出
    assert out.startswith(f"{Style.BRIGHT}{patched_colormap['red']}")
    assert out.endswith(Style.RESET_ALL)


def test_width_invalid_negative_fallback_to_100(
    monkeypatch: pytest.MonkeyPatch,
    patched_colormap: Dict[str, str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """
    非法宽度(<=0)时回退到 100.
    """
    print_ascii("NEG", justify="center", color_code="cyan", width=-5)
    out = capsys.readouterr().out
    assert "[center:100]NEG\n" in out
