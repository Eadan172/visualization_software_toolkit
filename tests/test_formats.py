# -*- coding: utf-8 -*-
"""格式识别与端点映射（molvis.formats）单元测试。"""
from __future__ import annotations

from molvis import formats as F


def test_detect_format_by_suffix(tmp_path):
    pdb = tmp_path / "a.pdb"
    pdb.write_text("ATOM      1  N   MET A   1", encoding="utf-8")
    cif = tmp_path / "a.cif"
    cif.write_text("data_x\nloop_\n_atom_site.id\n", encoding="utf-8")
    assert F.detect_format(pdb) == "pdb"
    assert F.detect_format(cif) == "cif"


def test_detect_format_content_sniff_for_unknown_suffix(tmp_path):
    f = tmp_path / "struct.txt"
    f.write_text("data_1ABC\n#\n_atom_site.id\n", encoding="utf-8")
    assert F.detect_format(f) == "cif"


def test_parse_input_id_and_suffix():
    assert F.parse_input("1hsg") == ("1HSG", "pdb")
    assert F.parse_input("1hsg.cif") == ("1HSG", "cif")
    assert F.parse_input("dir/1abc.pdb") == ("1ABC", "pdb")


def test_mapping_helpers():
    assert F.data_filename("1HSG", "cif") == "1hsg.cif"
    assert F.rcsb_download_url("1hsg", "cif").endswith("/1hsg.cif")
    assert F.rcsb_download_url("1hsg", "pdb").endswith("/1hsg.pdb")
    assert F.py3dmol_format("cif") == "cif"
    assert F.py3dmol_format("pdb") == "pdb"
    assert F.mvs_parse_format("cif") == "mmcif"
    assert F.mvs_parse_format("pdb") == "pdb"
