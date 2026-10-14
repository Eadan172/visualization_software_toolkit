# -*- coding: utf-8 -*-
"""一键演示：PyMOL / Jmol 出图 + py3Dmol 网页 + MolViewSpec 场景 + 质量校验 + meta.json。"""
from __future__ import annotations

import time

from .config import DATA, OUTPUTS
from .engines.jmol import jmol_render
from .engines.molviewspec import make_mvsj
from .engines.py3dmol import make_html
from .meta import JobMeta
from .qa import report, validate
from .render import render_png
from .spec import RenderSpec
from .utils import section_title


def _canvas_from_args(args) -> dict | None:
    """仅收集 CLI 显式给出的 --width/--height/--dpi（其余交给默认画布）。"""
    items = {k: getattr(args, k, None) for k in ("width", "height", "dpi")}
    items = {k: v for k, v in items.items() if v is not None}
    return items or None


def cmd_demo(args) -> int:
    """对示例结构跑一遍完整演示流水线，汇总产物与质量校验，并写出 meta.json。"""
    started = time.time()
    qa = getattr(args, "qa", 1)
    canvas = _canvas_from_args(args)
    outp = OUTPUTS / "demo"
    outp.mkdir(parents=True, exist_ok=True)
    scripts = outp / "scripts"
    pdb = DATA / "1ubq.pdb"
    if not pdb.exists():
        print("[!!] 缺少示例数据 data/1ubq.pdb")
        return 1

    meta = JobMeta("demo")
    meta.set_engine("multi", "pymol+jmol+py3dmol+molviewspec")
    meta.add_input(pdb)
    meta.canvas = canvas or {}

    results: list[tuple[str, bool]] = []            # 产物成功 / 失败
    produced: list[tuple[str, object, bool, RenderSpec]] = []   # (kind, path, ok, spec)

    section_title("一键演示：1UBQ 泛素")
    spec_ubq = RenderSpec(structure_source=str(pdb), style="cartoon", qa_level=qa, canvas=canvas)
    spec_ubq.validate()
    meta.set_spec(spec_ubq)
    p1 = outp / "1ubq_pymol.png"
    ok1, _e = render_png(pdb, p1, "cartoon", script_dir=scripts, canvas=canvas)
    results.append(("1ubq 主渲染图（PyMOL 优先，失败回退 Jmol）", ok1))
    produced.append(("png", p1, ok1, spec_ubq))
    p2 = outp / "1ubq_jmol.png"
    ok2 = jmol_render(pdb, p2, canvas=canvas)
    results.append(("1ubq Jmol 后备图", ok2))
    produced.append(("png", p2, ok2, spec_ubq))
    p3 = outp / "1ubq_interactive.html"
    ok3 = make_html(pdb, p3, "cartoon", canvas=canvas)
    results.append(("1ubq 交互网页", ok3))
    produced.append(("html", p3, ok3, spec_ubq))
    p4 = outp / "1ubq_molviewspec.mvsj"
    ok4 = make_mvsj(pdb, p4, "pdb")
    results.append(("1ubq MolViewSpec 场景", ok4))
    produced.append(("mvsj", p4, ok4, spec_ubq))

    lig = DATA / "1hsg.pdb"
    if lig.exists():
        meta.add_input(lig)
        section_title("附加示例：1HSG（HIV 蛋白酶 + 配体，ligand 视角）")
        spec_lig = RenderSpec(structure_source=str(lig), style="ligand", qa_level=qa, canvas=canvas)
        spec_lig.validate()
        p5 = outp / "1hsg_ligand_pymol.png"
        ok5, _e = render_png(lig, p5, "ligand", script_dir=scripts, canvas=canvas)
        results.append(("1hsg 配体口袋图", ok5))
        produced.append(("png", p5, ok5, spec_lig))
        p6 = outp / "1hsg_ligand.html"
        ok6 = make_html(lig, p6, "ligand", canvas=canvas)
        results.append(("1hsg 交互网页", ok6))
        produced.append(("html", p6, ok6, spec_lig))

    print("\n演示完成。产物均在:", outp)
    failed = [name for name, ok in results if not ok]

    for kind, path, ok, _spec in produced:
        if ok:
            meta.add_artifact(kind, path, outp)

    if qa >= 1:
        qa_results = [validate(path, kind, spec, qa) for kind, path, ok, spec in produced if ok]
        qa_passed = report(qa_results, qa)
        meta.set_qa(qa, qa_results, qa_passed)
        if not qa_passed:
            failed.append("质量校验")
    else:
        print("\n== 质量校验：已跳过（qa_level=0）==")
        meta.set_qa(0, [], True)

    meta.set_failures(failed)
    meta.secs = time.time() - started
    print("元数据:", meta.write(outp))

    if failed:
        print(f"[!!] 失败项 {len(failed)}: {', '.join(failed)}")
        return 1
    print(f"[OK] 全部 {len(results)} 项产物生成成功")
    return 0
