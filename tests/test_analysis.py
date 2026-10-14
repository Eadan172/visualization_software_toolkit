# -*- coding: utf-8 -*-
"""分析层单元测试：关键帧规则（molvis.analysis.traj）与配体 2D（ligand）。"""
from __future__ import annotations

import pytest

from molvis.config import ROOT
from molvis.analysis.traj import select_keyframes
from molvis.analysis.ligand import depict_ligand


def test_select_keyframes_marks_start_peak_end():
    frames = list(range(10))
    rmsd = [0, 1, 2, 3, 4, 5, 4, 3, 2, 1]
    kf = select_keyframes(frames, rmsd)
    idx = {f for f, _v, _r in kf}
    assert {0, 5, 9} <= idx
    reasons = {f: r for f, _v, r in kf}
    assert "起始帧" in reasons[0]
    assert "峰值" in reasons[5]
    assert "结束帧" in reasons[9]


def test_select_keyframes_merges_reason_on_same_frame():
    # 末帧即为峰值 -> 理由应合并
    frames = list(range(5))
    rmsd = [0, 1, 2, 3, 9]
    kf = select_keyframes(frames, rmsd)
    reasons = {f: r for f, _v, r in kf}
    assert "结束帧" in reasons[4] and "峰值" in reasons[4]


def test_select_keyframes_empty():
    assert select_keyframes([], []) == []


@pytest.mark.skipif(not (ROOT / "data" / "1hsg.pdb").exists(),
                    reason="需要示例数据 data/1hsg.pdb")
def test_depict_ligand_from_complex(tmp_path):
    out = tmp_path / "lig.png"
    ok, info = depict_ligand(ROOT / "data" / "1hsg.pdb", out)
    assert ok, info
    assert out.exists() and out.stat().st_size > 512
    assert info["atoms"] > 0
