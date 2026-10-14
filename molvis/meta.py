# -*- coding: utf-8 -*-
"""作业元数据（meta.json）：每个作业目录写一份可复现记录。

记录内容：作业类型与 id、时间、RenderSpec、输入文件 sha256、使用引擎与组件版本、
画布、各产物（相对路径 / 大小 / sha256）、质量校验结果、失败项与总耗时。
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import pathlib

from . import __version__

META_NAME = "meta.json"


def sha256_file(path, chunk: int = 1 << 20) -> str:
    """计算文件 sha256（分块读取，适用大文件）。"""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def new_job_id() -> str:
    return _dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def now_iso() -> str:
    return _dt.datetime.now().astimezone().isoformat(timespec="seconds")


def runtime_versions() -> dict:
    """相关运行期组件版本（缺失记 None）。"""
    from importlib import metadata
    out: dict = {"molvis": __version__}
    for dist, key in (("pymol", "pymol"), ("py3Dmol", "py3dmol"),
                      ("molviewspec", "molviewspec"), ("MDAnalysis", "mdanalysis"),
                      ("rdkit", "rdkit"), ("matplotlib", "matplotlib"), ("Pillow", "pillow")):
        try:
            out[key] = metadata.version(dist)
        except Exception:
            out[key] = None
    # Jmol 版本从 Jar 所在目录名推断（如 jmol-16.3.51）
    try:
        from .engines.jmol import find_jmol_jar
        jar = find_jmol_jar()
        out["jmol"] = jar.parent.name.split("-")[-1] if jar else None
    except Exception:
        out["jmol"] = None
    return out


class JobMeta:
    """一次作业的可复现记录。"""

    def __init__(self, kind: str, job_id: str | None = None):
        self.kind = kind
        self.job_id = job_id or new_job_id()
        self.created_at = now_iso()
        self.spec: dict | None = None
        self.inputs: list[dict] = []
        self.engine: dict = {}
        self.canvas: dict | None = None
        self.artifacts: list[dict] = []
        self.qa: dict = {}
        self.failures: list[str] = []
        self.secs: float = 0.0
        self.extra: dict = {}

    # ---- 记录项 ----------------------------------------------------------
    def set_spec(self, spec) -> "JobMeta":
        if spec is not None and hasattr(spec, "to_dict"):
            self.spec = spec.to_dict()
        return self

    def add_input(self, path) -> "JobMeta":
        """记录输入文件（路径 + 大小 + sha256）。"""
        p = pathlib.Path(path)
        rec: dict = {"path": str(p)}
        if p.exists():
            rec["size"] = p.stat().st_size
            rec["sha256"] = sha256_file(p)
        self.inputs.append(rec)
        return self

    def set_engine(self, requested: str, used: str | None = None, **info) -> "JobMeta":
        self.engine = {"requested": requested, "used": used or requested, **info}
        return self

    def add_artifact(self, kind: str, path, outdir=None) -> "JobMeta":
        """记录产物（相对作业目录的 posix 路径 + 大小 + sha256）。"""
        p = pathlib.Path(path)
        rel = p
        if outdir is not None:
            try:
                rel = p.resolve().relative_to(pathlib.Path(outdir).resolve())
            except Exception:
                rel = p
        rec: dict = {"kind": kind, "path": str(rel).replace("\\", "/")}
        if p.exists():
            rec["size"] = p.stat().st_size
            rec["sha256"] = sha256_file(p)
        self.artifacts.append(rec)
        return self

    def set_qa(self, level: int, results=None, passed: bool | None = None) -> "JobMeta":
        from .qa import as_dict
        recs = [as_dict(r) for r in (results or [])]
        self.qa = {
            "level": level,
            "passed": bool(passed) if passed is not None else all(r["passed"] for r in recs),
            "results": recs,
        }
        return self

    def set_failures(self, failures) -> "JobMeta":
        self.failures = list(failures or [])
        return self

    # ---- 输出 ------------------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "tool": "molvis",
            "tool_version": __version__,
            "kind": self.kind,
            "job_id": self.job_id,
            "created_at": self.created_at,
            "secs": round(self.secs, 3),
            "spec": self.spec,
            "input": self.inputs,
            "engine": self.engine,
            "canvas": self.canvas,
            "artifacts": self.artifacts,
            "qa": self.qa,
            "failures": self.failures,
            "versions": runtime_versions(),
            **self.extra,
        }

    def write(self, outdir) -> pathlib.Path:
        """写出 <outdir>/meta.json，返回其路径。"""
        outdir = pathlib.Path(outdir)
        outdir.mkdir(parents=True, exist_ok=True)
        path = outdir / META_NAME
        path.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return path
