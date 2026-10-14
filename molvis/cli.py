# -*- coding: utf-8 -*-
"""命令行入口：解析参数并分发到 check / demo / render / traj / ligand。"""
from __future__ import annotations

import argparse

from .analysis import cmd_ligand, cmd_traj
from .check import cmd_check
from .config import STYLES
from .demo import cmd_demo
from .render import cmd_render

_QA_HELP = "质量校验级别：0 关闭 / 1 L0+L1 / 2 L0+L1+L2（L2 需配置视觉后端）"


def _add_canvas_args(p: argparse.ArgumentParser) -> None:
    """为子命令添加画布参数（缺省用全局默认画布）。"""
    p.add_argument("--width", type=int, default=None, help="图像宽度（默认 1600）")
    p.add_argument("--height", type=int, default=None, help="图像高度（默认 1200）")
    p.add_argument("--dpi", type=int, default=None, help="出图 DPI（默认 150）")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="分子可视化工具包入口（无子命令时显示本帮助）")
    sub = ap.add_subparsers(dest="cmd")

    sub.add_parser("check", help="环境自检")

    dp = sub.add_parser("demo", help="一键演示")
    _add_canvas_args(dp)
    dp.add_argument("--qa", type=int, default=1, choices=[0, 1, 2], help=_QA_HELP)

    rp = sub.add_parser("render", help="渲染结构")
    rp.add_argument("input", nargs="?", help="data 下的文件名 / PDB ID / .pdb/.cif 路径（使用 --spec 时可省略）")
    rp.add_argument("--style", default="cartoon", choices=list(STYLES.keys()))
    rp.add_argument("--out", default=None, help="输出目录")
    rp.add_argument("--spec", default=None, help="RenderSpec JSON 路径（提供后以其中的结构/样式/期望为准）")
    rp.add_argument("--engine", default="pymol", choices=["pymol", "jmol", "both"],
                    help="渲染引擎：pymol（默认，失败回退 Jmol）/ jmol / both")
    _add_canvas_args(rp)
    rp.add_argument("--qa", type=int, default=1, choices=[0, 1, 2], help=_QA_HELP)

    tp = sub.add_parser("traj", help="轨迹分析：RMSD / RMSF 曲线 + 关键帧结构图")
    tp.add_argument("topology", help="拓扑文件（如 data/1ubq.pdb）")
    tp.add_argument("trajectory", help="轨迹文件（如 data/1ubq_traj.dcd）")
    tp.add_argument("--stride", type=int, default=1, help="抽帧步长（默认 1）")
    tp.add_argument("--out", default=None, help="输出目录")
    tp.add_argument("--qa", type=int, default=1, choices=[0, 1, 2], help=_QA_HELP)

    lp = sub.add_parser("ligand", help="RDKit 配体 2D 结构图")
    lp.add_argument("input", help="结构文件 / data 文件名 / PDB ID")
    lp.add_argument("--resname", default=None, help="指定配体残基名（缺省取非蛋白非水）")
    lp.add_argument("--out", default=None, help="输出目录")
    lp.add_argument("--qa", type=int, default=1, choices=[0, 1, 2], help=_QA_HELP)
    return ap


def main() -> int:
    """无子命令时打印帮助（不再自动运行 demo），各子命令返回其退出码。"""
    ap = build_parser()
    args = ap.parse_args()
    if args.cmd == "check":
        return cmd_check(args)
    if args.cmd == "demo":
        return cmd_demo(args)
    if args.cmd == "render":
        return cmd_render(args)
    if args.cmd == "traj":
        return cmd_traj(args)
    if args.cmd == "ligand":
        return cmd_ligand(args)
    ap.print_help()
    return 0
