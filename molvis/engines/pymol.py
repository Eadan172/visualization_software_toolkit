# -*- coding: utf-8 -*-
"""PyMOL 引擎适配：CPU 光线追踪输出 PNG（主力出图路径）。"""
from __future__ import annotations

import pathlib
import subprocess
import time

from ..config import PYMOL_EXE, PYMOL_TEMPLATE, STYLES, full_canvas
from ..utils import to_posix


def pymol_render(pdb_path, png_path, style: str = "cartoon", script_dir=None,
                 canvas: dict | None = None) -> bool:
    """用 PyMOL 渲染一张 PNG。

    script_dir 指定生成的 .py 脚本存放目录（默认与 PNG 同级）；
    canvas 为 ``{width, height, dpi}``，缺省用全局默认画布。
    """
    c = full_canvas(canvas)
    png_path = pathlib.Path(png_path)
    cfg = STYLES.get(style, STYLES["cartoon"])
    script = PYMOL_TEMPLATE.format(pdb=to_posix(pdb_path), png=to_posix(png_path),
                                   setup=cfg["setup"], frame=cfg["frame"],
                                   width=c["width"], height=c["height"], dpi=c["dpi"])
    sdir = pathlib.Path(script_dir) if script_dir else png_path.parent
    sdir.mkdir(parents=True, exist_ok=True)
    sp = sdir / f"{png_path.stem}.py"
    sp.write_text(script, encoding="utf-8")
    if not PYMOL_EXE.exists():
        print("[--] 未找到 PyMOL 可执行文件，跳过图像渲染")
        return False
    print(f"正在用 PyMOL 渲染 [{style}] {c['width']}x{c['height']}（CPU 光线追踪，通常 5~60 秒）...")
    t0 = time.time()
    r = subprocess.run([str(PYMOL_EXE), "-cq", str(sp)],
                       capture_output=True, text=True, timeout=900)
    if png_path.exists():
        print(f"[OK] 图像已生成: {png_path}  （{time.time() - t0:.1f}s）")
        return True
    print("[!!] PyMOL 渲染失败，末行输出：")
    print((r.stdout or "")[-600:])
    print((r.stderr or "")[-600:])
    return False
