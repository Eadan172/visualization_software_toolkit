# -*- coding: utf-8 -*-
"""matplotlib（Agg 后端）绘制轨迹指标曲线，并标注关键帧。"""
from __future__ import annotations


def _plt():
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    return plt


def plot_metric(x, y, out_path, xlabel: str, ylabel: str, title: str,
                keyframes=None, color: str = "#4a90c2") -> bool:
    """绘制单条指标曲线；``keyframes`` 为 ``[(x, y, reason)]`` 时在曲线上标注。"""
    plt = _plt()
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150)
    ax.plot(x, y, "-", color=color, lw=1.6)
    for kx, ky, reason in (keyframes or []):
        ax.scatter([kx], [ky], color="#e07b39", zorder=5)
        ax.annotate(reason, (kx, ky), textcoords="offset points", xytext=(6, 6),
                    fontsize=8, color="#a0522d")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    return True
