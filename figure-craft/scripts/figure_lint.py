#!/usr/bin/env python3
"""figure_lint.py — 出图机械自检：最小字号、有效分辨率、文字可编辑、矢量纯度、画布尺寸。

边界：只用本地文件，不联网、不调用模型、不改动被检文件。只查确定性项；
通过不代表视觉验收通过（判据见 references/导出、自检与图注.md 的 FIG11）。

用法（建议设置 PYTHONUTF8=1）：
  python figure_lint.py <文件> [--width-mm 89] [--min-pt 5] [--min-dpi 300] [--allow-no-text] [--json]

退出码：0=通过；1=有警告；2=有失败、输入错误或依赖缺失。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

MM_PER_INCH = 25.4
PT_PER_INCH = 72.0
PX_PER_INCH = 96.0
WIDTH_TOLERANCE_MM = 2.0

SVG_TAG_RE = re.compile(r"<svg\b[^>]*>", re.IGNORECASE)
SVG_WIDTH_RE = re.compile(r'\bwidth\s*=\s*"([0-9.]+)\s*(mm|cm|in|pt|px)?"', re.IGNORECASE)
SVG_FONT_RE = re.compile(r'font-size\s*[:=]\s*"?([0-9.]+)\s*(pt|px)?"?', re.IGNORECASE)


def _length_to_mm(value: float, unit: str) -> float:
    unit = (unit or "px").lower()
    if unit == "mm":
        return value
    if unit == "cm":
        return value * 10.0
    if unit == "in":
        return value * MM_PER_INCH
    if unit == "pt":
        return value * MM_PER_INCH / PT_PER_INCH
    return value * MM_PER_INCH / PX_PER_INCH


def _font_to_pt(value: float, unit: str) -> float:
    if (unit or "px").lower() == "pt":
        return value
    return value * PT_PER_INCH / PX_PER_INCH


def _add(findings: list[dict], level: str, check: str, message: str) -> None:
    findings.append({"level": level, "check": check, "message": message})


def _lint_svg(path: Path, width_mm: float | None, min_pt: float, allow_no_text: bool) -> list[dict]:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    findings: list[dict] = []

    tag = SVG_TAG_RE.search(text)
    if not tag:
        _add(findings, "fail", "画布尺寸", "未找到 <svg> 根标签，文件可能不是 SVG")
        return findings
    width = SVG_WIDTH_RE.search(tag.group(0))
    if width:
        svg_mm = _length_to_mm(float(width.group(1)), width.group(2) or "px")
        if width_mm is not None and abs(svg_mm - width_mm) > WIDTH_TOLERANCE_MM:
            _add(findings, "warn", "画布尺寸",
                 f"SVG 宽 {svg_mm:.1f} mm 与目标 {width_mm:.1f} mm 偏差超过 {WIDTH_TOLERANCE_MM:g} mm")
    else:
        _add(findings, "warn", "画布尺寸", "SVG 未声明 width，无法核对目标宽度")

    sizes = [_font_to_pt(float(m.group(1)), m.group(2) or "px") for m in SVG_FONT_RE.finditer(text)]
    if sizes:
        smallest = min(sizes)
        if smallest < min_pt:
            _add(findings, "fail", "最小字号", f"最小字号约 {smallest:.1f} pt，低于下限 {min_pt:g} pt")
    elif "<text" in text:
        _add(findings, "warn", "最小字号", "含文本节点但未检出 font-size，需人工核对")

    if "<text" not in text:
        level = "warn" if allow_no_text else "fail"
        message = "未检出 <text> 节点" + ("（已按参数忽略）" if allow_no_text else "，文字可能已转为路径")
        _add(findings, level, "文字可编辑", message)

    if "<image" in text:
        _add(findings, "warn", "矢量纯度", "SVG 内含位图 <image>，该部分不可矢量化")

    return findings


def _lint_png(path: Path, width_mm: float | None, min_dpi: float) -> list[dict]:
    try:
        from PIL import Image
    except ImportError:
        raise RuntimeError("缺少 Pillow，无法检查 PNG；请先安装 Pillow（pip install pillow）")

    findings: list[dict] = []
    with Image.open(path) as image:
        px_width = image.size[0]
        dpi_meta = image.info.get("dpi")

    if width_mm:
        effective = px_width / (width_mm / MM_PER_INCH)
        if effective < min_dpi:
            _add(findings, "warn", "有效分辨率",
                 f"{px_width} px 在 {width_mm:g} mm 宽度下约 {effective:.0f} dpi，低于 {min_dpi:g} dpi")
    elif dpi_meta:
        dpi = float(dpi_meta[0])
        if dpi < min_dpi:
            _add(findings, "warn", "有效分辨率", f"按元数据 {dpi:.0f} dpi，低于 {min_dpi:g} dpi")
    else:
        _add(findings, "warn", "有效分辨率", "未给 --width-mm 且无 dpi 元数据，无法核对实际分辨率")

    _add(findings, "warn", "矢量纯度", "PNG 为位图，线稿与文字不可再编辑")
    return findings


def _lint_pdf(path: Path, width_mm: float | None, min_pt: float, allow_no_text: bool) -> list[dict]:
    try:
        import fitz
    except ImportError:
        raise RuntimeError("缺少 PyMuPDF，无法检查 PDF；请先安装 PyMuPDF（pip install pymupdf）")

    findings: list[dict] = []
    document = fitz.open(str(path))
    try:
        if document.page_count == 0:
            _add(findings, "fail", "输入", "PDF 没有页面")
            return findings
        page = document[0]
        page_mm = page.rect.width * MM_PER_INCH / PT_PER_INCH
        if width_mm is not None and abs(page_mm - width_mm) > WIDTH_TOLERANCE_MM:
            _add(findings, "warn", "画布尺寸",
                 f"页面宽 {page_mm:.1f} mm 与目标 {width_mm:.1f} mm 偏差超过 {WIDTH_TOLERANCE_MM:g} mm")

        sizes: list[float] = []
        for block in page.get_text("dict").get("blocks", []):
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    sizes.append(float(span.get("size", 0.0)))
        if sizes:
            smallest = min(sizes)
            if smallest < min_pt:
                _add(findings, "fail", "最小字号", f"最小字号约 {smallest:.1f} pt，低于下限 {min_pt:g} pt")

        fonts = page.get_fonts(full=True)
        images = page.get_images(full=True)
        if not sizes and not fonts:
            level = "warn" if allow_no_text else "fail"
            message = "未检出可编辑文字与字体" + ("（已按参数忽略）" if allow_no_text else "，文字可能已转曲")
            _add(findings, level, "文字可编辑", message)
        if images:
            _add(findings, "warn", "矢量纯度", f"PDF 内含 {len(images)} 个位图对象")
    finally:
        document.close()
    return findings


def lint_file(path: str | Path, *, width_mm: float | None = None,
              min_pt: float = 5.0, min_dpi: float = 300.0,
              allow_no_text: bool = False) -> dict:
    """检查一个导出图件，返回 {file, verdict, findings}。"""

    target = Path(path)
    if not target.is_file():
        raise FileNotFoundError(f"文件不存在: {target}")

    suffix = target.suffix.lower()
    if suffix == ".svg":
        findings = _lint_svg(target, width_mm, min_pt, allow_no_text)
    elif suffix == ".pdf":
        findings = _lint_pdf(target, width_mm, min_pt, allow_no_text)
    elif suffix in {".png", ".tif", ".tiff"}:
        findings = _lint_png(target, width_mm, min_dpi)
    else:
        raise ValueError(f"不支持的文件类型: {suffix or '(无后缀)'}")

    if any(item["level"] == "fail" for item in findings):
        verdict = 2
    elif any(item["level"] == "warn" for item in findings):
        verdict = 1
    else:
        verdict = 0
    return {"file": str(target), "verdict": verdict, "findings": findings}


def _render(result: dict) -> str:
    lines = [f"图件自检：{result['file']}"]
    if not result["findings"]:
        lines.append("  未发现可机械判定的问题。")
    for item in result["findings"]:
        mark = "失败" if item["level"] == "fail" else "警告"
        lines.append(f"  [{mark}] {item['check']}：{item['message']}")
    lines.append({0: "结论：机械项通过；视觉与统计核对仍需人工完成。",
                  1: "结论：有警告，请人工核对后再交付。",
                  2: "结论：未通过，按规则不得交付。"}[result["verdict"]])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="科研图件出图机械自检")
    parser.add_argument("file", help="导出图件路径（SVG、PDF、PNG、TIFF）")
    parser.add_argument("--width-mm", type=float, default=None, help="目标刊印宽度（毫米）")
    parser.add_argument("--min-pt", type=float, default=5.0, help="最小字号下限（默认 5 pt）")
    parser.add_argument("--min-dpi", type=float, default=300.0, help="有效分辨率下限（默认 300 dpi）")
    parser.add_argument("--allow-no-text", action="store_true", help="允许图中没有可编辑文字")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args(argv)

    try:
        result = lint_file(args.file, width_mm=args.width_mm, min_pt=args.min_pt,
                           min_dpi=args.min_dpi, allow_no_text=args.allow_no_text)
    except (FileNotFoundError, ValueError, RuntimeError) as error:
        payload = {"error": str(error)}
        print(json.dumps(payload, ensure_ascii=False) if args.json else f"错误：{error}")
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else _render(result))
    return result["verdict"]


if __name__ == "__main__":
    sys.exit(main())
