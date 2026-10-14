# -*- coding: utf-8 -*-
"""轨迹分析核心：MDAnalysis 载入、RMSD / RMSF 指标、确定性关键帧选择。"""
from __future__ import annotations


def load_trajectory(topology, trajectory):
    """载入 ``MDAnalysis.Universe``（拓扑 + 轨迹）。"""
    import MDAnalysis as mda
    return mda.Universe(str(topology), str(trajectory))


def rmsd_series(u, select: str = "backbone", stride: int = 1, ref_frame: int = 0):
    """对参考帧计算 RMSD 序列。

    返回 ndarray，列 = ``[frame, time, rmsd]``。
    """
    from MDAnalysis.analysis import rms
    return rms.RMSD(u, u, select=select, ref_frame=ref_frame).run(
        step=stride, verbose=False).results.rmsd


def rmsf_series(u, select: str = "name CA", stride: int = 1):
    """计算逐原子 RMSF 序列（``name CA`` 时即为逐残基涨落）。"""
    from MDAnalysis.analysis import rms
    return rms.RMSF(u.select_atoms(select)).run(step=stride, verbose=False).results.rmsf


def select_keyframes(frames, rmsd, max_frames: int = 4):
    """确定性关键帧选择，不使用学习模型。

    规则：首帧、末帧、RMSD 峰值帧；帧数足够时追加「中位数平台代表帧」。
    同一帧命中多条规则时理由合并。返回 ``[(frame, rmsd_value, reason)]``（帧序升序）。
    """
    import numpy as np
    from collections import defaultdict
    n = len(frames)
    if n == 0:
        return []
    reasons: dict = defaultdict(list)
    reasons[0].append("起始帧")
    reasons[n - 1].append("结束帧")
    reasons[int(np.argmax(rmsd))].append("RMSD 峰值")
    if max_frames >= 4 and n >= 4:
        vals = np.asarray(rmsd, dtype=float)
        med = float(np.median(vals))
        reasons[int(np.argmin(np.abs(vals - med)))].append("平台代表帧（接近 RMSD 中位数）")
    return [(int(frames[i]), float(rmsd[i]), "；".join(reasons[i])) for i in sorted(reasons)]
