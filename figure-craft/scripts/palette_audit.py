#!/usr/bin/env python3
"""palette_audit.py — 配色自检：灰度明度区分（CIELAB ΔL*）、色觉模拟区分（Machado 2009，ΔE76）、与背景的对比度（WCAG）。

只做确定性计算，不改图。阈值是经验起点，判据与取舍见 references/多面板、配色与刊印版式.md（FIG8）：
灰度或色觉下不可区分的配对，要么换色，要么用线型、标记、直接标注做冗余编码。

用法（建议设置 PYTHONUTF8=1）：
  python palette_audit.py --palette okabe-ito
  python palette_audit.py "#0072B2" "#D55E00" "#009E73" [--background "#FFFFFF"] [--json]
库用法：audit_palette(colors) / colors_in_figure(fig)
退出码：0=通过；1=有警告；2=输入错误。
"""

from __future__ import annotations

import argparse
import json
import sys
from itertools import combinations

import numpy as np

PALETTES = {
    "okabe-ito": ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#000000", "#F0E442"],
    "tol-bright": ["#4477AA", "#EE6677", "#228833", "#CCBB44", "#66CCEE", "#AA3377", "#BBBBBB"],
    "tol-vibrant": ["#0077BB", "#33BBEE", "#009988", "#EE7733", "#CC3311", "#EE3377", "#BBBBBB"],
}
GRAY_DELTA_L_MIN = 10.0     # 灰度打印下两色明度差下限（L* 单位）
CVD_DELTA_E_MIN = 10.0      # 色觉模拟后两色色差下限（ΔE76）
CONTRAST_GRAPHIC_MIN = 3.0  # WCAG 2.1 非文本对比度；文字为 4.5
# Machado, Oliveira & Fernandes (2009) 严重度 1.0 矩阵，作用于线性 RGB
CVD_MATRICES = {
    "红色盲": np.array([[0.152286, 1.052583, -0.204868], [0.114503, 0.786281, 0.099216],
                       [-0.003882, -0.048116, 1.051998]]),
    "绿色盲": np.array([[0.367322, 0.860646, -0.227968], [0.280085, 0.672501, 0.047413],
                       [-0.011820, 0.042940, 0.968881]]),
    "蓝色盲": np.array([[1.255528, -0.076749, -0.178779], [-0.078411, 0.930809, 0.147602],
                       [0.004733, 0.691367, 0.303900]]),
}
D65_WHITE = np.array([0.95047, 1.0, 1.08883])
SRGB_TO_XYZ = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750],
                        [0.0193339, 0.1191920, 0.9503041]])


def to_rgb(color) -> np.ndarray:
    from matplotlib.colors import to_rgb as mpl_to_rgb
    return np.array(mpl_to_rgb(color), dtype=float)


def srgb_to_linear(rgb: np.ndarray) -> np.ndarray:
    return np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)


def linear_to_lab(linear: np.ndarray) -> np.ndarray:
    xyz = SRGB_TO_XYZ @ np.clip(linear, 0.0, 1.0) / D65_WHITE
    f = np.where(xyz > (6 / 29) ** 3, np.cbrt(xyz), xyz / (3 * (6 / 29) ** 2) + 4 / 29)
    return np.array([116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])])


def relative_luminance(rgb: np.ndarray) -> float:
    return float(np.dot([0.2126, 0.7152, 0.0722], srgb_to_linear(rgb)))


