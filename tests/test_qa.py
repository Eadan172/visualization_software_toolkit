# -*- coding: utf-8 -*-
"""校验层（molvis.qa）单元测试：L0 文件判定、L1 图像统计、分级编排。"""
from __future__ import annotations

from molvis.qa import validate
from molvis.qa.checks import check_l0, check_l1_png


def test_l0_png_magic_ok_and_fail(make_png, tmp_path):
    good = make_png("good.png")
    assert check_l0(good, "png") == []
    bad = tmp_path / "bad.png"
    bad.write_bytes(b"not a png at all" * 60)
    assert check_l0(bad, "png")


def test_l0_missing_file(tmp_path):
    assert check_l0(tmp_path / "nope.png", "png")


def test_l0_html_and_mvsj(make_html, make_mvsj):
    assert check_l0(make_html("ok.html", full=True), "html") == []
    assert check_l0(make_html("frag.html", full=False), "html")
    assert check_l0(make_mvsj("ok.mvsj", valid=True), "mvsj") == []
    assert check_l0(make_mvsj("bad.mvsj", valid=False), "mvsj")


def test_l1_detects_blank_image(make_png):
    blank = make_png("blank.png")
    issues, details = check_l1_png(blank)
    assert any("空白" in i for i in issues)
    assert details["foreground_ratio"] < 0.005


def test_l1_passes_with_foreground(make_png):
    fg = make_png("fg.png", blob=(200, 40, 40))
    issues, details = check_l1_png(fg)
    assert issues == []
    assert details["foreground_ratio"] > 0.005
    assert details["size"] == [200, 150]


def test_l1_canvas_mismatch(make_png):
    fg = make_png("m.png", blob=(0, 0, 0))
    issues, _ = check_l1_png(fg, {"width": 800, "height": 600})
    assert any("尺寸不符" in i for i in issues)


def test_validate_levels(make_png, monkeypatch):
    fg = make_png("a.png", blob=(200, 40, 40))

    r0 = validate(fg, "png", None, 0)
    assert r0.passed and r0.l2["status"] == "not_run"

    r1 = validate(fg, "png", None, 1)
    assert r1.passed
    assert r1.details["l1"]["foreground_ratio"] > 0

    for var in ("MOLVIS_VISION_BASE_URL", "MOLVIS_VISION_API_KEY", "MOLVIS_VISION_MODEL"):
        monkeypatch.delenv(var, raising=False)
    r2 = validate(fg, "png", None, 2)
    assert r2.passed and r2.l2["status"] == "skipped"


def test_validate_corrupt_png_fails(tmp_path):
    bad = tmp_path / "bad.png"
    bad.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 600)
    r = validate(bad, "png", None, 1)
    assert not r.passed
