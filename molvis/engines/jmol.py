# -*- coding: utf-8 -*-
"""Jmol 引擎适配：纯软件无头渲染输出 PNG（零 OpenGL 依赖的稳妥后备）。"""
from __future__ import annotations

import os
import shutil
import subprocess

from ..config import SOFTWARE, full_canvas
from ..utils import to_posix


def find_jmol_jar():
    """在 software/ 目录下递归查找 JmolData.jar，找不到返回 None。"""
    if not SOFTWARE.exists():
        return None
    hits = sorted(SOFTWARE.rglob("JmolData.jar"))
    return hits[0] if hits else None


def jmol_render(pdb_path, png_path, canvas: dict | None = None) -> bool:
    """用 JmolData 无头渲染一张 PNG；canvas 控制输出尺寸。"""
    jar = find_jmol_jar()
    if not jar:
        print("[--] 未找到 JmolData.jar，跳过 Jmol 渲染")
        return False
    java = shutil.which("java")
    if not java:
        print("[--] 未找到 Java，跳过 Jmol 渲染")
        return False
    c = full_canvas(canvas)
    js = (f'load "{to_posix(pdb_path)}"; background white; select protein; '
          f'cartoon only; color structure;')
    args = [java, "-Xmx2g", "-jar", str(jar), "-n", "-x",
            f"-g{c['width']}x{c['height']}", "-J", js, "-w", f"PNG:{to_posix(png_path)}"]
    print(f"正在用 JmolData 渲染 {c['width']}x{c['height']}（纯软件渲染，无 GPU/OpenGL 依赖）...")
    env = dict(os.environ)
    env.setdefault("JAVA_TOOL_OPTIONS", "-Djava.awt.headless=true")
    r = subprocess.run(args, capture_output=True, text=True, timeout=300, env=env)
    if png_path.exists():
        print(f"[OK] 图像已生成: {png_path}")
        return True
    print("[!!] Jmol 渲染失败：", (r.stderr or r.stdout or "")[-400:])
    return False
