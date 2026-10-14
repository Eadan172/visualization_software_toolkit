# -*- coding: utf-8 -*-
"""环境自检：解释器、依赖版本、Jmol / Java、示例数据。"""
from __future__ import annotations

import shutil
import sys

from .config import DATA, PKGS
from .engines.jmol import find_jmol_jar
from .utils import section_title


def cmd_check(_args) -> int:
    """打印环境自检结果；全部依赖可用时返回 0，否则返回 1。"""
    from importlib import metadata
    section_title("环境自检")
    print(f"Python      : {sys.version.split()[0]}")
    print(f"解释器      : {sys.executable}")
    ok = True
    for dist, label in PKGS:
        try:
            print(f"[OK] {label:<12}: {metadata.version(dist)}")
        except Exception:
            ok = False
            print(f"[!!] {label:<12}: 未安装")
    jmol = find_jmol_jar()
    print(f"[{'OK' if jmol else '--'}] {'JmolData':<10}: {jmol or '未安装（可选后备）'}")
    java = shutil.which("java")
    print(f"[{'OK' if java else '--'}] {'Java':<10}: {java or '未找到'}")
    for f in ("1ubq.pdb", "1hsg.pdb"):
        p = DATA / f
        print(f"[{'OK' if p.exists() else '--'}] {'示例数据':<9}: {p}")
    print("\n结论:", "环境完好，可直接使用 ✔" if ok else "存在缺失项 ✘（请重跑安装）")
    return 0 if ok else 1
