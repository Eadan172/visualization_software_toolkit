# -*- coding: utf-8 -*-
"""渲染引擎适配器集合。

每个适配器只负责「拿输入、调引擎、出产物、报成功与否」，
不做业务判断、不自行吞错、不决定回退策略。
"""
from __future__ import annotations
