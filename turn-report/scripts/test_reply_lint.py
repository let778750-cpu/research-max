#!/usr/bin/env python3
"""test_reply_lint.py — reply_lint.py 的自测：十五个正反例。

运行（在本目录）：
    python -m unittest discover -s . -p "test_*.py" -v
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from reply_lint import lint_text, load_allow  # noqa: E402

GOOD_SAMPLE = """\
**结论：这批报告只回答一个问题——"先把拍照排满、再安排下传"会亏多少。同一批 72 单、总权重 440 分，顺序拿 160 分，联合拿 256 分。**

- 亏的原因可数：顺序拍了 43 单，只有 22 单按期把字节收齐，21 单白拍还占时隙（`results/summary.json`）。
- 平均权重几乎一样（7.27 vs 7.31 分/单），所以联合不是挑大单，是只挑传得下来的。
- "最优"只在枚举的 1,568 个候选内成立；新 UTC（协调世界时）历元组联合 243 分、上界 297，是 12 秒限时的整数规划解（`static_summary.csv` 的 `status=timeout_feasible`）。
- 硬件比算法更左右结论：离轴角上限 50°→30°，联合从 35 单/256 分掉到 17 单/110 分（`payload_angle_orders.csv`）。
- 加姿态与实时下传只多 2 单、1 单：姿态让计划"能执行"，实时才让订单"多交付"（`attitude_live/summary.json`）。

**边界与未做**：全部为仿真；15 颗星不是真实星座；实星参数只核到公开资料与 5 个真实条带的外部几何；我没有重跑测试与求解。

**下一步（可选）**：补 O005/O039/O008 三条证据链；多 Agent 对照尚未运行。
"""

HEDGED_SAMPLE = """\
我理解你的问题。你遇到的并不是完成任务的技术能力不足，而是报告组织时的表达方式问题。

需要注意的是，这一判断在一定程度上依赖于若干假设，不能完全排除其他解释，可能存在偏差。综上所述，建议进一步核实相关情况。以上仅供参考，希望能帮到你，如有需要我可以继续分析。
"""

LIMITS_ONLY = """\
## 边界与未做

未运行真实模型；不能完全排除参数取值带来的差异；缓存与功耗未实测。
"""

CODE_BLOCK = """\
```text
综上所述，以上内容仅供参考。
```

结论：窗口筛选已修复（`geometry.py:88`），漏窗从 6 降到 0。
"""

TABLE_ROW = """\
结论：改完（`store.py:203`）。