def contrast_ratio(a: np.ndarray, b: np.ndarray) -> float:
    la, lb = sorted((relative_luminance(a), relative_luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def _close_pairs(names: list[str], values: list[np.ndarray], limit: float, metric) -> list[tuple]:
    pairs = []
    for (i, a), (j, b) in combinations(enumerate(values), 2):
        distance = metric(a, b)
        if distance < limit:
            pairs.append((names[i], names[j], round(float(distance), 1)))
    return pairs


def audit_palette(colors, background="#FFFFFF", gray_min: float = GRAY_DELTA_L_MIN,
                  cvd_min: float = CVD_DELTA_E_MIN, contrast_min: float = CONTRAST_GRAPHIC_MIN) -> dict:
    """返回 {verdict, findings, lightness}；verdict 0=通过 1=警告。"""
    names = [str(c) for c in colors]
    rgbs = [to_rgb(c) for c in colors]
    labs = [linear_to_lab(srgb_to_linear(rgb)) for rgb in rgbs]
    findings: list[dict] = []
    gray = _close_pairs(names, labs, gray_min, lambda a, b: abs(a[0] - b[0]))
    if gray:
        findings.append({"level": "warn", "check": "灰度区分",
                         "message": f"ΔL* < {gray_min:g} 的配对：{_fmt(gray)}；灰度打印需线型或标记冗余"})
    for kind, matrix in CVD_MATRICES.items():
        simulated = [linear_to_lab(matrix @ srgb_to_linear(rgb)) for rgb in rgbs]
        close = _close_pairs(names, simulated, cvd_min, lambda a, b: np.linalg.norm(a - b))
        if close:
            findings.append({"level": "warn", "check": f"色觉模拟（{kind}）",
                             "message": f"ΔE < {cvd_min:g} 的配对：{_fmt(close)}"})
    back = to_rgb(background)
    low = [(n, round(contrast_ratio(rgb, back), 2)) for n, rgb in zip(names, rgbs)
           if contrast_ratio(rgb, back) < contrast_min]
    if low:
        findings.append({"level": "warn", "check": "背景对比度",
                         "message": f"对 {background} 低于 {contrast_min:g}:1：" +
                                    "，".join(f"{n}={r}" for n, r in low) + "；细线与小标记改深色或加描边"})
    return {"verdict": 1 if findings else 0, "findings": findings,
            "lightness": {n: round(float(lab[0]), 1) for n, lab in zip(names, labs)}}


def _fmt(pairs: list[tuple]) -> str:
    shown = "，".join(f"{a}/{b}({d})" for a, b, d in pairs[:6])
    return shown + (f" 等 {len(pairs)} 对" if len(pairs) > 6 else "")


def colors_in_figure(fig) -> list[str]:
    """提取图中线、散点、填充面的去重颜色（十六进制），供 audit_palette 使用。"""
    from matplotlib.colors import to_hex
    seen: list[str] = []

    def add(color) -> None:
        try:
            value = to_hex(color, keep_alpha=False)
        except ValueError:
            return
        if value not in seen:
            seen.append(value)

    for ax in fig.axes:
        for line in ax.get_lines():
            add(line.get_color())
        for collection in ax.collections:
            for face in collection.get_facecolors()[:1]:
                add(face)
        for patch in ax.patches:
            add(patch.get_facecolor())
    return [c for c in seen if c not in {"#ffffff"}]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="配色灰度、色觉与对比度自检")
    parser.add_argument("colors", nargs="*", help="颜色（十六进制或 matplotlib 颜色名）")
    parser.add_argument("--palette", choices=sorted(PALETTES), help="内置色板")
    parser.add_argument("--background", default="#FFFFFF", help="背景色（默认白）")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args(argv)
    colors = list(PALETTES[args.palette]) if args.palette else []
    colors += args.colors
    if len(colors) < 2:
        print("错误：至少给两种颜色或一个 --palette")
        return 2
    try:
        result = audit_palette(colors, background=args.background)
    except ValueError as error:
        print(f"错误：{error}")
        return 2
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("明度 L*：" + "，".join(f"{n}={v}" for n, v in result["lightness"].items()))
        for item in result["findings"]:
            print(f"  [警告] {item['check']}：{item['message']}")
        print("结论：" + ("配色机械项通过。" if not result["findings"] else "有警告，按 FIG8 换色或加冗余编码。"))
    return result["verdict"]


if __name__ == "__main__":
    sys.exit(main())
