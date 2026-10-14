# -*- coding: utf-8 -*-
"""py3Dmol 引擎适配：生成自包含的可交互 HTML 网页。"""
from __future__ import annotations

import pathlib

from ..config import full_canvas


def make_html(pdb_path, html_path, style: str = "cartoon", fmt: str = "pdb",
              canvas: dict | None = None) -> bool:
    """生成可直接在浏览器中旋转 / 缩放的 HTML 交互页面。

    fmt 为 3Dmol.js 的 addModel 格式标识（'pdb' / 'cif'）；canvas 控制视图尺寸。
    """
    try:
        import py3Dmol
    except Exception as e:
        print(f"[!!] py3Dmol 不可用: {e}")
        return False
    c = full_canvas(canvas)
    v = py3Dmol.view(width=c["width"], height=c["height"])
    v.addModel(pathlib.Path(pdb_path).read_text(encoding="utf-8", errors="replace"), fmt)
    if style == "ligand":
        v.setStyle({}, {"cartoon": {"color": "lightgrey", "opacity": 0.6}})
        v.addStyle({"hetflag": True}, {"stick": {"colorscheme": "orangeCarbon", "radius": 0.15}})
        v.zoomTo({"hetflag": True})
    elif style == "surface":
        v.setStyle({"cartoon": {"color": "spectrum"}})
        v.addSurface(py3Dmol.VDW, {"opacity": 0.6, "color": "white"})
        v.zoomTo()
    elif style == "sticks":
        v.setStyle({"stick": {}, "sphere": {"scale": 0.25}})
        v.zoomTo()
    else:
        v.setStyle({"cartoon": {"color": "spectrum"}})
        v.zoomTo()
    v.setBackgroundColor("white")
    # py3Dmol 的 _make_html() 只返回 <div> 片段（供 Notebook 内嵌），
    # 这里补全为可独立打开的完整 HTML 文档（含 DOCTYPE 与 UTF-8 声明）。
    fragment = v._make_html()
    doc = (
        "<!DOCTYPE html>\n"
        '<html lang="zh">\n<head>\n<meta charset="utf-8">\n'
        "<title>molvis · 交互式结构视图</title>\n</head>\n"
        '<body style="margin: 0; padding: 0;">\n'
        f"{fragment}\n"
        "</body>\n</html>\n"
    )
    pathlib.Path(html_path).write_text(doc, encoding="utf-8")
    print(f"[OK] 交互网页已生成: {html_path}  （浏览器打开可旋转/缩放）")
    return True
