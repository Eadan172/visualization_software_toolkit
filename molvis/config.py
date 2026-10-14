# -*- coding: utf-8 -*-
"""全局路径与常量配置。

所有硬编码的路径派生、默认画布、样式表与 PyMOL 脚本模板集中于此，
其它模块一律从这里引用，避免散落各处。
"""
from __future__ import annotations

import pathlib

# 项目根目录：molvis/config.py -> parents[1]
ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUTPUTS = ROOT / "outputs"
SOFTWARE = ROOT / "software"
VENV_PY = ROOT / ".venv" / "Scripts" / "python.exe"
PYMOL_EXE = ROOT / ".venv" / "Scripts" / "pymol.exe"

# 默认画布：静态图（PyMOL / Jmol）与网页（py3Dmol）共用。
# 可经 CLI 的 --width/--height/--dpi 或 RenderSpec 的 canvas 字段覆盖。
DEFAULT_CANVAS = {"width": 1600, "height": 1200, "dpi": 150, "background": "white"}

# 自检所覆盖的核心依赖（dist 名, 展示名）
PKGS = [
    ("numpy", "NumPy"),
    ("pymol", "PyMOL 开源版"),
    ("MDAnalysis", "MDAnalysis"),
    ("mdtraj", "MDTraj"),
    ("rdkit", "RDKit"),
    ("py3Dmol", "py3Dmol"),
    ("molviewspec", "MolViewSpec"),
    ("matplotlib", "Matplotlib"),
    ("Pillow", "Pillow"),
]

# 预设样式：setup 为场景设置，frame 为取景/相机
STYLES = {
    "cartoon": {
        "setup": 'cmd.show("cartoon","polymer"); '
                 'cmd.color("skyblue","ss h"); cmd.color("salmon","ss s"); cmd.color("gray70","ss l+\'\'")',
        "frame": 'cmd.orient()',
    },
    "surface": {
        "setup": 'cmd.show("cartoon","polymer"); cmd.show("surface","polymer"); cmd.set("transparency", 0.4)',
        "frame": 'cmd.orient()',
    },
    "sticks": {
        "setup": 'cmd.show("sticks","all")',
        "frame": 'cmd.orient()',
    },
    "ligand": {
        "setup": 'cmd.show("cartoon","polymer"); cmd.set("cartoon_transparency", 0.7); '
                 'cmd.show("sticks","organic"); cmd.color("gray80","polymer"); cmd.color("orange","organic")',
        "frame": 'cmd.zoom("organic", 5) if cmd.count_atoms("organic") else cmd.orient()',
    },
}

# PyMOL 渲染脚本模板（交由 pymol.exe -cq 执行）；画布尺寸由 {width}/{height}/{dpi} 注入
PYMOL_TEMPLATE = '''from pymol import cmd
cmd.load(r"{pdb}", "mol")
cmd.hide("everything")
{setup}
{frame}
cmd.set("ray_opaque_background", 1)
cmd.bg_color("white")
cmd.ray({width}, {height})
cmd.png(r"{png}", dpi={dpi})
print("PYMOL_RENDER_DONE")
cmd.quit()
'''


def full_canvas(canvas: dict | None = None) -> dict:
    """把给定画布与默认值合并为完整参数（width / height / dpi / background）。"""
    return {**DEFAULT_CANVAS, **(canvas or {})}
