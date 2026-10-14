# -*- coding: utf-8 -*-
"""CLI 参数解析与失败返回码测试（不触发真实渲染、不联网）。"""
from __future__ import annotations

import argparse
import json

import pytest

from molvis import cli
from molvis.render import cmd_render, resolve_structure


def _render_args(**kw):
    base = dict(input=None, spec=None, style="cartoon", out=None, engine="pymol",
                width=None, height=None, dpi=None, qa=1)
    base.update(kw)
    return argparse.Namespace(**base)


def test_parser_subcommands_and_new_flags():
    ap = cli.build_parser()
    argmap = {"render": ["1ubq"], "ligand": ["1hsg"], "traj": ["data/1ubq.pdb", "data/1ubq_traj.dcd"]}
    for cmd in ("check", "demo", "render", "traj", "ligand"):
        ns = ap.parse_args([cmd] + argmap.get(cmd, []))
        assert ns.cmd == cmd
    a = ap.parse_args(["render", "1ubq", "--width", "800", "--height", "600",
                       "--dpi", "96", "--engine", "jmol"])
    assert (a.width, a.height, a.dpi, a.engine) == (800, 600, 96, "jmol")


def test_default_no_subcommand_prints_help(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["main.py"])
    code = cli.main()
    out = capsys.readouterr().out
    assert code == 0
    assert "usage" in out.lower()


def test_render_requires_input_or_spec():
    assert cmd_render(_render_args()) == 1


def test_render_invalid_spec_returns_error(tmp_path):
    bad = tmp_path / "s.json"
    bad.write_text(json.dumps({"structure": {"source": "x.pdb"}, "style": "bogus"}),
                   encoding="utf-8")
    assert cmd_render(_render_args(spec=str(bad))) == 1


def test_resolve_structure_local(tmp_path):
    f = tmp_path / "x.pdb"
    f.write_text("ATOM", encoding="utf-8")
    p, fmt = resolve_structure(str(f))
    assert p == f and fmt == "pdb"


def test_resolve_structure_missing_raises_without_network(monkeypatch):
    # 阻断下载，确保不联网且抛出 FileNotFoundError
    monkeypatch.setattr("molvis.render._download", lambda *a, **k: False)
    with pytest.raises(FileNotFoundError):
        resolve_structure("9ZZZ")
