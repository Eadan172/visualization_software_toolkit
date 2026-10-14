# -*- coding: utf-8 -*-
"""最小 RenderSpec：引擎无关的渲染意图载体。

本轮落地「结构 + 样式 + 画布 + 期望描述 + 校验策略」最小子集，
作为 L2 语义校验的「期望画像」来源，并通过 spec_version 为后续演进预留空间。
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass, field

from .config import DEFAULT_CANVAS, STYLES

SPEC_VERSION = "1.0"

# 各样式的中文期望描述模板（用于 L2 视觉判定），{name} 处填入结构名
_STYLE_EXPECTATIONS = {
    "cartoon": "白色背景上的蛋白质卡通图（cartoon），{name} 以二级结构着色区分螺旋与折叠",
    "surface": "白色背景上的蛋白卡通叠加半透明分子表面（surface），主体为 {name}",
    "sticks": "白色背景上的全原子棍状模型（sticks），主体为 {name}",
    "ligand": "白色背景上蛋白半透明卡通、配体（有机小分子）以橙色棍状高亮，为 {name} 的配体口袋视图",
}

_FORMATS = {"auto", "pdb", "cif"}


class SpecError(ValueError):
    """RenderSpec 校验失败。"""


@dataclass
class RenderSpec:
    """最小渲染规格。"""

    structure_source: str = ""
    style: str = "cartoon"
    structure_format: str = "auto"
    canvas: dict = field(default_factory=lambda: dict(DEFAULT_CANVAS))
    description: str = ""
    qa_level: int = 1
    spec_version: str = SPEC_VERSION

    def __post_init__(self) -> None:
        # 画布只保留已知字段，并用默认值补齐
        self.canvas = {**DEFAULT_CANVAS,
                       **{k: v for k, v in (self.canvas or {}).items() if k in DEFAULT_CANVAS}}

    def default_description(self) -> str:
        """按结构名与样式生成期望描述（L2 的期望画像）。"""
        name = pathlib.Path(self.structure_source).name or self.structure_source or "该结构"
        tpl = _STYLE_EXPECTATIONS.get(self.style, _STYLE_EXPECTATIONS["cartoon"])
        return tpl.format(name=name)

    def validate(self) -> None:
        """就地校验并补全，非法则抛 SpecError。"""
        if not self.structure_source:
            raise SpecError("structure.source 不能为空")
        if self.style not in STYLES:
            raise SpecError(f"未知样式: {self.style}（可选: {', '.join(STYLES)}）")
        if self.structure_format not in _FORMATS:
            raise SpecError(f"未知结构格式: {self.structure_format}（可选: {', '.join(sorted(_FORMATS))}）")
        if self.qa_level not in (0, 1, 2):
            raise SpecError("policy.qa_level 只能为 0 / 1 / 2")
        if not self.description:
            self.description = self.default_description()

    def to_dict(self) -> dict:
        return {
            "spec_version": self.spec_version,
            "structure": {"source": self.structure_source, "format": self.structure_format},
            "style": self.style,
            "canvas": dict(self.canvas),
            "description": self.description,
            "policy": {"qa_level": self.qa_level},
        }


def load_spec(path) -> RenderSpec:
    """从 JSON 文件读取 RenderSpec（不自动 validate，交由调用方决定）。"""
    data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SpecError("spec 根节点必须是 JSON 对象")
    structure = data.get("structure") or {}
    policy = data.get("policy") or {}
    spec = RenderSpec(
        spec_version=data.get("spec_version", SPEC_VERSION),
        structure_source=structure.get("source", ""),
        structure_format=structure.get("format", "auto"),
        style=data.get("style", "cartoon"),
        canvas=data.get("canvas") or {},
        description=data.get("description", ""),
        qa_level=policy.get("qa_level", data.get("qa_level", 1)),
    )
    return spec
