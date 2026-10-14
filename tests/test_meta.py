# -*- coding: utf-8 -*-
"""作业元数据（molvis.meta）单元测试。"""
from __future__ import annotations

import hashlib
import json

from molvis import __version__
from molvis.meta import META_NAME, JobMeta, runtime_versions, sha256_file


def test_sha256_matches_hashlib(tmp_path):
    f = tmp_path / "a.bin"
    f.write_bytes(b"hello world")
    assert sha256_file(f) == hashlib.sha256(b"hello world").hexdigest()


def test_job_meta_records_and_writes(tmp_path):
    inp = tmp_path / "in.pdb"
    inp.write_text("ATOM", encoding="utf-8")
    art = tmp_path / "figures" / "out.png"
    art.parent.mkdir()
    art.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 700)

    meta = JobMeta("render", job_id="20261014-000000")
    meta.set_engine("pymol", "pymol")
    meta.add_input(inp)
    meta.add_artifact("png", art, tmp_path)
    meta.set_qa(1, [], True)
    meta.set_failures([])
    meta.secs = 1.234
    path = meta.write(tmp_path)

    assert path.name == META_NAME
    d = json.loads(path.read_text(encoding="utf-8"))
    assert d["kind"] == "render"
    assert d["job_id"] == "20261014-000000"
    assert d["tool_version"] == __version__
    assert d["input"][0]["sha256"] == sha256_file(inp)
    assert d["artifacts"][0]["path"] == "figures/out.png"        # 相对作业目录
    assert d["artifacts"][0]["sha256"] == sha256_file(art)
    assert d["qa"]["passed"] is True
    assert d["secs"] == 1.234
    assert d["versions"]["molvis"] == __version__


def test_set_qa_defaults_to_all_pass_when_no_results():
    meta = JobMeta("x")
    meta.set_qa(1, [], None)
    assert meta.qa["passed"] is True


def test_runtime_versions_has_expected_keys():
    v = runtime_versions()
    for key in ("molvis", "pymol", "py3dmol", "molviewspec", "mdanalysis", "rdkit", "jmol"):
        assert key in v
