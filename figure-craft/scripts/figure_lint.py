#!/usr/bin/env python3
"""figure_lint.py — 出图机械自检：画布宽度、最小字号、最细线宽、字体类型与嵌入、文字可编辑、矢量纯度、有效分辨率。

边界：只读本地文件，不联网、不调用模型、不改动被检文件。只查确定性项；
通过不代表视觉验收通过（判据见 references/导出、自检与图注.md 的 FIG11）。

用法（建议设置 PYTHONUTF8=1）：
  python figure_lint.py <文件>... [--profile aiaa --columns single]
                        [--width-mm 89] [--min-pt 5] [--min-line-pt 0.25] [--min-dpi 300]
                        [--allow-raster] [--allow-no-text] [--json]
--profile 从 templates/journal_profiles.json 读栏宽、字号下限、线宽下限与 dpi；显式参数优先。

退出码：0=通过；1=有警告；2=有失败、输入错误或依赖缺失（多文件取最严重者）。
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
DEFAULT_MIN_PT = 5.0
DEFAULT_MIN_DPI = 300.0
PROFILES_PATH = Path(__file__).resolve().parent.parent / "templates" / "journal_profiles.json"

SVG_TAG_RE = re.compile(r"<svg\b[^>]*>", re.IGNORECASE | re.DOTALL)
SVG_LEN_RE = r'\b{}\s*=\s*"([0-9.]+)\s*(mm|cm|in|pt|px)?"'
SVG_VIEWBOX_RE = re.compile(r'\bviewBox\s*=\s*"[-0-9.eE]+[\s,]+[-0-9.eE]+[\s,]+([0-9.eE]+)', re.IGNORECASE)
# 同时识别 font-size: 8px、font-size="8"、以及简写 font: 8px 'Arial'
SVG_FONT_RE = re.compile(r'(?:font-size\s*[:=]\s*"?|\bfont\s*:\s*(?:(?:italic|bold|normal|oblique|\d00)\s+)*)'
                         r'([0-9.]+)\s*(pt|px)?', re.IGNORECASE)
SVG_STROKE_RE = re.compile(r'stroke-width\s*[:=]\s*"?([0-9.]+)', re.IGNORECASE)
EPS_BBOX_RE = re.compile(rb"%%BoundingBox:\s*(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)")


def _length_to_mm(value: float, unit: str) -> float:
    factor = {"mm": 1.0, "cm": 10.0, "in": MM_PER_INCH,
              "pt": MM_PER_INCH / PT_PER_INCH}.get((unit or "px").lower(), MM_PER_INCH / PX_PER_INCH)
    return value * factor


def _add(findings: list[dict], level: str, check: str, message: str) -> None:
    findings.append({"level": level, "check": check, "message": message})


def _check_width(findings: list[dict], actual_mm: float, target_mm: float | None, what: str) -> None:
    if target_mm is not None and abs(actual_mm - target_mm) > WIDTH_TOLERANCE_MM:
        _add(findings, "warn", "画布尺寸",
             f"{what}宽 {actual_mm:.1f} mm 与目标 {target_mm:.1f} mm 偏差超过 {WIDTH_TOLERANCE_MM:g} mm"
             "（不要用 bbox_inches='tight' 改画布）")


def _check_min(findings: list[dict], values: list[float], limit: float | None,
               check: str, level: str, unit: str = "pt") -> None:
    if values and limit is not None and min(values) < limit - 1e-6:
        _add(findings, level, check, f"最小值约 {min(values):.2f} {unit}，低于下限 {limit:g} {unit}")


def _check_raster(findings: list[dict], count: int, allow_raster: bool, where: str) -> None:
    if count and not allow_raster:
        _add(findings, "warn", "矢量纯度", f"{where}含 {count} 个位图对象（照片类图件用 --allow-raster）")


def _no_text(findings: list[dict], allow_no_text: bool, message: str) -> None:
    level = "warn" if allow_no_text else "fail"
    suffix = "（已按参数放宽）" if allow_no_text else "，文字可能已转为路径"
    _add(findings, level, "文字可编辑", message + suffix)


def _svg_scale_pt(tag: str) -> tuple[float | None, float]:
    """返回 (画布宽 mm, 每个用户单位对应的 pt)。有 viewBox 时用户单位按宽度缩放。"""
    width = re.search(SVG_LEN_RE.format("width"), tag, re.IGNORECASE)
    if not width:
        return None, PT_PER_INCH / PX_PER_INCH
    width_mm = _length_to_mm(float(width.group(1)), width.group(2) or "px")
    viewbox = SVG_VIEWBOX_RE.search(tag)
    if viewbox and float(viewbox.group(1)) > 0:
        return width_mm, width_mm / MM_PER_INCH * PT_PER_INCH / float(viewbox.group(1))
    return width_mm, PT_PER_INCH / PX_PER_INCH


def _lint_svg(path: Path, opts: dict) -> list[dict]:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    findings: list[dict] = []
    tag = SVG_TAG_RE.search(text)
    if not tag:
        _add(findings, "fail", "画布尺寸", "未找到 <svg> 根标签，文件可能不是 SVG")
        return findings
    width_mm, unit_pt = _svg_scale_pt(tag.group(0))
    if width_mm is None:
        _add(findings, "warn", "画布尺寸", "SVG 未声明 width，无法核对目标宽度")
    else:
        _check_width(findings, width_mm, opts["width_mm"], "SVG ")

    sizes = [float(m.group(1)) * (1.0 if (m.group(2) or "").lower() == "pt" else unit_pt)
             for m in SVG_FONT_RE.finditer(text)]
    _check_min(findings, sizes, opts["min_pt"], "最小字号", "fail")
    strokes = [float(m.group(1)) * unit_pt for m in SVG_STROKE_RE.finditer(text) if float(m.group(1)) > 0]
    _check_min(findings, strokes, opts["min_line_pt"], "最细线宽", "warn")

    if "<text" not in text:
        _no_text(findings, opts["allow_no_text"], "未检出 <text> 节点")
    elif not sizes:
        _add(findings, "warn", "最小字号", "含文本节点但未检出字号，需人工核对")
    _check_raster(findings, text.count("<image"), opts["allow_raster"], "SVG ")
    if sizes:
        _add(findings, "info", "字号范围", f"{min(sizes):.2f}—{max(sizes):.2f} pt（已按 viewBox 换算）")
    return findings


def _pdf_fonts(document) -> dict[str, tuple[str, str]]:
    fonts: dict[str, tuple[str, str]] = {}
    for page in document:
        for _xref, ext, ftype, basefont, *_rest in page.get_fonts(full=True):
            fonts[basefont.split("+")[-1] or "(无名)"] = (ftype, ext)
    return fonts


def _check_pdf_fonts(findings: list[dict], fonts: dict[str, tuple[str, str]]) -> None:
    type3 = sorted(name for name, (ftype, _ext) in fonts.items() if ftype == "Type3")
    missing = sorted(name for name, (ftype, ext) in fonts.items() if ext == "n/a" and ftype != "Type3")
    if type3:
        _add(findings, "fail", "字体类型",
             f"Type 3 字体：{', '.join(type3)}；投稿系统常拒收且不可编辑，设 pdf.fonttype=42 重导出")
    if missing:
        _add(findings, "fail", "字体嵌入", f"未嵌入字体：{', '.join(missing)}；换可嵌入字体重导出")
    if fonts:
        _add(findings, "info", "字体清单", ", ".join(f"{n}({t})" for n, (t, _e) in sorted(fonts.items())))


def _pdf_page_metrics(page) -> tuple[list[float], list[float], int]:
    sizes = [float(span.get("size", 0.0))
             for block in page.get_text("dict").get("blocks", [])
             for line in block.get("lines", []) for span in line.get("spans", [])]
    strokes = [float(d["width"]) for d in page.get_drawings() if d.get("width")]
    return sizes, strokes, len(page.get_images(full=True))


def _lint_pdf(path: Path, opts: dict) -> list[dict]:
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
        sizes, strokes, images = [], [], 0
        for number, page in enumerate(document, start=1):
            where = "页面" if document.page_count == 1 else f"第 {number} 页"
            _check_width(findings, page.rect.width * MM_PER_INCH / PT_PER_INCH, opts["width_mm"], where)
            page_sizes, page_strokes, page_images = _pdf_page_metrics(page)
            sizes += page_sizes
            strokes += page_strokes
            images += page_images
        fonts = _pdf_fonts(document)
    finally:
        document.close()
    _check_min(findings, sizes, opts["min_pt"], "最小字号", "fail")
    _check_min(findings, strokes, opts["min_line_pt"], "最细线宽", "warn")
    _check_pdf_fonts(findings, fonts)
    if not sizes and not fonts:
        _no_text(findings, opts["allow_no_text"], "未检出可编辑文字与字体")
    _check_raster(findings, images, opts["allow_raster"], "PDF ")
    return findings


def _lint_eps(path: Path, opts: dict) -> list[dict]:
    data = path.read_bytes()
    findings: list[dict] = []
    bbox = EPS_BBOX_RE.search(data)
    if bbox:
        x0, _y0, x1, _y1 = (int(v) for v in bbox.groups())
        _check_width(findings, (x1 - x0) * MM_PER_INCH / PT_PER_INCH, opts["width_mm"], "EPS ")
    else:
        _add(findings, "warn", "画布尺寸", "未找到 %%BoundingBox，无法核对宽度")
    if b"/FontType 3" in data:
        _add(findings, "fail", "字体类型", "含 Type 3 字体；设 ps.fonttype=42 重导出")
    if b"/FontType" not in data:
        _no_text(findings, opts["allow_no_text"], "未检出嵌入字体")
    _add(findings, "info", "未查项", "EPS 不查字号与线宽，以同源 PDF 或 SVG 的自检为准")
    return findings


def _lint_raster(path: Path, opts: dict) -> list[dict]:
    try:
        from PIL import Image
    except ImportError:
        raise RuntimeError("缺少 Pillow，无法检查位图；请先安装 Pillow（pip install pillow）")
    findings: list[dict] = []
    with Image.open(path) as image:
        px_width = image.size[0]
        dpi_meta = image.info.get("dpi")
    min_dpi = opts["min_dpi"]
    if opts["width_mm"]:
        effective = px_width / (opts["width_mm"] / MM_PER_INCH)
        if effective < min_dpi:
            _add(findings, "warn", "有效分辨率",
                 f"{px_width} px 在 {opts['width_mm']:g} mm 宽度下约 {effective:.0f} dpi，低于 {min_dpi:g} dpi")
    elif dpi_meta:
        if float(dpi_meta[0]) < min_dpi:
            _add(findings, "warn", "有效分辨率", f"按元数据 {float(dpi_meta[0]):.0f} dpi，低于 {min_dpi:g} dpi")
    else:
        _add(findings, "warn", "有效分辨率", "未给宽度且无 dpi 元数据，无法核对实际分辨率")
    if not opts["allow_raster"]:
        _add(findings, "warn", "矢量纯度", "位图：线稿与文字不可再编辑（照片类图件用 --allow-raster）")
    return findings


LINTERS = {".svg": _lint_svg, ".pdf": _lint_pdf, ".eps": _lint_eps,
           ".png": _lint_raster, ".tif": _lint_raster, ".tiff": _lint_raster}


def profile_options(name: str, columns: str = "single", path: Path = PROFILES_PATH) -> dict:
    """从期刊预设推出检查参数。"""
    profiles = json.loads(Path(path).read_text(encoding="utf-8"))["profiles"]
    if name not in profiles:
        raise ValueError(f"未知期刊预设 {name!r}；可用：{', '.join(sorted(profiles))}")
    spec = profiles[name]
    if columns not in spec["width_mm"]:
        raise ValueError(f"预设 {name} 没有栏宽 {columns!r}；可用：{', '.join(spec['width_mm'])}")
    return {"width_mm": float(spec["width_mm"][columns]), "min_pt": float(spec["font_pt"]["min"]),
            "min_line_pt": float(spec["line_width_pt"]["min"]), "min_dpi": float(spec["dpi"]["line_art"])}


def lint_file(path: str | Path, *, width_mm: float | None = None, min_pt: float = DEFAULT_MIN_PT,
              min_line_pt: float | None = None, min_dpi: float = DEFAULT_MIN_DPI,
              allow_no_text: bool = False, allow_raster: bool = False) -> dict:
    """检查一个导出图件，返回 {file, verdict, findings}；info 级不影响 verdict。"""
    target = Path(path)
    if not target.is_file():
        raise FileNotFoundError(f"文件不存在: {target}")
    linter = LINTERS.get(target.suffix.lower())
    if linter is None:
        raise ValueError(f"不支持的文件类型: {target.suffix or '(无后缀)'}")
    opts = {"width_mm": width_mm, "min_pt": min_pt, "min_line_pt": min_line_pt, "min_dpi": min_dpi,
            "allow_no_text": allow_no_text, "allow_raster": allow_raster}
    findings = linter(target, opts)
    levels = {item["level"] for item in findings}
    verdict = 2 if "fail" in levels else 1 if "warn" in levels else 0
    return {"file": str(target), "verdict": verdict, "findings": findings}


def _render(result: dict) -> str:
    marks = {"fail": "失败", "warn": "警告", "info": "信息"}
    lines = [f"图件自检：{result['file']}"]
    if not any(item["level"] != "info" for item in result["findings"]):
        lines.append("  未发现可机械判定的问题。")
    lines += [f"  [{marks[item['level']]}] {item['check']}：{item['message']}" for item in result["findings"]]
    lines.append({0: "结论：机械项通过；视觉与统计核对仍需人工完成。",
                  1: "结论：有警告，请人工核对后再交付。",
                  2: "结论：未通过，按规则不得交付。"}[result["verdict"]])
    return "\n".join(lines)


def _options(args: argparse.Namespace) -> dict:
    base = profile_options(args.profile, args.columns) if args.profile else {
        "width_mm": None, "min_pt": DEFAULT_MIN_PT, "min_line_pt": None, "min_dpi": DEFAULT_MIN_DPI}
    for key in ("width_mm", "min_pt", "min_line_pt", "min_dpi"):
        if getattr(args, key) is not None:
            base[key] = getattr(args, key)
    return {**base, "allow_no_text": args.allow_no_text, "allow_raster": args.allow_raster}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="科研图件出图机械自检")
    parser.add_argument("files", nargs="+", help="导出图件路径（SVG、PDF、EPS、PNG、TIFF）")
    parser.add_argument("--profile", help="期刊预设名，见 templates/journal_profiles.json")
    parser.add_argument("--columns", default="single", help="预设栏宽名（默认 single）")
    parser.add_argument("--width-mm", type=float, help="目标刊印宽度（毫米），覆盖预设")
    parser.add_argument("--min-pt", type=float, help=f"最小字号下限（默认 {DEFAULT_MIN_PT:g} pt）")
    parser.add_argument("--min-line-pt", type=float, help="最细线宽下限（pt，默认不查）")
    parser.add_argument("--min-dpi", type=float, help=f"位图有效分辨率下限（默认 {DEFAULT_MIN_DPI:g}）")
    parser.add_argument("--allow-raster", action="store_true", help="照片或显微图等允许位图")
    parser.add_argument("--allow-no-text", action="store_true", help="允许图中没有可编辑文字")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args(argv)
    try:
        opts = _options(args)
        results = [lint_file(path, **opts) for path in args.files]
    except (FileNotFoundError, ValueError, RuntimeError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False) if args.json else f"错误：{error}")
        return 2
    if args.json:
        print(json.dumps(results if len(results) > 1 else results[0], ensure_ascii=False, indent=2))
    else:
        print("\n\n".join(_render(result) for result in results))
    return max(result["verdict"] for result in results)


if __name__ == "__main__":
    sys.exit(main())
