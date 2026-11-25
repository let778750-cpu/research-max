#!/usr/bin/env python3
"""layout_audit.py — 基于 matplotlib Figure 对象的版面自检：文字重叠、出界裁切、字号下限、缺字、图例压数据。

与 figure_lint 分工：figure_lint 查导出文件（字体类型、嵌入、画布、分辨率）；本脚本在保存前查
渲染后的版面几何。通过不代表视觉验收通过（FIG11），缺字以渲染告警与字形表双重判定。

库用法：
  from layout_audit import audit_figure
  result = audit_figure(fig, min_pt=7)       # {"verdict", "findings"}；verdict 0/1/2
"""

from __future__ import annotations

import warnings
from itertools import combinations

import numpy as np

OVERLAP_MIN_FRACTION = 0.05   # 交叠面积占较小文字框的比例，超过即判重叠
CANVAS_TOLERANCE_PX = 1.0     # 文字框越出画布超过该像素即判裁切
LEGEND_POINT_MARGIN_PX = 1.0


def _add(findings: list[dict], level: str, check: str, message: str) -> None:
    findings.append({"level": level, "check": check, "message": message})


def _undrawn_tick_labels(fig) -> set[int]:
    """matplotlib 为视窗外的刻度保留标签对象但不绘制；按 draw 时的同一筛选剔除。"""
    hidden: set[int] = set()
    for ax in fig.axes:
        axes_map = getattr(ax, "_axis_map", {"x": ax.xaxis, "y": ax.yaxis})
        for axis in axes_map.values():
            try:
                shown = {id(tick) for tick in axis._update_ticks()}
            except AttributeError:
                continue
            for tick in axis.get_major_ticks() + axis.get_minor_ticks():
                if id(tick) not in shown:
                    hidden.update({id(tick.label1), id(tick.label2)})
    return hidden


def _visible_texts(fig) -> list:
    from matplotlib.text import Text
    hidden = _undrawn_tick_labels(fig)
    texts = []
    for artist in fig.findobj(Text):
        if (artist.get_visible() and artist.get_text().strip() and id(artist) not in hidden
                and _ancestors_visible(artist)):
            texts.append(artist)
    return texts


def _ancestors_visible(artist) -> bool:
    axes = getattr(artist, "axes", None)
    return axes is None or axes.get_visible()


def _label(text) -> str:
    content = text.get_text().replace("\n", " ")
    return content if len(content) <= 24 else content[:22] + "…"


def _draw(fig) -> tuple[object, list[str]]:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        fig.canvas.draw()
    messages = [str(w.message) for w in caught if "missing from" in str(w.message) or "Glyph" in str(w.message)]
    return fig.canvas.get_renderer(), messages


def _overlaps(texts: list, renderer) -> list[str]:
    boxes = [(t, t.get_window_extent(renderer)) for t in texts]
    found = []
    for (ta, a), (tb, b) in combinations(boxes, 2):
        width = min(a.x1, b.x1) - max(a.x0, b.x0)
        height = min(a.y1, b.y1) - max(a.y0, b.y0)
        if width <= 0 or height <= 0:
            continue
        smaller = min(a.width * a.height, b.width * b.height) or 1.0
        if width * height / smaller > OVERLAP_MIN_FRACTION:
            found.append(f"「{_label(ta)}」与「{_label(tb)}」")
    return found


def _clipped(texts: list, renderer, fig) -> list[str]:
    canvas = fig.bbox
    out = []
    for text in texts:
        box = text.get_window_extent(renderer)
        if (box.x0 < canvas.x0 - CANVAS_TOLERANCE_PX or box.y0 < canvas.y0 - CANVAS_TOLERANCE_PX
                or box.x1 > canvas.x1 + CANVAS_TOLERANCE_PX or box.y1 > canvas.y1 + CANVAS_TOLERANCE_PX):
            out.append(f"「{_label(text)}」")
    return out


