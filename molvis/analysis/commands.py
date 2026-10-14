# -*- coding: utf-8 -*-
"""analysis 子命令编排：traj（轨迹分析）/ ligand（配体 2D）。"""
from __future__ import annotations

import pathlib
import time

from ..config import OUTPUTS
from ..meta import JobMeta
from ..qa import report, validate
from ..render import render_png, resolve_structure
from ..spec import RenderSpec
from ..utils import section_title
from .ligand import depict_ligand
from .plot import plot_metric
from .traj import load_trajectory, rmsd_series, rmsf_series, select_keyframes


# 关键帧理由 -> 文件名安全后缀（理由可能由多条规则合并而来）
def _slug_for(reason: str) -> str:
    if "起始帧" in reason:
        return "start"
    if "结束帧" in reason:
        return "end"
    if "峰值" in reason:
        return "peak"
    return "median"


def cmd_traj(args) -> int:
    """轨迹分析：RMSD / RMSF 曲线 + 关键帧结构图（复用渲染与校验管线），并写 meta.json。"""
    started = time.time()
    qa = getattr(args, "qa", 1)
    topo = pathlib.Path(args.topology)
    traj = pathlib.Path(args.trajectory)
    for p, label in ((topo, "拓扑"), (traj, "轨迹")):
        if not p.exists():
            print(f"[!!] 找不到{label}文件: {p}")
            return 1
    stride = max(1, args.stride)
    outdir = pathlib.Path(args.out) if args.out else OUTPUTS / f"traj_{traj.stem}"
    figures = outdir / "figures"
    scripts = outdir / "scripts"
    figures.mkdir(parents=True, exist_ok=True)
    scripts.mkdir(parents=True, exist_ok=True)
    section_title(f"轨迹分析 {topo.name} + {traj.name}（stride={stride}）")

    u = load_trajectory(topo, traj)
    total_frames = len(u.trajectory)
    rmsd = rmsd_series(u, "backbone", stride)
    frames = [int(f) for f in rmsd[:, 0]]
    rmsd_vals = [float(v) for v in rmsd[:, 2]]
    rmsf = rmsf_series(u, "name CA", stride)
    rmsf_vals = [float(v) for v in rmsf]
    print(f"[OK] 载入 {u.atoms.n_atoms} 原子；原始 {total_frames} 帧，采样 {len(frames)} 帧")
    print(f"[OK] RMSD 范围 {min(rmsd_vals):.2f} ~ {max(rmsd_vals):.2f} Å；"
          f"RMSF（CA 逐残基）均值 {sum(rmsf_vals) / len(rmsf_vals):.2f} Å")

    keyframes = select_keyframes(frames, rmsd_vals)
    print("关键帧选取：")
    for fr, val, reason in keyframes:
        print(f"  - 帧 {fr:>4}   RMSD {val:.2f} Å   （{reason}）")

    spec = RenderSpec(structure_source=str(topo), style="cartoon", qa_level=qa)
    spec.validate()
    meta = JobMeta("traj")
    meta.set_spec(spec)
    meta.add_input(topo)
    meta.add_input(traj)
    meta.set_engine("mdanalysis", "mdanalysis")
    meta.extra["keyframes"] = [{"frame": f, "rmsd": round(r, 3), "reason": why}
                               for f, r, why in keyframes]
    meta.extra["metrics"] = {
        "rmsd_range": [round(min(rmsd_vals), 3), round(max(rmsd_vals), 3)],
        "rmsf_mean": round(sum(rmsf_vals) / len(rmsf_vals), 3),
        "atoms": int(u.atoms.n_atoms),
        "sampled_frames": len(frames),
        "total_frames": int(total_frames),
    }

    artifacts: list[tuple[str, str, pathlib.Path, bool, object]] = []

    curve = figures / "rmsd_curve.png"
    plot_metric(frames, rmsd_vals, curve, "Frame", "RMSD (Å)", "RMSD vs frame", keyframes)
    artifacts.append(("RMSD 曲线图", "png", curve, True, None))

    rmsf_curve = figures / "rmsf_curve.png"
    plot_metric(list(range(1, len(rmsf_vals) + 1)), rmsf_vals, rmsf_curve,
                "Residue", "RMSF (Å)", "RMSF per residue (CA)")
    artifacts.append(("RMSF 曲线图", "png", rmsf_curve, True, None))

    for fr, _val, reason in keyframes:
        u.trajectory[fr]
        frame_pdb = scripts / f"frame_{fr}.pdb"
        u.atoms.write(str(frame_pdb))
        frame_png = figures / f"frame_{fr}_{_slug_for(reason)}.png"
        ok, _engine = render_png(frame_pdb, frame_png, "cartoon", script_dir=scripts)
        artifacts.append((f"关键帧 {fr} 结构图", "png", frame_png, ok, spec))

    for _label, kind, path, ok, _sp in artifacts:
        if ok:
            meta.add_artifact(kind, path, outdir)

    failed = [label for label, _k, _p, ok, _sp in artifacts if not ok]
    if failed:
        print(f"[!!] 失败产物: {', '.join(failed)}")

    if qa >= 1:
        qa_results = [validate(path, kind, sp, qa) for _l, kind, path, ok, sp in artifacts if ok]
        qa_passed = report(qa_results, qa)
        meta.set_qa(qa, qa_results, qa_passed)
        if not qa_passed:
            failed.append("质量校验")
    else:
        print("\n== 质量校验：已跳过（qa_level=0）==")
        meta.set_qa(0, [], True)

    meta.set_failures(failed)
    meta.secs = time.time() - started
    print("\n产物目录:", outdir)
    print("元数据:", meta.write(outdir))
    if failed:
        return 1
    print(f"[OK] 轨迹分析完成：{len(artifacts)} 项产物（{len(keyframes)} 个关键帧）")
    return 0


