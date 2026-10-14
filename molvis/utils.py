# -*- coding: utf-8 -*-
"""通用小工具：路径规范化与终端标题。"""
from __future__ import annotations


def to_posix(p) -> str:
    """把 Windows 反斜杠路径转成正斜杠形式，供 PyMOL / Jmol 内联脚本使用。"""
    return str(p).replace("\\", "/")


def section_title(title: str) -> None:
    """打印一个由等号分隔的段落标题。"""
    print("\n" + "=" * 64)
    print(title)
    print("=" * 64)
