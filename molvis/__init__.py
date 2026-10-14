# -*- coding: utf-8 -*-
"""molvis —— 分子可视化工具包的核心 Python 包。

模块职责划分：
  config    全局路径与常量（样式表、PyMOL 脚本模板、依赖清单）
  utils     通用小工具（路径规范化、终端标题）
  engines/  各渲染引擎适配器（pymol / jmol / py3dmol / molviewspec）
  check     环境自检
  demo      一键演示流水线
  render    单结构渲染
  cli       命令行入口（check / demo / render）
"""
from __future__ import annotations

__version__ = "1.0.0"
