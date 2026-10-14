# -*- coding: utf-8 -*-
"""程序调用契约（供 Agent / 脚本使用）。

与 CLI 共用同一套引擎与校验管线，额外写出 ``meta.json`` 并返回结构化结果字典。
推荐直接导入：``from molvis.api import render_structure``；
命令行入口见 ``tools/molvis.py``。
"""
from __future__ import annotations

import pathlib
import time

from .config import OUTPUTS, full_canvas
from .engines.py3dmol import make_html
from .formats import py3dmol_format
from .meta import JobMeta
from .qa import report, validate
from .render import render_png, resolve_structure
from .spec import RenderSpec


def render_structure(source, style: str = "cartoon", engine: str = "pymol",
                     canvas=None, qa_level: int = 1, outdir=None,
                     spec: RenderSpec | None = None, quiet: bool = False) -> dict:
    """渲染一个结构：出 PNG（+HTML）、写 ``meta.json``，返回结构化结果。

    返回键：``job_id`` / ``status`` / ``ok`` / ``png`` / ``html`` / ``engine_used`` /
    ``secs`` / ``versions`` / ``sha256`` / ``meta`` / ``artifacts`` / ``qa`` / ``failures``。
    ``engine`` 取值 ``pymol``（默认，失败回退 Jmol）或 ``jmol``。
    """
    started = time.time()

    if spec is None:
        p, fmt = resolve_structure(source)
        spec = RenderSpec(structure_source=str(p), style=style, structure_format=fmt,
                          qa_level=qa_level)
    else:
        p, fmt = resolve_structure(spec.structure_source)
    spec.canvas = full_canvas(canvas or spec.canvas)
    spec.validate()

    out = pathlib.Path(outdir) if outdir else OUTPUTS / p.stem
    out.mkdir(parents=True, exist_ok=True)
    scripts = out / "scripts"

    meta = JobMeta("render")
    meta.set_spec(spec)
    meta.add_input(p)
    meta.canvas = dict(spec.canvas)

    png = out / f"{p.stem}_{spec.style}.png"
    html = out / f"{p.stem}_{spec.style}.html"
    ok_png, used = render_png(p, png, spec.style, script_dir=scripts,
                              canvas=spec.canvas, engine=engine)
    ok_html = make_html(p, html, spec.style, fmt=py3dmol_format(fmt), canvas=spec.canvas)
    meta.set_engine(engine, used)

    failures: list[str] = []
    for kind, path, ok in (("png", png, ok_png), ("html", html, ok_html)):
        if ok:
            meta.add_artifact(kind, path, out)
        else:
            failures.append(kind)

    if qa_level >= 1:
        qa_results = [validate(path, kind, spec, qa_level)
                      for kind, path, ok in (("png", png, ok_png), ("html", html, ok_html)) if ok]
        qa_passed = all(r.passed for r in qa_results)
        if not quiet:
            report(qa_results, qa_level)
        meta.set_qa(qa_level, qa_results, qa_passed)
        if not qa_passed:
            failures.append("qa")
    else:
        meta.set_qa(0, [], True)

    meta.set_failures(failures)
    meta.secs = time.time() - started
    meta_path = meta.write(out)

    png_rec = next((a for a in meta.artifacts if a["kind"] == "png"), None)
    return {
        "job_id": meta.job_id,
        "status": "done" if not failures else "failed",
        "ok": not failures,
        "png": str(png) if ok_png else None,
        "html": str(html) if ok_html else None,
        "engine_used": used,
        "secs": round(meta.secs, 3),
        "versions": meta.to_dict()["versions"],
        "sha256": png_rec["sha256"] if png_rec else None,
        "meta": str(meta_path),
        "artifacts": meta.artifacts,
        "qa": meta.qa,
        "failures": failures,
    }
