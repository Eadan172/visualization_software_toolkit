# -*- coding: utf-8 -*-
"""轨迹与配体分析核心。

模块职责：
  traj.py     MDAnalysis 载入、RMSD / RMSF 指标、确定性关键帧选择
  plot.py     matplotlib（Agg）指标曲线绘制
  ligand.py   RDKit 配体 2D 结构图
  commands.py traj / ligand 子命令编排（复用 render_png 与 qa 校验）
"""
from __future__ import annotations

from .commands import cmd_ligand, cmd_traj

__all__ = ["cmd_traj", "cmd_ligand"]
