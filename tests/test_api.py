# -*- coding: utf-8 -*-
"""程序调用契约（molvis.api.render_structure）单元测试。

通过替换渲染/网页函数为轻量假实现，使契约与 meta.json 写入可在不触发真实渲染、
不联网的前提下被验证。
"""
from __future__ import annotations

import json
import pathlib

from PIL import Image
import pytest

import molvis.api as api

EXPECTED_KEYS = {"job_id", "status", "ok", "png", "html", "engine_used", "secs",
                 "versions", "sha256", "meta", "artifacts", "qa", "failures"}


def _fake_render_png(pdb, png, *a, **k):
    """生成带前景色块的合法 PNG（200×150，补足到 512 B 以上），以满足 L0/L1 校验。"""
    from PIL import Image, PngImagePlugin
    pathlib.Path(png).parent.mkdir(parents=True, exist_ok=True)
    im = Image.new("RGB", (200, 150), (255, 255, 255))
    for x in range(50, 100):
        for y in range(37, 75):
            im.putpixel((x, y), (200, 40, 40))
    info = PngImagePlugin.PngInfo()
    info.add_text("pad", "x" * 700)
    im.save(png, pnginfo=info)
    return True, "pymol"


def _fake_make_html(pdb, html, *a, **k):
    pathlib.Path(html).write_text(
        "<!DOCTYPE html><html><body>3dmol</body></html><!--" + "x" * 600 + "-->",
        encoding="utf-8")
    return True


@pytest.fixture
def patched(monkeypatch):
    monkeypatch.setattr(api, "render_png", _fake_render_png)
    monkeypatch.setattr(api, "make_html", _fake_make_html)
    return api


def _make_structure(tmp_path):
    src = tmp_path / "1ubq.pdb"
    src.write_text("ATOM      1  N   MET A   1\n" * 20, encoding="utf-8")
    return src


def test_contract_shape_and_meta_written(tmp_path, patched):
    src = _make_structure(tmp_path)
    out = tmp_path / "job"
    res = patched.render_structure(str(src), outdir=str(out), qa_level=0, quiet=True)

    assert EXPECTED_KEYS <= set(res)
    assert res["ok"] is True and res["status"] == "done"
    assert res["engine_used"] == "pymol"
    assert res["sha256"] and len(res["sha256"]) == 64
    assert res["png"] and res["html"]
    assert res["failures"] == []

    meta_path = pathlib.Path(res["meta"])
    assert meta_path.exists() and meta_path.name == "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    assert meta["kind"] == "render"
    assert meta["spec"]["style"] == "cartoon"
    assert meta["input"][0]["sha256"]
    assert {a["kind"] for a in meta["artifacts"]} == {"png", "html"}


def test_qa_level_1_records_and_passes(tmp_path, patched):
    src = _make_structure(tmp_path)
    res = patched.render_structure(str(src), outdir=str(tmp_path / "job2"),
                                   qa_level=1, canvas={"width": 200, "height": 150}, quiet=True)
    assert res["ok"] is True
    assert res["qa"]["level"] == 1
    assert res["qa"]["passed"] is True
    assert {r["kind"] for r in res["qa"]["results"]} == {"png", "html"}
