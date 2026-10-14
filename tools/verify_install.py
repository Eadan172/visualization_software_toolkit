# -*- coding: utf-8 -*-
"""安装验收辅助脚本：汇总环境、依赖版本、功能冒烟测试与文件清单。

运行：.venv\\Scripts\\python.exe tools\\verify_install.py
"""
import pathlib
import sys
import importlib.metadata as md

ROOT = pathlib.Path(__file__).resolve().parents[1]


def png_ok(p: pathlib.Path) -> bool:
    try:
        with open(p, "rb") as f:
            return f.read(8) == b"\x89PNG\r\n\x1a\n"
    except Exception:
        return False


print("== Python ==")
print(sys.version)
print("exec:", sys.executable)

print("== 包版本 ==")
for dist in ["numpy", "pymol", "MDAnalysis", "mdtraj", "rdkit",
             "py3Dmol", "molviewspec", "matplotlib", "Pillow"]:
    try:
        print(f"{dist} == {md.version(dist)}")
    except Exception:
        print(f"{dist} == MISSING")

print("== 功能冒烟 ==")
try:
    from pymol import cmd
    cmd.fragment("ala")
    print("pymol import OK, atoms =", cmd.count_atoms("all"))
except Exception as e:
    print("pymol import FAIL:", type(e).__name__, str(e)[:160])

try:
    import MDAnalysis as mda
    u = mda.Universe(str(ROOT / "data" / "1ubq.pdb"))
    print("MDAnalysis OK, atoms =", u.atoms.n_atoms, "frames =", len(u.trajectory))
except Exception as e:
    print("MDAnalysis FAIL:", type(e).__name__, str(e)[:160])

try:
    import mdtraj as t
    traj = t.load(str(ROOT / "data" / "1ubq.pdb"))
    print("mdtraj OK, atoms =", traj.n_atoms)
except Exception as e:
    print("mdtraj FAIL:", type(e).__name__, str(e)[:160])

try:
    from rdkit import Chem
    m = Chem.MolFromSmiles("CCO")
    print("rdkit OK, ethanol atoms =", m.GetNumAtoms())
except Exception as e:
    print("rdkit FAIL:", type(e).__name__, str(e)[:160])

try:
    import py3Dmol  # noqa: F401
    print("py3Dmol OK")
except Exception as e:
    print("py3Dmol FAIL:", type(e).__name__, str(e)[:160])

try:
    import molviewspec  # noqa: F401
    print("molviewspec OK")
except Exception as e:
    print("molviewspec FAIL:", type(e).__name__, str(e)[:160])

print("== 文件清单 ==")
for rel in ["main.py", "molvis/cli.py", "molvis/config.py", "molvis/meta.py", "molvis/api.py",
            "molvis/engines/pymol.py", "molvis/engines/jmol.py",
            "tools/molvis.py", "启动.bat", "requirements.txt",
            ".venv/Scripts/python.exe",
            "software/Jmol/jmol-16.3.51/JmolData.jar",
            "data/1ubq.pdb", "data/1hsg.pdb",
            "docs/分子模拟可视化软件_检索与安装方案.md"]:
    p = ROOT / rel
    if p.exists():
        print(f"OK   {rel} ({p.stat().st_size} bytes)")
    else:
        print(f"MISS {rel}")

outp = ROOT / "outputs"
if outp.exists():
    for p in sorted(outp.rglob("*.png")):
        print(f"PNG  {p.relative_to(ROOT)} ({p.stat().st_size} bytes, magic_ok={png_ok(p)})")
    for p in sorted(outp.rglob("*.html")):
        print(f"HTML {p.relative_to(ROOT)} ({p.stat().st_size} bytes)")
    for p in sorted(outp.rglob("*.mvsj")):
        print(f"MVSJ {p.relative_to(ROOT)} ({p.stat().st_size} bytes)")
    for p in sorted(outp.rglob("scripts/*.py")):
        print(f"SCRIPT {p.relative_to(ROOT)} ({p.stat().st_size} bytes)")
    for p in sorted(outp.rglob("meta.json")):
        print(f"META {p.relative_to(ROOT)} ({p.stat().st_size} bytes)")