def _font_chain(text) -> list:
    from matplotlib import font_manager
    from matplotlib.ft2font import FT2Font
    props = text.get_fontproperties()
    try:
        paths = font_manager.fontManager._find_fonts_by_props(props)
    except AttributeError:
        paths = [font_manager.findfont(props)]
    return [FT2Font(str(path)) for path in paths]


def _missing_glyphs(texts: list) -> list[str]:
    found = []
    for text in texts:
        content = text.get_text()
        if content.count("$") >= 2:
            continue  # 数学文本由 mathtext 字体负责，靠渲染告警判定
        fonts = _font_chain(text)
        absent = sorted({ch for ch in content if not ch.isspace()
                         and not any(font.get_char_index(ord(ch)) for font in fonts)})
        if absent:
            found.append(f"「{_label(text)}」缺 {''.join(absent)}")
    return found


def _data_points(ax) -> np.ndarray:
    chunks = []
    for line in ax.get_lines():
        if line.get_visible() and len(line.get_xydata()):
            chunks.append(line.get_transform().transform(line.get_xydata()))
    for collection in ax.collections:
        offsets = collection.get_offsets()
        if collection.get_visible() and len(offsets):
            chunks.append(collection.get_offset_transform().transform(offsets))
    if not chunks:
        return np.empty((0, 2))
    points = np.vstack(chunks)
    return points[np.isfinite(points).all(axis=1)]


def _legend_hits(fig, renderer) -> list[str]:
    hits = []
    for index, ax in enumerate(fig.axes):
        legend = ax.get_legend()
        if legend is None or not legend.get_visible():
            continue
        box = legend.get_window_extent(renderer).expanded(1.0, 1.0)
        points = _data_points(ax)
        inside = ((points[:, 0] > box.x0 + LEGEND_POINT_MARGIN_PX) & (points[:, 0] < box.x1 - LEGEND_POINT_MARGIN_PX)
                  & (points[:, 1] > box.y0 + LEGEND_POINT_MARGIN_PX) & (points[:, 1] < box.y1 - LEGEND_POINT_MARGIN_PX))
        if inside.any():
            hits.append(f"第 {index + 1} 个坐标轴：图例下压 {int(inside.sum())} 个数据点")
    return hits


def audit_figure(fig, min_pt: float | None = None) -> dict:
    """渲染一次并检查版面；返回 {verdict, findings}，verdict 0=通过 1=警告 2=失败。"""
    renderer, glyph_warnings = _draw(fig)
    texts = _visible_texts(fig)
    findings: list[dict] = []
    if min_pt is not None:
        small = sorted({round(t.get_fontsize(), 2) for t in texts if t.get_fontsize() < min_pt - 1e-6})
        if small:
            _add(findings, "fail", "字号下限", f"存在 {small} pt 文字，低于 {min_pt:g} pt")
    missing = _missing_glyphs(texts)
    if missing or glyph_warnings:
        detail = "；".join(missing) or "；".join(sorted(set(glyph_warnings)))[:200]
        _add(findings, "fail", "缺字", f"{detail}（会显示为方块，补中文或数学字体回退）")
    clipped = _clipped(texts, renderer, fig)
    if clipped:
        _add(findings, "fail", "出界裁切", "、".join(clipped) + " 越出画布")
    overlaps = _overlaps(texts, renderer)
    if overlaps:
        _add(findings, "warn", "文字重叠", "；".join(overlaps[:8]) + (" 等" if len(overlaps) > 8 else ""))
    for hit in _legend_hits(fig, renderer):
        _add(findings, "warn", "图例压数据", hit + "；移到空白处或改为直接标注")
    levels = {item["level"] for item in findings}
    verdict = 2 if "fail" in levels else 1 if "warn" in levels else 0
    return {"verdict": verdict, "findings": findings}


def render(result: dict, name: str = "图件") -> str:
    marks = {"fail": "失败", "warn": "警告", "info": "信息"}
    lines = [f"版面自检：{name}"]
    lines += [f"  [{marks[i['level']]}] {i['check']}：{i['message']}" for i in result["findings"]]
    if not result["findings"]:
        lines.append("  未发现可机械判定的版面问题。")
    return "\n".join(lines)
