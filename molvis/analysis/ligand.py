# -*- coding: utf-8 -*-
"""RDKit 配体 2D 结构图：从复合物结构抽取配体并绘制。"""
from __future__ import annotations

import pathlib
import tempfile


def depict_ligand(structure_path, out_path, resname: str | None = None,
                  size: tuple = (600, 450)) -> tuple[bool, dict]:
    """抽取配体并绘制 2D 结构图。

    ``resname`` 缺省时按「非蛋白且非水」选择配体。
    返回 ``(是否成功, 信息字典)``；失败时信息字典含 ``error``。
    """
    import MDAnalysis as mda
    from rdkit import Chem
    from rdkit.Chem import AllChem
    from rdkit.Chem.Draw import rdMolDraw2D

    u = mda.Universe(str(structure_path))
    sel = f"resname {resname}" if resname else "not protein and not water"
    atoms = u.select_atoms(sel)
    if atoms.n_atoms == 0:
        return False, {"error": f"未找到配体（选择式: {sel}）"}
    resnames = sorted(set(atoms.resnames))

    tmp = tempfile.NamedTemporaryFile(suffix=".pdb", delete=False)
    tmp.close()
    try:
        atoms.write(tmp.name)
        mol = Chem.MolFromPDBFile(tmp.name, sanitize=False, removeHs=True)
    finally:
        pathlib.Path(tmp.name).unlink(missing_ok=True)
    if mol is None:
        return False, {"error": "RDKit 无法解析配体结构"}

    AllChem.Compute2DCoords(mol)
    drawer = rdMolDraw2D.MolDraw2DCairo(*size)
    rdMolDraw2D.PrepareAndDrawMolecule(drawer, mol)
    drawer.FinishDrawing()
    pathlib.Path(out_path).write_bytes(drawer.GetDrawingText())
    return True, {"resname": ",".join(resnames), "atoms": atoms.n_atoms,
                  "bonds": mol.GetNumBonds()}
