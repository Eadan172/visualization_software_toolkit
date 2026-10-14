# -*- coding: utf-8 -*-
"""校验层编排：按 qa_level 依次执行 L0 / L1 / L2 并结构化汇报。

    qa_level 0  关闭校验（与历史行为一致）
    qa_level 1  L0 文件级 + L1 图像统计
    qa_level 2  追加 L2 视觉语义（需配置视觉后端，未配置则自动跳过）
"""
from __future__ import annotations

import pathlib
from dataclasses import dataclass, field

from .checks import check_l0, check_l1_png
from .vision import VisionNotConfigured, judge

__all__ = ["QaResult", "validate", "report", "summarize", "as_dict", "check_l0", "check_l1_png"]

_LEVEL_LABEL = {0: "已关闭", 1: "L0 + L1", 2: "L0 + L1 + L2"}


@dataclass
class QaResult:
    """单个产物的校验结果。"""

    artifact: str
    kind: str
    level: int
    passed: bool
    issues: list = field(default_factory=list)
    details: dict = field(default_factory=dict)
    l2: dict = field(default_factory=dict)


def validate(path, kind: str, spec=None, qa_level: int = 1) -> QaResult:
    """对单个产物执行质量校验。L2 仅对 PNG 生效（HTML / mvsj 止于 L0）。"""
    path = pathlib.Path(path)
    issues: list[str] = []
    details: dict = {}
    l2: dict = {"status": "not_run"}

    l0 = check_l0(path, kind)
    details["l0"] = "ok" if not l0 else "fail"
    issues += l0

    if qa_level >= 1 and kind == "png" and not l0:
        l1, d1 = check_l1_png(path, getattr(spec, "canvas", None) if spec else None)
        details["l1"] = d1
        issues += l1

    if qa_level >= 2 and kind == "png" and not issues:
        expectation = (getattr(spec, "description", "") or "") if spec else ""
        try:
            verdict = judge(path, expectation)
            l2 = {"status": "pass" if verdict["passed"] else "fail", **verdict}
            if not verdict["passed"]:
                reasons = "; ".join(verdict.get("reasons") or []) or "模型未给出理由"
                issues.append(f"L2 语义不符: {reasons}")
        except VisionNotConfigured:
            l2 = {"status": "skipped",
                  "reason": "未配置视觉后端（MOLVIS_VISION_BASE_URL / _API_KEY / _MODEL）"}
        except Exception as e:  # 后端不可达、超时、返回不可解析等
            l2 = {"status": "error", "reason": f"{type(e).__name__}: {str(e)[:160]}"}

    return QaResult(str(path), kind, qa_level, not issues, issues, details, l2)


def summarize(r: QaResult) -> str:
    """把单个结果渲染成一行摘要。"""
    tag = r.kind.upper().ljust(4)
    name = pathlib.Path(r.artifact).name
    if not r.passed:
        return f"[!!] {tag} {name}  " + "；".join(r.issues)
    line = f"[OK] {tag} {name}"
    l1 = r.details.get("l1")
    if isinstance(l1, dict):
        line += f"  尺寸 {l1.get('size')}  前景 {l1.get('foreground_ratio', 0):.1%}"
    status = r.l2.get("status")
    if status == "pass":
        line += f"  L2=通过(conf={r.l2.get('confidence', 0):.2f})"
    elif status == "fail":
        line += "  L2=不符"
    elif status == "skipped":
        line += "  L2=跳过（未配置视觉后端）"
    elif status == "error":
        line += f"  L2=错误（{r.l2.get('reason', '')}）"
    return line


def as_dict(r: QaResult) -> dict:
    """序列化为可写入 meta.json 的轻量记录（artifact 取文件名，保证记录可移植）。"""
    return {"artifact": pathlib.Path(r.artifact).name, "kind": r.kind, "level": r.level,
            "passed": r.passed, "issues": list(r.issues), "l2": r.l2.get("status", "not_run")}


def report(results: list[QaResult], qa_level: int) -> bool:
    """打印整组校验结果，返回是否全部通过。"""
    if qa_level < 1:
        print("\n== 质量校验：已跳过（qa_level=0）==")
        return True
    print(f"\n== 质量校验（{_LEVEL_LABEL.get(qa_level, qa_level)}）==")
    ok = True
    for r in results:
        print(summarize(r))
        ok = ok and r.passed
    return ok