def cmd_ligand(args) -> int:
    """配体 2D 结构图：抽取配体并用 RDKit 绘制，并写 meta.json。"""
    started = time.time()
    qa = getattr(args, "qa", 1)
    try:
        p, _fmt = resolve_structure(args.input)
    except FileNotFoundError as e:
        print(f"[!!] {e}")
        return 1
    outdir = pathlib.Path(args.out) if args.out else OUTPUTS / f"ligand_{p.stem}"
    figures = outdir / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    section_title(f"配体 2D 结构图 {p.name}")

    out_png = figures / f"{p.stem}_ligand2d.png"
    ok, info = depict_ligand(p, out_png, resname=args.resname)
    if not ok:
        print(f"[!!] 配体绘制失败: {info.get('error')}")
        return 1
    print(f"[OK] 配体 2D 图已生成: {out_png}")
    print(f"      残基 {info['resname']}，{info['atoms']} 原子 / {info['bonds']} 键")

    meta = JobMeta("ligand")
    meta.add_input(p)
    meta.set_engine("rdkit", "rdkit")
    meta.extra["ligand"] = {"resname": info["resname"], "atoms": info["atoms"],
                            "bonds": info["bonds"]}
    meta.add_artifact("png", out_png, outdir)

    failed: list[str] = []
    if qa >= 1:
        # 2D 图为化学结构式而非结构卡通，仅做文件级与图像统计校验（不带画布约束）
        qa_results = [validate(out_png, "png", None, qa)]
        qa_passed = report(qa_results, qa)
        meta.set_qa(qa, qa_results, qa_passed)
        if not qa_passed:
            failed.append("质量校验")
    else:
        print("\n== 质量校验：已跳过（qa_level=0）==")
        meta.set_qa(0, [], True)

    meta.set_failures(failed)
    meta.secs = time.time() - started
    print("\n产物目录:", outdir)
    print("元数据:", meta.write(outdir))
    return 1 if failed else 0
