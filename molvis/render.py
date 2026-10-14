# -*- coding: utf-8 -*-
"""单结构渲染：本地优先，缺失时从 RCSB 下载；按后缀分流 PDB / mmCIF；可选质量校验。"""
from __future__ import annotations

import pathlib
import time

from .config import DATA, OUTPUTS, full_canvas
from .engines.jmol import jmol_render
from .engines.py3dmol import make_html
from .engines.pymol import pymol_render
from .formats import (data_filename, detect_format, parse_input,
                      py3dmol_format, rcsb_download_url)
from .meta import JobMeta
from .qa import report, validate
from .spec import RenderSpec, load_spec
from .utils import section_title


def render_png(pdb_path, png_path, style: str = "cartoon", script_dir=None,
               allow_fallback: bool = True, canvas=None,
               engine: str = "pymol") -> tuple[bool, str]:
    """出 PNG，按 ``engine`` 选择渲染路径。

    ``pymol``（默认）：PyMOL 优先，失败回退 Jmol；
    ``jmol``：直接使用 Jmol（纯软件渲染）。
    ``both`` 由调用方分别调用两次（见 ``cmd_render``）。
    返回 ``(是否成功, 实际使用的引擎名)``；回退时的 Jmol 为卡通近似渲染。
    """
    if engine == "jmol":
        ok = jmol_render(pdb_path, png_path, canvas=canvas)
        return (True, "jmol") if ok else (False, "jmol")
    if pymol_render(pdb_path, png_path, style, script_dir=script_dir, canvas=canvas):
        return True, "pymol"
    if not allow_fallback:
        return False, "pymol"
    print("[--] PyMOL 出图失败，回退 Jmol（纯软件渲染，卡通近似）...")
    if jmol_render(pdb_path, png_path, canvas=canvas):
        return True, "jmol"
    return False, "none"


def _download(pid: str, fmt: str, target: pathlib.Path) -> bool:
    import urllib.request
    url = rcsb_download_url(pid, fmt)
    print(f"从 RCSB 下载 {pid}（格式 {fmt}）...")
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(urllib.request.urlopen(url, timeout=40).read())
        return True
    except Exception as e:
        print(f"[!!] 下载失败: {e}")
        return False


def resolve_structure(src) -> tuple[pathlib.Path, str]:
    """把输入解析为本地结构路径与格式：本地优先，缺失则从 RCSB 下载。

    失败抛 ``FileNotFoundError``。``render`` / ``ligand`` / ``api`` 共用。
    """
    p = pathlib.Path(src)
    if p.exists():
        return p, detect_format(p)
    pid, fmt = parse_input(src)
    target = DATA / data_filename(pid, fmt)
    if not target.exists() and not _download(pid, fmt, target):
        raise FileNotFoundError(f"无法获取结构: {src}")
    return target, fmt


def _canvas_from_args(spec, args) -> dict:
    """以 spec.canvas 为基础，用 CLI 显式给出的 --width/--height/--dpi 覆盖。"""
    canvas = dict(spec.canvas)
    for key in ("width", "height", "dpi"):
        val = getattr(args, key, None)
        if val is not None:
            canvas[key] = val
    return full_canvas(canvas)


def cmd_render(args) -> int:
    """渲染指定结构：解析输入（本地路径 / PDB ID，按后缀分流格式）→ 出图 → 质量校验 → meta.json。"""
    started = time.time()
    qa = getattr(args, "qa", 1)
    engine = getattr(args, "engine", "pymol")

    # 1) 载入可选的 RenderSpec（提供后以其中的结构 / 样式 / 期望为准）
    spec = None
    if getattr(args, "spec", None):
        try:
            spec = load_spec(args.spec)
            spec.validate()
        except Exception as e:
            print(f"[!!] RenderSpec 无效: {e}")
            return 1

    # 2) 确定并解析结构来源
    src = args.input or (spec.structure_source if spec else None)
    if not src:
        print("[!!] 需要 input 或 --spec 之一")
        return 1
    try:
        p, fmt = resolve_structure(src)
    except FileNotFoundError as e:
        print(f"[!!] {e}")
        return 1

    # 3) 未提供 spec 时按命令行参数合成
    if spec is None:
        spec = RenderSpec(structure_source=str(p), style=args.style,
                          structure_format=fmt, qa_level=qa)
    spec.canvas = _canvas_from_args(spec, args)
    spec.validate()
    style = spec.style
    canvas = spec.canvas
    qa = max(qa, spec.qa_level)

    outdir = pathlib.Path(args.out) if args.out else OUTPUTS / p.stem
    outdir.mkdir(parents=True, exist_ok=True)
    scripts = outdir / "scripts"
    section_title(f"渲染 {p.name}（格式: {fmt}，样式: {style}，引擎: {engine}，"
                  f"画布: {canvas['width']}x{canvas['height']} @{canvas['dpi']}dpi）")

    meta = JobMeta("render")
    meta.set_spec(spec)
    meta.add_input(p)
    meta.canvas = dict(canvas)

    artifacts: list[tuple[str, str, pathlib.Path, bool]] = []
    base_png = outdir / f"{p.stem}_{style}.png"
    if engine == "both":
        ok_p, _u = render_png(p, base_png, style, script_dir=scripts,
                              canvas=canvas, engine="pymol", allow_fallback=False)
        artifacts.append(("PNG (PyMOL)", "png", base_png, ok_p))
        jmol_png = outdir / f"{p.stem}_{style}_jmol.png"
        ok_j = jmol_render(p, jmol_png, canvas=canvas)
        artifacts.append(("PNG (Jmol)", "png", jmol_png, ok_j))
        used = "+".join(n for n, ok in (("pymol", ok_p), ("jmol", ok_j)) if ok) or "none"
    else:
        ok_p, used = render_png(p, base_png, style, script_dir=scripts,
                                canvas=canvas, engine=engine)
        artifacts.append(("PNG", "png", base_png, ok_p))
    meta.set_engine(engine, used)

    html_path = outdir / f"{p.stem}_{style}.html"
    ok_html = make_html(p, html_path, style, fmt=py3dmol_format(fmt), canvas=canvas)
    artifacts.append(("HTML", "html", html_path, ok_html))

    for _name, kind, path, ok in artifacts:
        if ok:
            meta.add_artifact(kind, path, outdir)

    print("\n产物目录:", outdir)
    failed = [name for name, _k, _p, ok in artifacts if not ok]
    if failed:
        print(f"[!!] 失败产物: {', '.join(failed)}")

    # 4) 质量校验（仅对成功产出的文件执行）
    if qa >= 1:
        qa_results = [validate(path, kind, spec, qa) for _n, kind, path, ok in artifacts if ok]
        qa_passed = report(qa_results, qa)
        meta.set_qa(qa, qa_results, qa_passed)
        if not qa_passed:
            failed.append("质量校验")
    else:
        print("\n== 质量校验：已跳过（qa_level=0）==")
        meta.set_qa(0, [], True)

    meta.set_failures(failed)
    meta.secs = time.time() - started
    print("元数据:", meta.write(outdir))

    if failed:
        return 1
    print(f"[OK] 全部产物生成成功（引擎: {engine}）")
    return 0