| 项 | 说明 |
|---|---|
| 鲁棒性 | 已提升，协同能力形成闭环 |
"""

LONG_NO_ANCHOR = "这次改动集中在状态保存与恢复两条路径上。恢复时先校验快照版本，再决定是否重放命令。" * 18

BARE_ACRONYM = "结论：整数规划在十二秒内返回可行解（`summary.json`）。MILP 只覆盖已枚举的候选组合。"

DEFINED_ACRONYM = (
    "结论：混合整数线性规划（Mixed-Integer Linear Programming, MILP）在十二秒内返回可行解；"
    "MILP 只覆盖已枚举的候选（`summary.json`）。"
)

WHITELIST_SAMPLE = "结论：几何核对通过（`geo.py:12`）。坐标用 WGS84，速率上限 450 Mbps，字段在 `obsbase.contracts`。"

ALLOW_SAMPLE = "结论：先用大邻域搜索重排，再回放校验（`plans.csv`）。LNS 共运行 3 次。"

FILENAME_SAMPLE = "结论：按 README 与 AGENTS 的分工改完，SKILL 与 3 处引用同步到 SOURCES 与 TASKS（`docs.md`）。"

RULE_LABEL_SAMPLE = "结论：按 FIG4 与 FIG11 核对误差定义与图注（`a.md`），FIG1 的契约已填。"


class ReplyLintTest(unittest.TestCase):
    def test_01_good_sample_passes(self):
        result = lint_text(GOOD_SAMPLE)
        self.assertEqual(result["verdict"], 0, [c["message"] for c in result["checks"]])

    def test_02_hedged_sample_fails(self):
        result = lint_text(HEDGED_SAMPLE)
        self.assertEqual(result["verdict"], 2)
        ids = {c["id"] for c in result["checks"] if c["level"] == "fail"}
        self.assertTrue({"R1", "R2", "R4"} & ids, ids)

    def test_03_limits_section_not_counted(self):
        result = lint_text(LIMITS_ONLY)
        self.assertEqual(result["verdict"], 0, [c["message"] for c in result["checks"]])

    def test_04_code_block_ignored(self):
        result = lint_text(CODE_BLOCK)
        self.assertEqual(result["verdict"], 0, [c["message"] for c in result["checks"]])

    def test_05_table_row_ignored(self):
        result = lint_text(TABLE_ROW)
        self.assertEqual(result["verdict"], 0, [c["message"] for c in result["checks"]])

    def test_06_long_text_without_anchor_warns(self):
        result = lint_text(LONG_NO_ANCHOR)
        self.assertEqual(result["verdict"], 1)
        checks = {c["id"]: c for c in result["checks"]}
        self.assertEqual(checks["R5"]["level"], "warn")

    def test_07_empty_input_is_safe(self):
        result = lint_text("   \n\n ")
        self.assertEqual(result["verdict"], 0)
        self.assertEqual(result["checks"][0]["id"], "R0")

    def test_08_json_shape(self):
        result = lint_text(GOOD_SAMPLE)
        self.assertEqual(set(result), {"verdict", "verdict_text", "stats", "checks"})
        self.assertIn("cjk", result["stats"])
        self.assertIn("density_per_kcjk", result["stats"])
        self.assertTrue(all({"id", "name", "level", "message", "hits"} <= set(c) for c in result["checks"]))

    def test_09_bare_acronym_warns(self):
        result = lint_text(BARE_ACRONYM)
        self.assertEqual(result["verdict"], 1)
        r7 = next(c for c in result["checks"] if c["id"] == "R7")
        self.assertEqual(r7["level"], "warn")
        self.assertIn("MILP", r7["hits"])

    def test_10_defined_acronym_passes(self):
        result = lint_text(DEFINED_ACRONYM)
        r7 = next(c for c in result["checks"] if c["id"] == "R7")
        self.assertEqual(r7["level"], "pass", r7["message"])

    def test_11_units_paths_and_known_names_ignored(self):
        result = lint_text(WHITELIST_SAMPLE)
        r7 = next(c for c in result["checks"] if c["id"] == "R7")
        self.assertEqual(r7["level"], "pass", r7["message"])
        self.assertEqual(result["verdict"], 0)

    def test_12_allow_list_suppresses_acronym(self):
        result = lint_text(ALLOW_SAMPLE, allow={"LNS"})
        r7 = next(c for c in result["checks"] if c["id"] == "R7")
        self.assertEqual(r7["level"], "pass", r7["message"])
        self.assertEqual(result["verdict"], 0)

    def test_13_load_allow_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "allow.txt"
            path.write_text("# 注释\nLNS\n\nMILP\n", encoding="utf-8")
            self.assertEqual(load_allow(path), {"LNS", "MILP"})

    def test_14_repo_filenames_not_treated_as_acronyms(self):
        result = lint_text(FILENAME_SAMPLE)
        r7 = next(c for c in result["checks"] if c["id"] == "R7")
        self.assertEqual(r7["level"], "pass", r7["message"])

    def test_15_rule_labels_not_treated_as_acronyms(self):
        result = lint_text(RULE_LABEL_SAMPLE)
        r7 = next(c for c in result["checks"] if c["id"] == "R7")
        self.assertEqual(r7["level"], "pass", r7["message"])


if __name__ == "__main__":
    unittest.main()
