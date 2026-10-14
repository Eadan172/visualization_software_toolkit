# -*- coding: utf-8 -*-
"""校验层 L0（文件级）与 L1（图像统计）。"""
from __future__ import annotations

import json
import pathlib

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
MIN_BYTES = 512
FOREGROUND_MIN = 0.005      # 前景占比下限（低于视为接近空白）
FOREGROUND_MAX = 0.98       # 前景占比上限（高于视为几乎被填满）
BG_TOLERANCE = 30           # 与背景色的 RGB 绝对差之和阈值


def check_l0(path, kind: str) -> list[str]:
    """L0 文件级校验，返回问题列表（空列表 = 通过）。"""
    issues: list[str] = []
    p = pathlib.Path(path)
    if not p.exists():
        return [f"产物不存在: {p}"]
    if p.stat().st_size < MIN_BYTES:
        issues.append(f"文件过小: {p.stat().st_size} B（阈值 {MIN_BYTES} B）")
    if kind == "png":
        if p.read_bytes()[:8] != PNG_MAGIC:
            issues.append("PNG 魔数不正确")
    elif kind == "html":
        text = p.read_text(encoding="utf-8", errors="replace").lower()
        if "<html" not in text and "<!doctype" not in text:
            issues.append("HTML 结构不完整（缺少 <html>/<!DOCTYPE>）")
    elif kind == "mvsj":
        try:
            json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            issues.append(f"mvsj JSON 解析失败: {type(e).__name__}")
    return issues


def check_l1_png(path, canvas: dict | None = None) -> tuple[list[str], dict]:
    """L1 图像统计校验：尺寸、前景占比、非全白/全黑。返回 (问题列表, 统计详情)。

    说明：Jmol 导出的 PNG 其 pHYs 附属块 CRC 有误（Jmol 自身缺陷，只影响 DPI 等元数据，
    与图像像素无关），会使 Pillow 12+ 的严格 CRC 校验判为「无法识别」。此处临时放宽
    附属块 CRC 校验以容忍该情况——作用域受限，退出即恢复全局设置。
    """
    from PIL import Image, ImageFile

    prev = ImageFile.LOAD_TRUNCATED_IMAGES
    ImageFile.LOAD_TRUNCATED_IMAGES = True
    try:
        with Image.open(path) as im:
            w, h = im.size
            rgb = im.convert("RGB")
            px = rgb.load()
            # 背景色取四角平均；网格采样避免大图全量遍历
            corners = [px[0, 0], px[w - 1, 0], px[0, h - 1], px[w - 1, h - 1]]
            bg = tuple(sum(c[i] for c in corners) // 4 for i in range(3))
            step = max(1, min(w, h) // 200)
            total = fg = 0
            for y in range(0, h, step):
                for x in range(0, w, step):
                    r, g, b = px[x, y]
                    total += 1
                    if abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2]) > BG_TOLERANCE:
                        fg += 1
            ratio = fg / total if total else 0.0
    except Exception as e:
        return [f"图像无法解析: {type(e).__name__}: {str(e)[:120]}"], {}
    finally:
        ImageFile.LOAD_TRUNCATED_IMAGES = prev

    details = {"size": [w, h], "background": list(bg),
               "foreground_ratio": round(ratio, 4), "sampled": total}
    issues: list[str] = []
    if canvas and canvas.get("width") and (w, h) != (canvas["width"], canvas["height"]):
        issues.append(f"尺寸不符: {w}x{h}（spec 期望 {canvas['width']}x{canvas['height']}）")
    if ratio < FOREGROUND_MIN:
        issues.append(f"图像接近空白（前景占比 {ratio:.2%} < {FOREGROUND_MIN:.1%}）")
    if ratio > FOREGROUND_MAX:
        issues.append(f"图像几乎被填满（前景占比 {ratio:.2%} > {FOREGROUND_MAX:.1%}）")
    return issues, details
