# -*- coding: utf-8 -*-
"""最小 RenderSpec（molvis.spec）单元测试。"""
from __future__ import annotations

import json

import pytest

from molvis.config import DEFAULT_CANVAS
from molvis.spec import RenderSpec, SpecError, load_spec


def test_default_description_and_canvas():
    s = RenderSpec(structure_source=r"data\1ubq.pdb", style="cartoon")
    s.validate()
    assert "1ubq.pdb" in s.description
    assert "cartoon" in s.description.lower()
    assert s.canvas["width"] == DEFAULT_CANVAS["width"]
    assert s.canvas["dpi"] == DEFAULT_CANVAS["dpi"]


def test_canvas_keeps_only_known_keys():
    s = RenderSpec(structure_source="x.pdb", style="cartoon",
                   canvas={"width": 800, "unknown_key": 1})
    assert s.canvas["width"] == 800
    assert "unknown_key" not in s.canvas
    assert s.canvas["height"] == DEFAULT_CANVAS["height"]


@pytest.mark.parametrize("kw", [
    {"structure_source": "", "style": "cartoon"},
    {"structure_source": "x.pdb", "style": "bogus"},
    {"structure_source": "x.pdb", "style": "cartoon", "structure_format": "xyz"},
    {"structure_source": "x.pdb", "style": "cartoon", "qa_level": 9},
])
def test_invalid_spec_raises(kw):
    with pytest.raises(SpecError):
        RenderSpec(**kw).validate()


def test_load_spec_from_json(tmp_path):
    f = tmp_path / "spec.json"
    f.write_text(json.dumps({
        "spec_version": "1.0",
        "structure": {"source": "data/1hsg.pdb", "format": "pdb"},
        "style": "ligand",
        "canvas": {"width": 800, "height": 600},
        "description": "配体口袋",
        "policy": {"qa_level": 2},
    }), encoding="utf-8")
    s = load_spec(f)
    s.validate()
    assert s.style == "ligand"
    assert s.qa_level == 2
    assert s.canvas["width"] == 800
    assert s.description == "配体口袋"


def test_spec_to_dict_roundtrip_shape():
    s = RenderSpec(structure_source="data/1ubq.pdb", style="sticks")
    s.validate()
    d = s.to_dict()
    assert d["structure"]["source"] == "data/1ubq.pdb"
    assert d["style"] == "sticks"
    assert d["policy"]["qa_level"] == 1
