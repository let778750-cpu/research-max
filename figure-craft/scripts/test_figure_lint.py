#!/usr/bin/env python3
"""test_figure_lint.py — figure_lint.py 的自测：十项检查用例与配方语法编译。

运行（在本目录）：
    python -m unittest discover -s . -p "test_*.py" -v
"""

from __future__ import annotations

import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from figure_lint import lint_file  # noqa: E402

try:
    import fitz  # noqa: F401
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

try:
    from PIL import Image  # noqa: F401
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def svg_text(body: str, width: str = "89mm", height: str = "60mm") -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 89 60">\n{body}\n</svg>\n'
    )


class FigureLintTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write(self, name: str, content: str) -> Path:
        path = self.dir / name
        path.write_text(content, encoding="utf-8")
        return path

    def checks(self, result: dict) -> set[str]:
        return {item["check"] for item in result["findings"]}

    def test_01_svg_passes(self):
        path = self.write("ok.svg", svg_text('<text x="5" y="10" font-size="6pt">a</text>'))
        result = lint_file(path, width_mm=89)
        self.assertEqual(result["verdict"], 0, result)

    def test_02_svg_small_font_fails(self):
        path = self.write("small.svg", svg_text('<text x="5" y="10" font-size="4pt">a</text>'))
        result = lint_file(path, width_mm=89)
        self.assertEqual(result["verdict"], 2)
        self.assertIn("最小字号", self.checks(result))

    def test_03_svg_text_as_paths_fails(self):
        path = self.write("paths.svg", svg_text('<path d="M0 0 L10 10"/>'))
        result = lint_file(path, width_mm=89)
        self.assertEqual(result["verdict"], 2)
        self.assertIn("文字可编辑", self.checks(result))

    def test_04_svg_allow_no_text(self):
        path = self.write("paths_allowed.svg", svg_text('<path d="M0 0 L10 10"/>'))
        result = lint_file(path, width_mm=89, allow_no_text=True)
        self.assertEqual(result["verdict"], 1)
        self.assertNotIn("文字可编辑", {i["check"] for i in result["findings"] if i["level"] == "fail"})

    def test_05_svg_embedded_raster_warns(self):
        body = '<text x="5" y="10" font-size="6pt">a</text><image href="x.png" width="10" height="10"/>'
        path = self.write("image.svg", svg_text(body))
        result = lint_file(path, width_mm=89)
        self.assertEqual(result["verdict"], 1)
        self.assertIn("矢量纯度", self.checks(result))

    def test_06_svg_width_mismatch_warns(self):
        path = self.write("wide.svg", svg_text('<text x="5" y="10" font-size="6pt">a</text>', width="183mm"))
        result = lint_file(path, width_mm=89)
        self.assertEqual(result["verdict"], 1)
        self.assertIn("画布尺寸", self.checks(result))

    @unittest.skipUnless(HAS_PIL, "需要 Pillow")
    def test_07_png_low_dpi_warns(self):
        path = self.dir / "low.png"
        Image.new("RGB", (400, 300)).save(path, dpi=(300, 300))
        result = lint_file(path, width_mm=89)
        self.assertEqual(result["verdict"], 1)
        self.assertIn("有效分辨率", self.checks(result))

    @unittest.skipUnless(HAS_PIL, "需要 Pillow")
    def test_08_png_high_dpi_has_no_resolution_warning(self):
        path = self.dir / "high.png"
        Image.new("RGB", (1200, 800)).save(path, dpi=(300, 300))
        result = lint_file(path, width_mm=89)
        self.assertNotIn("有效分辨率", self.checks(result))
        self.assertEqual(result["verdict"], 1)  # 位图本身仍给矢量纯度警告

    @unittest.skipUnless(HAS_FITZ, "需要 PyMuPDF")
    def test_09_pdf_small_font_fails(self):
        path = self.dir / "tiny.pdf"
        document = fitz.open()
        page = document.new_page(width=89 / 25.4 * 72, height=60 / 25.4 * 72)
        page.insert_text((10, 20), "tiny", fontsize=4)
        document.save(path)
        document.close()
        result = lint_file(path, width_mm=89)
        self.assertEqual(result["verdict"], 2)
        self.assertIn("最小字号", self.checks(result))

    @unittest.skipUnless(HAS_FITZ, "需要 PyMuPDF")
    def test_10_pdf_width_mismatch_warns(self):
        path = self.dir / "a4.pdf"
        document = fitz.open()
        page = document.new_page()
        page.insert_text((10, 20), "text", fontsize=6)
        document.save(path)
        document.close()
        result = lint_file(path, width_mm=89)
        self.assertEqual(result["verdict"], 1)
        self.assertIn("画布尺寸", self.checks(result))

    def test_11_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            lint_file(self.dir / "nope.svg", width_mm=89)

    def test_12_unsupported_suffix_raises(self):
        path = self.write("note.txt", "x")
        with self.assertRaises(ValueError):
            lint_file(path)

    def test_13_json_shape(self):
        path = self.write("shape.svg", svg_text('<text x="5" y="10" font-size="6pt">a</text>'))
        result = lint_file(path, width_mm=89)
        self.assertEqual(set(result), {"file", "verdict", "findings"})
        self.assertIsInstance(result["findings"], list)

    def test_14_recipes_compile(self):
        recipes = Path(__file__).resolve().parent.parent / "templates" / "绘图配方示例.md"
        text = recipes.read_text(encoding="utf-8")
        blocks = re.findall(r"```python\n(.*?)```", text, re.S)
        self.assertGreaterEqual(len(blocks), 5, "配方示例少于 5 段")
        for index, block in enumerate(blocks, start=1):
            with self.subTest(block=index):
                compile(block, f"<recipe-{index}>", "exec")


if __name__ == "__main__":
    unittest.main()
