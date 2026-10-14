# -*- coding: utf-8 -*-
"""结构文件格式识别与各下游端点映射。

职责：把「输入形态」统一成规范化格式名（`pdb` / `cif`），
并提供 RCSB 下载、py3Dmol、MolViewSpec 与本地缓存命名所需的标识，
消除原先「声明支持 .cif 实际按 PDB 处理」的名实不符问题。
"""
from __future__ import annotations

import pathlib

# 规范化格式名
PDB = "pdb"
CIF = "cif"

# 文件后缀 -> 规范化格式名
_SUFFIX_FORMATS = {
    ".pdb": PDB,
    ".ent": PDB,
    ".cif": CIF,
    ".mmcif": CIF,
}

# 规范化格式名 -> 文件扩展名（RCSB 端点与本地缓存共用）
_EXT = {PDB: "pdb", CIF: "cif"}


def detect_format(path) -> str:
    """识别本地结构文件格式，返回 'pdb' 或 'cif'。

    优先按后缀判断；后缀未知时按内容嗅探（mmCIF 以 data_ 开头并含 _atom_site）。
    """
    p = pathlib.Path(path)
    fmt = _SUFFIX_FORMATS.get(p.suffix.lower())
    if fmt:
        return fmt
    try:
        head = p.read_text(encoding="utf-8", errors="replace")[:4096]
    except Exception:
        return PDB
    if head.lstrip().startswith("data_") or "_atom_site." in head:
        return CIF
    return PDB


def parse_input(src: str) -> tuple[str, str]:
    """从命令行输入推断 (pdb_id, 格式)。

    输入可为 '1hsg' / '1hsg.cif' / '1abc.pdb'（含目录亦可）。
    未带后缀时默认按 PDB 处理。
    """
    name = pathlib.Path(str(src).strip()).name
    suffix = pathlib.Path(name).suffix.lower()
    fmt = _SUFFIX_FORMATS.get(suffix, PDB)
    pid = (name[: -len(suffix)] if suffix else name).upper()
    return pid, fmt


def data_filename(pdb_id: str, fmt: str) -> str:
    """data/ 目录下的本地缓存文件名。"""
    return f"{pdb_id.strip().lower()}.{_EXT.get(fmt, 'pdb')}"


def rcsb_download_url(pdb_id: str, fmt: str) -> str:
    """RCSB 对应格式的下载地址。"""
    return f"https://files.rcsb.org/download/{pdb_id.strip().lower()}.{_EXT.get(fmt, 'pdb')}"


def py3dmol_format(fmt: str) -> str:
    """py3Dmol / 3Dmol.js 的 addModel 格式标识（'pdb' / 'cif'）。"""
    return CIF if fmt == CIF else PDB


def mvs_parse_format(fmt: str) -> str:
    """MolViewSpec parse 节点的格式标识（'pdb' / 'mmcif'）。"""
    return "mmcif" if fmt == CIF else "pdb"
