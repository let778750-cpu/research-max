"""Examples of grouping failures, not scientific acceptance evidence."""
from pathlib import Path
import tempfile
import unittest

import research_infra as infra


class ModuleGroupsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="module-groups-example-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "project.json").write_text('{"schema_version":1,"name":"示例"}', encoding="utf-8")

    def task(self, tid, dependency="无"):
        return f"\n## {tid} 示例任务\n- 状态：待做\n- 依赖：{dependency}\n- 复核方式：自检\n\n### 验收条件\n核对示例输入与输出。\n"

    def run_case(self, grouping, tasks=None):
        text = "# 示例任务\n\n" + grouping + (tasks or self.task("T-1") + self.task("T-2", "T-1"))
        (self.root / "TASKS.md").write_text(text, encoding="utf-8")
        return infra.check(self.root)

    def table(self, rows):
        return "## 模块分组\n| 模块 | 任务 | 共同产出 | 集成条件 |\n|---|---|---|---|\n" + rows + "\n"

    def test_shared_delivery_keeps_distinct_task_states(self):
        self.assertTrue(self.run_case(self.table("| M-1 | T-1、T-2 | 示例评分器及对照 | 核对同一接口 |"))["ok"])
        before = (self.root / "TASKS.md").read_bytes()
        board, report = infra.export_board(self.root)
        self.assertIn("T-1：待做", board)
        self.assertIn("T-2：待做", board)
        self.assertEqual(before, (self.root / "TASKS.md").read_bytes())

    def test_missing_member_duplicate_membership_and_id(self):
        rows = ["| M-1 | T-9 | 示例 | 检查 |",
                "| M-1 | T-1、T-1 | 示例 | 检查 |",
                "| M-1 | T-1 | 示例 | 检查 |\n| M-2 | T-1 | 示例 | 检查 |",
                "| M-1 | T-1 | 示例 | 检查 |\n| M-1 | T-2 | 示例 | 检查 |"]
        for row in rows:
            with self.subTest(row=row):
                report = self.run_case(self.table(row))
                self.assertFalse(report["ok"])
                self.assertIn("TASKS.md:", str(report["errors"]))

    def test_contraction_cycle_through_an_ungrouped_task(self):
        tasks = self.task("T-1") + self.task("T-2", "T-1") + self.task("T-3", "T-2")
        result = self.run_case(self.table("| M-1 | T-1、T-3 | 示例 | 检查 |"), tasks)
        self.assertFalse(result["ok"])
        self.assertIn("分组后的依赖成环", str(result["errors"]))

    def test_example_sections_do_not_activate(self):
        example = self.table("| M-1 | T-999 | 示例 | 检查 |")
        for text in ("```markdown\n" + example + "```\n", "\n".join("> " + x for x in example.splitlines()) + "\n"):
            self.assertTrue(self.run_case(text)["ok"])

    def test_placeholders_do_not_qualify_as_grouping(self):
        self.assertFalse(self.run_case(self.table("| M-1 | T-1 | 待填写 | 待填写 |"))["ok"])

    def test_no_grouping_remains_compatible(self):
        self.assertTrue(self.run_case("")["ok"])


if __name__ == "__main__":
    unittest.main()
