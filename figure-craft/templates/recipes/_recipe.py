"""配方公共件：命令行参数、导入 scripts 下的工具、双语标签、出图前版面与配色自检。

每个配方都可直接运行：
  python <配方>.py [--profile aiaa|ieee|elsevier|nature|cn-journal|thesis] [--width single|double]
                   [--lang zh|en] [--out 目录] [--formats pdf,svg]
配方里的数据全部是示例数据（固定随机种子生成），用于演示图型；换成真实数据时保留
图型结构与自检步骤，并在 save 的 sources 中登记真实数据文件，以便清单记录哈希。
退出码：0=版面自检通过；1=有警告；2=有失败。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import figstyle  # noqa: E402
import layout_audit  # noqa: E402
import palette_audit  # noqa: E402

EXAMPLE_SOURCE = "示例数据（配方内固定随机种子生成，非真实结果）"


def parse_args(description: str, default_width: str = "single") -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--profile", default="aiaa", help="期刊预设名")
    parser.add_argument("--width", default=default_width, help="栏宽名：single / double / onehalf 等")
    parser.add_argument("--lang", choices=["zh", "en"], help="标签语言，默认按预设")
    parser.add_argument("--out", default="out", help="输出目录")
    parser.add_argument("--formats", default="pdf,svg", help="导出格式，逗号分隔")
    args = parser.parse_args()
    args.lang = args.lang or figstyle.get_profile(args.profile).get("lang", "en")
    return args


def text(args: argparse.Namespace, zh: str, en: str) -> str:
    """按语言取标签。中文标签里的变量与单位仍用西文，如「时间 t / s」。"""
    return zh if args.lang == "zh" else en


def context(args: argparse.Namespace, height_mm: float | None = None, aspect: float = figstyle.GOLDEN):
    return figstyle.profile_context(args.profile, width=args.width, height_mm=height_mm,
                                    aspect=aspect, lang=args.lang)


def finish(fig, args: argparse.Namespace, name: str, script: str, sources=(EXAMPLE_SOURCE,)) -> int:
    """保存前做版面自检与配色提示，再导出矢量、预览、灰度预览与清单；须在 context 内调用。"""
    profile = figstyle.get_profile(args.profile)
    audit = layout_audit.audit_figure(fig, min_pt=profile["font_pt"]["min"])
    print(layout_audit.render(audit, name))
    colors = palette_audit.colors_in_figure(fig)
    if len(colors) >= 2:
        for item in palette_audit.audit_palette(colors)["findings"]:
            print(f"  [配色提示] {item['check']}：{item['message']}")
    formats = tuple(f.strip() for f in args.formats.split(",") if f.strip())
    manifest = figstyle.save_figure(fig, Path(args.out) / name, formats=formats,
                                    profile=args.profile, script=script, sources=sources)
    print("  已写出：" + "，".join(entry["path"] for entry in manifest["files"]))
    return audit["verdict"]
