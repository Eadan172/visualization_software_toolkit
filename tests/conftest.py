# -*- coding: utf-8 -*-
"""pytest 共享夹具：合成最小 PNG / HTML / MVSJ，避免测试依赖真实渲染。

合成文件均补足到 512 B 以上，以符合 L0「文件过小」阈值（真实产物远大于该阈值）。
"""
from __future__ import annotations

import json

from PIL import Image, PngImagePlugin
import pytest

PAD = "x" * 700


@pytest.fixture
def make_png(tmp_path):
    """生成最小 PNG。默认整幅白底（接近空白）；给 blob 则画一块前景色块。"""
    def _make(name: str = "a.png", size=(200, 150), color=(255, 255, 255), blob=None):
        path = tmp_path / name
        im = Image.new("RGB", size, color)
        if blob is not None:
            for x in range(size[0] // 4, size[0] // 2):
                for y in range(size[1] // 4, size[1] // 2):
                    im.putpixel((x, y), blob)
        info = PngImagePlugin.PngInfo()
        info.add_text("pad", PAD)          # 补足体积到 512 B 以上
        im.save(path, pnginfo=info)
        return path
    return _make


@pytest.fixture
def make_html(tmp_path):
    def _make(name: str = "a.html", full: bool = True):
        path = tmp_path / name
        body = "<!DOCTYPE html><html><body>3dmol</body></html>" if full else "<div>x</div>"
        path.write_text(f"{body}<!--{PAD}-->", encoding="utf-8")
        return path
    return _make


@pytest.fixture
def make_mvsj(tmp_path):
    def _make(name: str = "a.mvsj", valid: bool = True):
        path = tmp_path / name
        payload = json.dumps({"kind": "single", "pad": PAD}) if valid else "{not json" + PAD
        path.write_text(payload, encoding="utf-8")
        return path
    return _make
