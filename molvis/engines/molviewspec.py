# -*- coding: utf-8 -*-
"""MolViewSpec 引擎适配：生成声明式场景 .mvsj（可被 Mol* 等查看器渲染）。"""
from __future__ import annotations

import pathlib


def make_mvsj(structure_path, out_path, fmt: str = "pdb") -> bool:
    """从**本地结构文件**生成 MolViewSpec 场景。

    使用 file:// URI 引用本地文件，生成过程不再需要联网（原先写死 RCSB URL）。
    """
    try:
        import molviewspec as mvs
        uri = pathlib.Path(structure_path).resolve().as_uri()
        parse_fmt = "mmcif" if fmt == "cif" else "pdb"
        b = mvs.create_builder()
        (b.download(url=uri).parse(format=parse_fmt).model_structure()
          .component(selector="polymer").representation(type="cartoon"))
        state = b.get_state()
        text = state.dumps() if hasattr(state, "dumps") else state.model_dump_json()
        import json as _json
        _json.loads(text)
        pathlib.Path(out_path).write_text(text, encoding="utf-8")
        print(f"[OK] MolViewSpec 场景已生成: {out_path}")
        print(f"      来源（本地，离线）: {uri}")
        return True
    except Exception as e:
        print(f"[--] MolViewSpec 生成跳过: {type(e).__name__}: {str(e)[:120]}")
        return False
