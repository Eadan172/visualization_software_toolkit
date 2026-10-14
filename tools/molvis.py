#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工具契约入口：渲染结构并输出结构化 JSON（供 Agent / 外部程序调用）。

直接运行：
    .venv\\Scripts\\python.exe tools\\molvis.py 1hsg --style ligand --engine pymol --out outputs\\job1
    .venv\\Scripts\\python.exe tools\\molvis.py data\\1ubq.pdb --qa 2 --width 800 --height 600

stdout 输出一段 JSON，键：
    job_id / status / ok / png / html / engine_used / secs / versions / sha256 /
    meta / artifacts / qa / failures

也可在代码中直接导入核心实现（推荐）：``from molvis.api import render_structure``。
"""
from __future__ import annotations

import contextlib
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:      # 允许以脚本方式直接运行
    sys.path.insert(0, str(ROOT))

from molvis.api import render_structure  # noqa: E402  (需在上面的 sys.path 处理之后导入)


def main(argv=None) -> int:
    import argparse
    import json

    ap = argparse.ArgumentParser(description="molvis 工具契约：渲染结构并输出 JSON")
    ap.add_argument("source", help="data 文件名 / PDB ID / 本地路径")
    ap.add_argument("--style", default="cartoon", choices=["cartoon", "surface", "sticks", "ligand"])
    ap.add_argument("--engine", default="pymol", choices=["pymol", "jmol"],
                    help="渲染引擎：pymol（默认，失败回退 Jmol）/ jmol")
    ap.add_argument("--out", default=None, help="输出目录（同时写入 meta.json）")
    ap.add_argument("--qa", type=int, default=1, choices=[0, 1, 2], help="质量校验级别")
    ap.add_argument("--width", type=int, default=None, help="图像宽度")
    ap.add_argument("--height", type=int, default=None, help="图像高度")
    ap.add_argument("--dpi", type=int, default=None, help="出图 DPI")
    args = ap.parse_args(argv)

    canvas = {k: v for k, v in (("width", args.width), ("height", args.height),
                                ("dpi", args.dpi)) if v is not None} or None
    # 渲染过程中的进度 / 日志一律导向 stderr，stdout 仅保留最终 JSON（便于机器消费）
    with contextlib.redirect_stdout(sys.stderr):
        result = render_structure(args.source, style=args.style, engine=args.engine,
                                  canvas=canvas, qa_level=args.qa, outdir=args.out, quiet=True)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
