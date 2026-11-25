#!/usr/bin/env python3
"""figstyle.py — 按期刊预设设置 matplotlib 样式，出矢量图、预览、灰度预览与溯源清单。

唯一数据源是 templates/journal_profiles.json；templates/styles/*.mplstyle 由本脚本
--write-styles 生成，不手改。规则说明见 references/期刊与学位论文版式预设.md（FIG9）
与 references/导出、自检与图注.md（FIG10—FIG11）。

库用法：
  import figstyle
  with figstyle.profile_context("aiaa", width="single") as size:
      fig, ax = plt.subplots(figsize=size)
      ...
      figstyle.save_figure(fig, "out/fig1", profile="aiaa", sources=["data/x.csv"])

命令行：
  python figstyle.py --list | --fonts | --write-styles | --check-styles
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import platform
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

HERE = Path(__file__).resolve().parent
PROFILES_PATH = HERE.parent / "templates" / "journal_profiles.json"
STYLES_DIR = HERE.parent / "templates" / "styles"
MM_PER_IN = 25.4
GOLDEN = 0.618
FALLBACK_LATIN = ["DejaVu Sans"]
# Okabe-Ito 色盲友好配色；黄色放最后，因白底上对比度最低。
OKABE_ITO = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#000000", "#F0E442"]
MANIFEST_RC_KEYS = ("font.family", "font.size", "mathtext.fontset", "pdf.fonttype",
                    "svg.fonttype", "lines.linewidth", "axes.linewidth", "savefig.dpi")
PGF_PREAMBLE = "\n".join([
    r"\usepackage{fontspec}",
    r"\usepackage[UTF8,fontset=none]{ctex}",
    r"\setmainfont{Times New Roman}",
    r"\setCJKmainfont{SimSun}",
    r"\usepackage{unicode-math}",
    r"\setmathfont{STIX Two Math}",
])


def load_profiles(path: Path = PROFILES_PATH) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    profiles = data.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        raise ValueError(f"{path} 缺少 profiles 字段")
    return profiles


def get_profile(name: str, path: Path = PROFILES_PATH) -> dict:
    profiles = load_profiles(path)
    if name not in profiles:
        raise KeyError(f"未知期刊预设 {name!r}；可用：{', '.join(sorted(profiles))}")
    return profiles[name]


def installed_fonts() -> set[str]:
    from matplotlib import font_manager
    return {entry.name for entry in font_manager.fontManager.ttflist}


def resolve_family(profile: dict, lang: str | None = None) -> list[str]:
    """按优先级保留已安装字体：西文在前、中文在后，matplotlib 逐字形回退。"""
    have = installed_fonts()
    latin = [f for f in profile.get("font_family", []) if f in have] or FALLBACK_LATIN
    if (lang or profile.get("lang")) != "zh":
        return latin
    cjk = [f for f in profile.get("cjk_family", []) if f in have]
    if not cjk:
        warnings.warn("未找到预设中的中文字体，中文会显示为方块；安装宋体类字体或改用英文标签",
                      stacklevel=2)
    return latin + cjk


def figure_size(profile: dict, width: str | float = "single", height_mm: float | None = None,
                aspect: float = GOLDEN) -> tuple[float, float]:
    """返回英寸 (宽, 高)。width 可为预设栏名或毫米数；高默认为宽 × aspect。"""
    widths = profile["width_mm"]
    if isinstance(width, str):
        if width not in widths:
            raise KeyError(f"预设没有栏宽 {width!r}；可用：{', '.join(widths)}")
        width_mm = float(widths[width])
    else:
        width_mm = float(width)
    height = float(height_mm) if height_mm is not None else width_mm * aspect
    limit = profile.get("max_height_mm")
    if limit and height > limit:
        raise ValueError(f"图高 {height:.0f} mm 超过预设页深 {limit} mm")
    return width_mm / MM_PER_IN, height / MM_PER_IN


def profile_rc(profile: dict, lang: str | None = None, pgf: bool = False,
               families: list[str] | None = None) -> dict:
    from cycler import cycler
    size = profile["font_pt"]["base"]
    lines = profile["line_width_pt"]
    rc = {
        "font.family": families if families is not None else resolve_family(profile, lang),
        "font.size": size, "axes.labelsize": size, "axes.titlesize": size,
        "xtick.labelsize": size, "ytick.labelsize": size, "legend.fontsize": size,
        "mathtext.fontset": profile.get("math_fontset", "dejavusans"),
        "axes.unicode_minus": True,
        "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
        "figure.constrained_layout.use": True, "savefig.bbox": None,
        "savefig.dpi": profile["dpi"]["combination"], "figure.dpi": 100,
        "lines.linewidth": lines["data"], "axes.linewidth": lines["axes"],
        "xtick.major.width": lines["axes"], "ytick.major.width": lines["axes"],
        "xtick.minor.width": lines["min"], "ytick.minor.width": lines["min"],
        "grid.linewidth": lines["min"], "patch.linewidth": lines["axes"],
        "axes.spines.top": False, "axes.spines.right": False,
        "xtick.direction": "out", "ytick.direction": "out",
        "legend.frameon": False, "axes.grid": False, "image.cmap": "viridis",
        "axes.prop_cycle": cycler(color=OKABE_ITO),
    }
    if pgf:
        rc.update({"pgf.texsystem": "xelatex", "pgf.rcfonts": False, "pgf.preamble": PGF_PREAMBLE,
                   "text.usetex": False})
    return rc


def apply_profile(name: str, width: str | float = "single", height_mm: float | None = None,
                  aspect: float = GOLDEN, lang: str | None = None, pgf: bool = False):
    """全局套用预设（改 matplotlib.rcParams），返回 (rc, figsize)。脚本出图用；测试与库内用 profile_context。"""
    profile = get_profile(name)
    rc = profile_rc(profile, lang=lang, pgf=pgf)
    matplotlib.rcParams.update(rc)
    return rc, figure_size(profile, width, height_mm, aspect)


@contextlib.contextmanager
def profile_context(name: str, width: str | float = "single", height_mm: float | None = None,
                    aspect: float = GOLDEN, lang: str | None = None, pgf: bool = False):
    """只在 with 块内生效的预设，产出 figsize。"""
    profile = get_profile(name)
    with matplotlib.rc_context(profile_rc(profile, lang=lang, pgf=pgf)):
        yield figure_size(profile, width, height_mm, aspect)


def add_panel_labels(axes, profile: str | dict | None = None, start: int = 0) -> list[str]:
    """按预设给多面板加标号：Nature 为粗体小写 a，其余为 (a)。放在面板左上，随约束布局避让。"""
    spec = get_profile(profile) if isinstance(profile, str) else (profile or {})
    style = spec.get("panel_label", "(a)")
    size = spec.get("font_pt", {}).get("panel_label")
    labels = []
    for index, ax in enumerate(list(axes)):
        letter = chr(ord("a") + start + index)
        text = letter if style == "a" else f"({letter})"
        weight = "bold" if style == "a" else "normal"
        ax.set_title(text, loc="left", fontweight=weight, fontsize=size)
        labels.append(text)
    return labels


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _file_entry(path: Path) -> dict:
    return {"path": path.name, "bytes": path.stat().st_size, "sha256": _sha256(path)}


def _source_entry(item: str | Path) -> dict:
    path = Path(item)
    if path.is_file():
        return {"path": str(item), "sha256": _sha256(path)}
    return {"path": str(item), "sha256": None, "note": "文件不存在或非本地路径，未计哈希"}


def _save_vector(fig, path: Path, fmt: str, raster_dpi: int) -> None:
    if fmt in {"tif", "tiff"}:
        fig.savefig(path, dpi=raster_dpi, pil_kwargs={"compression": "tiff_lzw"})
    elif fmt == "pgf":
        try:
            fig.savefig(path, backend="pgf")
        except (RuntimeError, OSError) as error:
            raise RuntimeError(f"PGF 导出失败（需 xelatex 在 PATH 上）：{error}") from error
    else:
        fig.savefig(path)


def _save_previews(fig, stem: Path, dpi: int, grayscale: bool) -> list[Path]:
    from PIL import Image
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=dpi)
    preview = stem.with_name(stem.name + ".preview.png")
    preview.write_bytes(buffer.getvalue())
    written = [preview]
    if grayscale:
        buffer.seek(0)
        gray = stem.with_name(stem.name + ".gray.png")
        with Image.open(buffer) as image:
            image.convert("L").save(gray)
        written.append(gray)
    return written


def save_figure(fig, stem: str | Path, formats=("pdf", "svg"), preview_dpi: int = 300,
                grayscale: bool = True, profile: str | None = None, sources=(),
                script: str | Path | None = None, raster_dpi: int | None = None) -> dict:
    """按格式导出，另出预览与灰度预览，写 <stem>.manifest.json 并返回清单。

    不使用 bbox_inches="tight"：画布尺寸必须等于预设栏宽，裁切交给约束布局。
    """
    stem = Path(stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    spec = get_profile(profile) if profile else None
    dpi = raster_dpi or (spec["dpi"]["line_art"] if spec else 600)
    written = []
    for fmt in formats:
        path = stem.with_suffix("." + fmt.lower())
        _save_vector(fig, path, fmt.lower(), dpi)
        written.append(path)
    written += _save_previews(fig, stem, preview_dpi, grayscale)
    manifest = {
        "figure": stem.name,
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "profile": profile,
        "figsize_mm": [round(v * MM_PER_IN, 2) for v in fig.get_size_inches()],
        "files": [_file_entry(p) for p in written],
        "rc": {key: _jsonable(matplotlib.rcParams[key]) for key in MANIFEST_RC_KEYS},
        "versions": _versions(),
        "script": _source_entry(script) if script else None,
        "sources": [_source_entry(item) for item in sources],
    }
    out = stem.with_name(stem.name + ".manifest.json")
    out.write_bytes(json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8"))
    return manifest


def _jsonable(value):
    return list(value) if isinstance(value, (list, tuple)) else value


def _versions() -> dict:
    import numpy
    return {"python": platform.python_version(), "matplotlib": matplotlib.__version__,
            "numpy": numpy.__version__}


# ---------- mplstyle 生成（styles 目录只由此处写入） ----------

def _style_value(value) -> str:
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    if value is None:
        return "standard"
    return str(value)


def style_text(name: str, profile: dict, pgf: bool = False) -> str:
    families = profile.get("font_family", []) + profile.get("cjk_family", [])
    rc = profile_rc(profile, pgf=pgf, families=families)
    rc.pop("axes.prop_cycle")
    rc.pop("pgf.preamble", None)
    header = [f"# {profile['name']}（{name}）。由 scripts/figstyle.py --write-styles 从",
              "# templates/journal_profiles.json 生成，勿手改；栏宽与图高用 figstyle.figure_size。",
              "# 字体列表含未安装项时 matplotlib 会告警并跳过；中文字体在西文之后，逐字形回退。"]
    if pgf:
        header.append("# PGF 路线：pgf.preamble 无法写入 mplstyle，用 figstyle.apply_profile(..., pgf=True)。")
    body = [f"{key}: {_style_value(value)}" for key, value in rc.items()]
    colors = ", ".join(f"'{c.lstrip('#')}'" for c in OKABE_ITO)
    body.append(f"axes.prop_cycle: cycler('color', [{colors}])")
    return "\n".join(header + body) + "\n"


def expected_styles() -> dict[str, str]:
    profiles = load_profiles()
    styles = {f"{name}.mplstyle": style_text(name, spec) for name, spec in profiles.items()}
    if "thesis" in profiles:
        styles["thesis-pgf.mplstyle"] = style_text("thesis", profiles["thesis"], pgf=True)
    return styles


def write_styles() -> list[Path]:
    STYLES_DIR.mkdir(parents=True, exist_ok=True)
    written = []
    for filename, text in expected_styles().items():
        path = STYLES_DIR / filename
        path.write_bytes(text.encode("utf-8"))
        written.append(path)
    return written


def stale_styles() -> list[str]:
    stale = []
    for filename, text in expected_styles().items():
        path = STYLES_DIR / filename
        if not path.is_file() or path.read_text(encoding="utf-8") != text:
            stale.append(filename)
    return stale


def _font_report() -> str:
    have = installed_fonts()
    lines = []
    for name, spec in load_profiles().items():
        wanted = spec.get("font_family", []) + spec.get("cjk_family", [])
        marks = [f"{f}{'✓' if f in have else '✗'}" for f in wanted]
        lines.append(f"{name:12s} {' '.join(marks)}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="期刊版式预设：列出、查字体、生成或核对 mplstyle")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true", help="列出预设与栏宽")
    group.add_argument("--fonts", action="store_true", help="逐预设报告候选字体是否已安装")
    group.add_argument("--write-styles", action="store_true", help="从 JSON 重新生成 styles/*.mplstyle")
    group.add_argument("--check-styles", action="store_true", help="styles 与 JSON 不一致时退出码 1")
    args = parser.parse_args(argv)
    if args.list:
        for name, spec in load_profiles().items():
            widths = ", ".join(f"{k}={v}" for k, v in spec["width_mm"].items())
            mark = "已核实" if spec.get("verified", {}).get("fields") else "未核实"
            print(f"{name:12s} {spec['name']}；{widths} mm；{spec['font_pt']['base']} pt；{mark}")
    elif args.fonts:
        print(_font_report())
    elif args.write_styles:
        for path in write_styles():
            print(f"写入 {path.name}")
    else:
        stale = stale_styles()
        print("styles 与 JSON 一致" if not stale else f"需重新生成：{', '.join(stale)}")
        return 1 if stale else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
