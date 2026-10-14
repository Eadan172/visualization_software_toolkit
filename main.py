# -*- coding: utf-8 -*-
"""分子可视化工具包 · 统一入口

本文件只做一件事：把命令行交给 molvis 包，行为与历史版本完全一致。

用法（在项目根目录下）：
    .venv\\Scripts\\python.exe main.py             # 默认：环境自检 + 一键演示
    .venv\\Scripts\\python.exe main.py check       # 仅环境自检
    .venv\\Scripts\\python.exe main.py demo        # 一键演示（PyMOL + Jmol + py3Dmol + MolViewSpec）
    .venv\\Scripts\\python.exe main.py render 1hsg # 渲染结构（data 文件名 / PDB ID / .pdb 路径）
    .venv\\Scripts\\python.exe main.py render 1hsg --style ligand
也可以直接双击项目根目录的“启动.bat”。

实际实现位于 molvis/ 包：
    molvis.cli     命令行入口
    molvis.check   环境自检
    molvis.demo    一键演示
    molvis.render  单结构渲染
    molvis.engines 各渲染引擎适配器
"""
from __future__ import annotations

import sys

from molvis.cli import main

if __name__ == "__main__":
    sys.exit(main())
