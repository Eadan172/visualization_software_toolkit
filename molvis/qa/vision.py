# -*- coding: utf-8 -*-
"""校验层 L2：调用可插拔的外部视觉模型，判定图像是否符合 RenderSpec 期望。

后端通过环境变量配置（OpenAI 兼容的 chat/completions 接口）：
    MOLVIS_VISION_BASE_URL  例如 https://api.example.com/v1
    MOLVIS_VISION_API_KEY   鉴权 Key
    MOLVIS_VISION_MODEL     模型名，例如 gpt-4o-mini / qwen-vl-max
三者缺一即视为「未配置」，L2 自动跳过（不影响其它校验与产物生成）。
"""
from __future__ import annotations

import base64
import json
import os
import pathlib
import urllib.request

PROMPT_TEMPLATE = (
    "你是分子可视化质检员。请判断下方图像是否符合这条期望描述：\n"
    "「{expectation}」\n\n"
    "只输出 JSON，不要输出其它文字，格式："
    '{{"passed": true/false, "confidence": 0.0-1.0, "reasons": ["..."]}}\n'
    "判断依据：主体对象是否存在、样式是否正确、背景是否相符、是否出现空白或明显错位。"
)


class VisionNotConfigured(RuntimeError):
    """未配置视觉后端。"""


def _config():
    """读取后端配置，三者缺一返回 None。"""
    base = os.environ.get("MOLVIS_VISION_BASE_URL", "").rstrip("/")
    key = os.environ.get("MOLVIS_VISION_API_KEY", "")
    model = os.environ.get("MOLVIS_VISION_MODEL", "")
    if not (base and key and model):
        return None
    return base, key, model


def _extract_json(text: str) -> dict:
    """从模型输出中提取 JSON（容忍 ``` 代码围栏与前后缀文字）。"""
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else t
        t = t.rsplit("```", 1)[0]
    start, end = t.find("{"), t.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("模型输出中未找到 JSON")
    return json.loads(t[start:end + 1])


def judge(image_path, expectation: str, timeout: int = 60) -> dict:
    """调用视觉后端做语义判定。返回 {passed, confidence, reasons, raw}。"""
    cfg = _config()
    if cfg is None:
        raise VisionNotConfigured()
    base, key, model = cfg
    p = pathlib.Path(image_path)
    b64 = base64.b64encode(p.read_bytes()).decode("ascii")
    mime = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
    payload = {
        "model": model,
        "temperature": 0,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": PROMPT_TEMPLATE.format(expectation=expectation)},
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
            ],
        }],
    }
    req = urllib.request.Request(
        f"{base}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    content = body["choices"][0]["message"]["content"]
    verdict = _extract_json(content)
    return {
        "passed": bool(verdict.get("passed")),
        "confidence": float(verdict.get("confidence", 0.0)),
        "reasons": list(verdict.get("reasons", []) or []),
        "raw": content[:500],
    }
