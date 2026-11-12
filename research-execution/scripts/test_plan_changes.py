"""Synthetic plan changes; no scientific findings or live project state."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import research_infra as infra


class PlanChangesTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="research-plan-change-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        infra.initialize(self.root, "示例：计划变更测试")

    def put(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def replace(self, name, before, after):
        path = self.root / name
        self.assertIn(before, path.read_text(encoding="utf-8"))
        self.put(name, path.read_text(encoding="utf-8").replace(before, after))

    def card(self, tid="T-001", state="待做", mode="自检", extra="", body=""):
        return f"""## {tid} 示例结果检查
- 状态：{state}
- 要求版本：V1
- 依赖：无
- 负责人：author
- 复核方式：{mode}
{extra}
### 目标与边界
核验合成评分实现，不外推科学结论。
### 输入与版本
输入为固定的合成例 v1。
### 实施步骤
先检查正常值，再检查边界。
### 验收条件
两项独立算例与实现一致。
### 当前进展与下一步
核对输入，再提交实际证据。
{body}
"""

    def tasks(self, cards, header=True):
        head = "# 示例任务\n- 计划文件：[计划](PLAN.md)\n- 已同步计划修订：R1\n\n" if header else ""
        return self.put("TASKS.md", head + cards)

    def accepted(self, mode="自检"):
        product = self.put("result.md", "Synthetic result; not scientific evidence.")
        body = f"### 产物与证据\n| 产物 | SHA256 |\n|---|---|\n| [结果](result.md) | {infra.digest(product)} |\n\n### 自检记录\n核对两项合成输入的实际输出一致。\n"
        self.tasks(self.card(state="进行中", mode=mode, body=body))
        basis = infra.task_bases(self.root, task_id="T-001")["bases"][0]
        extra = f"- 自检依据：{basis['version']} | {basis['sha256']}\n"
        if mode == "独立复核":
            review = self.put("reviews/review.md", f"""# 示例验收
- 任务：T-001
- 结论：通过
- 复核者：reviewer
- 复核方式：独立复核
- 独立上下文：是
- 验收依据：{basis['version']} | {basis['sha256']}
### 检查内容
从合成输入独立复算并核对输出。
### 产物与证据
| 产物 | SHA256 |
|---|---|
| [结果](../result.md) | {infra.digest(product)} |
### 上下文依据
独立获得任务定义和合成输入，不采用作者结论。
### 局限
仅为软件接口声明，不认证科学独立复核。
""")
            extra += f"- 复核记录：[回执](reviews/review.md) | {infra.digest(review)}\n"
        self.tasks(self.card(state="已验收", mode=mode, extra=extra, body=body))
        self.assertTrue(infra.check(self.root)["ok"], infra.check(self.root))
        return basis

    def test_default_initialization_declares_plan_and_requirements(self):
        report = infra.check(self.root)
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["plan"], {"path": "PLAN.md", "revision": "R1"})
        self.assertTrue(all(t["requirements_version"] == "V1" for t in infra.load_tasks(self.root)["tasks"]))

    def test_changed_plan_blocks_snapshot_and_reports_unsynced_board(self):
        self.accepted()
        self.replace("PLAN.md", "当前修订：R1", "当前修订：R2")
        rendered, report = infra.export_board(self.root)
        self.assertFalse(report["ok"])
        self.assertIn("尚未同步", str(report["errors"]))
        self.assertNotIn("机械检查通过", rendered)
        with self.assertRaisesRegex(ValueError, "未通过"):
            infra.snapshot(self.root, "p1", "protocol", ["result.md"])
        self.assertFalse((self.root / "snapshots/p1.json").exists())

    def test_plan_other_module_change_does_not_invalidate_local_acceptance(self):
        before = self.accepted("独立复核")
        self.replace("PLAN.md", "当前修订：R1", "当前修订：R2")
        self.replace("TASKS.md", "已同步计划修订：R1", "已同步计划修订：R2")
        self.assertTrue(infra.check(self.root)["ok"])
        self.assertEqual(infra.task_bases(self.root, task_id="T-001")["bases"][0], before)

    def test_contract_changes_reject_unchanged_product_and_old_receipt(self):
        for old, new in (("两项独立算例", "跨三个输入组的算例"),
                         ("输入为固定的合成例 v1", "输入为固定的合成例 v2"),
                         ("不外推科学结论", "覆盖另外一个定义"), ("要求版本：V1", "要求版本：V2")):
            with self.subTest(change=new):
                self.accepted("独立复核")
                artifact = infra.digest(self.root / "result.md")
                self.replace("TASKS.md", old, new)
                report = infra.check(self.root)
                self.assertFalse(report["ok"])
                self.assertIn("验收依据", str(report["errors"]))
                self.assertEqual(infra.digest(self.root / "result.md"), artifact)

    def test_progress_steps_title_and_history_do_not_invalidate_acceptance(self):
        before = self.accepted("独立复核")
        for old, new in (("示例结果检查", "示例结果检查改名"), ("先检查正常值，再检查边界。", "先检查边界，再检查正常值。"),
                         ("核对输入，再提交实际证据。", "已完成，接续下一项工作。")):
            self.replace("TASKS.md", old, new)
        path = self.root / "TASKS.md"
        self.put("TASKS.md", path.read_text(encoding="utf-8") + "\n### 变更记录\n补充当前接续说明，无要求变化。\n")
        self.assertTrue(infra.check(self.root)["ok"])
        self.assertEqual(infra.task_bases(self.root, task_id="T-001")["bases"][0], before)

    def test_low_risk_self_check_also_binds_requirements(self):
        self.accepted()
        self.replace("TASKS.md", "两项独立算例", "三项独立算例")
        self.assertIn("自检依据", str(infra.check(self.root)["errors"]))

    def test_contract_embedded_code_is_bound_but_not_parsed_as_tasks(self):
        code = "核验合成评分实现，不外推科学结论。\n```text\n## T-999 示例伪任务\n- 状态：已验收\nunit = seconds\n```"
        self.tasks(self.card(state="进行中").replace("核验合成评分实现，不外推科学结论。", code))
        self.assertEqual(len(infra.load_tasks(self.root)["tasks"]), 1)
        before = infra.task_bases(self.root, task_id="T-001")["bases"][0]
        self.replace("TASKS.md", "unit = seconds", "unit = milliseconds")
        self.assertNotEqual(infra.task_bases(self.root, task_id="T-001")["bases"][0], before)

    def test_quoted_and_fenced_acceptance_content_is_bound(self):
        for extra in ("> 输入单位为秒。", "```text\n输入单位为秒。\n```", "<!-- 输入单位为秒。 -->"):
            with self.subTest(extra=extra):
                self.tasks(self.card(state="进行中").replace("两项独立算例与实现一致。", "两项独立算例与实现一致。\n" + extra))
                before = infra.task_bases(self.root, task_id="T-001")["bases"][0]
                self.replace("TASKS.md", "输入单位为秒。", "输入单位为毫秒。")
                self.assertNotEqual(infra.task_bases(self.root, task_id="T-001")["bases"][0], before)

    def test_review_submission_needs_current_self_check_basis(self):
        self.accepted()
        self.replace("TASKS.md", "状态：已验收", "状态：待核验")
        self.assertTrue(infra.check(self.root)["ok"])
        self.replace("TASKS.md", "要求版本：V1", "要求版本：V2")
        self.assertFalse(infra.check(self.root)["ok"])

    def test_legacy_receipt_cannot_accept_versioned_task(self):
        self.accepted("独立复核")
        path = self.root / "reviews/review.md"
        old_hash = infra.digest(path)
        self.put("reviews/review.md", "\n".join(line for line in path.read_text(encoding="utf-8").splitlines() if not line.startswith("- 验收依据")))
        self.replace("TASKS.md", old_hash, infra.digest(path))
        self.assertFalse(infra.check(self.root)["ok"])

    def test_combined_plan_needs_no_second_revision_marker(self):
        self.put("TASKS.md", "# 示例合并计划\n- 当前修订：R4\n\n## 目标\n观察合成算例。\n\n" + self.card())
        report = infra.check(self.root)
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["plan"], {"path": "TASKS.md", "revision": "R4"})

    def test_metadata_duplicates_malformed_and_partial_rejected(self):
        for header in ("- 计划文件：[计划](PLAN.md)\n", "- 已同步计划修订：R1\n",
                       "- 当前修订：R1\n- 当前修订：R2\n", "- 当前修订：第一版\n",
                       "- 当前修订：R1\n- 计划文件：[计划](PLAN.md)\n"):
            self.put("TASKS.md", "# 示例\n" + header + self.card())
            try:
                self.assertFalse(infra.check(self.root)["ok"], header)
            except ValueError:
                pass

    def test_metadata_inside_examples_is_ignored(self):
        self.put("TASKS.md", "# 示例\n```md\n- 当前修订：R99\n```\n> - 当前修订：R9\n\n" + self.card())
        report = infra.check(self.root)
        self.assertTrue(report["ok"])
        self.assertIsNone(report["plan"])

    def test_custom_subdirectory_plan_paths(self):
        self.put("plans/计划 (当前).md", "# 计划\n- 当前修订：R2\n")
        self.put("cards/任务.md", "# 任务\n- 计划文件：[计划](<../plans/计划 (当前).md>)\n- 已同步计划修订：R2\n" + self.card())
        self.assertTrue(infra.check(self.root, "cards/任务.md")["ok"])

    def test_plan_change_alone_makes_saved_board_stale(self):
        self.tasks(self.card())
        infra.export_board(self.root, output="artifacts/board.md")
        self.replace("PLAN.md", "# 总体计划", "# 总体计划（补充说明）")
        self.assertFalse(infra.check(self.root, board_file="artifacts/board.md")["ok"])

    def test_plan_concurrent_change_is_detected(self):
        self.tasks(self.card())
        original = infra.md.document_fields
        def changing(source):
            fields = original(source)
            if source.name == "PLAN.md":
                source.write_text(source.read_text(encoding="utf-8") + "\n变化\n", encoding="utf-8")
            return fields
        with patch.object(infra.md, "document_fields", side_effect=changing), self.assertRaisesRegex(ValueError, "变化"):
            infra.check(self.root)

    def test_successor_relations_do_not_act_as_dependencies(self):
        old = self.card(state="暂缓", extra="- 承接任务：T-002、T-003", body="### 暂缓原因\n示例：拆分，本轮不再执行旧卡。")
        self.tasks(old + self.card("T-002") + self.card("T-003"))
        report = infra.check(self.root)
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["ready_tasks"], ["T-002", "T-003"])

    def test_missing_duplicate_self_and_cyclic_successors_rejected(self):
        for targets in ("T-999", "T-001", "T-002、T-002"):
            self.tasks(self.card(state="暂缓", extra=f"- 承接任务：{targets}", body="### 暂缓原因\n已移交。") + self.card("T-002"))
            self.assertFalse(infra.check(self.root)["ok"])
        self.tasks(self.card(state="暂缓", extra="- 承接任务：T-002", body="### 暂缓原因\n已移交。") +
                   self.card("T-002", state="暂缓", extra="- 承接任务：T-001", body="### 暂缓原因\n已移交。"))
        self.assertIn("承接关系成环", str(infra.check(self.root)["errors"]))

    def test_retired_task_cannot_remain_ready(self):
        self.tasks(self.card(extra="- 承接任务：T-002") + self.card("T-002"))
        report = infra.check(self.root)
        self.assertFalse(report["ok"])
        self.assertEqual(report["ready_tasks"], [])

    def test_dependency_on_retired_task_is_visible(self):
        self.tasks(self.card(state="暂缓", extra="- 承接任务：T-002", body="### 暂缓原因\n已替代。") + self.card("T-002") +
                   self.card("T-003").replace("依赖：无", "依赖：T-001"))
        report = infra.check(self.root)
        self.assertTrue(report["ok"])
        self.assertIn("仍依赖", str(report["warnings"]))
        self.assertNotIn("T-003", report["ready_tasks"])

    def test_json_opt_in_has_same_basis_and_rejects_changed_contract(self):
        expected = self.accepted()
        board = infra.load_tasks(self.root)
        data = {"schema_version": 1, "plan": board["plan"], "tasks": board["tasks"]}
        self.put("opt-in.json", json.dumps(data, ensure_ascii=False))
        self.assertEqual(infra.task_bases(self.root, "opt-in.json", "T-001")["bases"][0], expected)
        self.assertTrue(infra.check(self.root, "opt-in.json")["ok"])
        data["tasks"][0]["goal"] = "新的交付目标。"
        self.put("opt-in.json", json.dumps(data, ensure_ascii=False))
        self.assertFalse(infra.check(self.root, "opt-in.json")["ok"])

    def test_basis_cli_is_read_only_and_not_acceptance(self):
        self.tasks(self.card(state="进行中"))
        before = infra.digest(self.root / "TASKS.md")
        self.replace("PLAN.md", "当前修订：R1", "当前修订：R2")
        command = [sys.executable, "-X", "utf8", "-B", str(infra.BASE / "scripts/research_infra.py"), "basis", "--root", str(self.root), "--task", "T-001"]
        result = subprocess.run(command, capture_output=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(len(json.loads(result.stdout)["bases"][0]["sha256"]), 64)
        self.assertEqual(before, infra.digest(self.root / "TASKS.md"))
        self.assertFalse(infra.check(self.root)["ok"])

    def test_snapshot_inconsistency_and_input_failure_have_distinct_exit_codes(self):
        self.accepted()
        self.replace("PLAN.md", "当前修订：R1", "当前修订：R2")
        command = [sys.executable, "-X", "utf8", "-B", str(infra.BASE / "scripts/research_infra.py"),
                   "snapshot", "--root", str(self.root), "--id", "blocked", "--kind", "protocol", "--files", "result.md"]
        result = subprocess.run(command, capture_output=True, encoding="utf-8")
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertFalse((self.root / "snapshots/blocked.json").exists())
        self.put("TASKS.md", "# No tasks")
        result = subprocess.run(command, capture_output=True, encoding="utf-8")
        self.assertEqual(result.returncode, 2, result.stdout)

    def test_plan_change_during_snapshot_preparation_is_rejected(self):
        self.accepted()
        project = infra.read_json(self.root / "project.json")
        project["snapshot_required_tasks"]["protocol"] = ["T-001"]
        self.put("project.json", json.dumps(project))
        original = infra.digest
        count = 0
        def changing(path):
            nonlocal count
            result = original(path)
            if Path(path).name == "result.md":
                count += 1
                if count == 2:
                    self.replace("PLAN.md", "当前修订：R1", "当前修订：R2")
            return result
        with patch.object(infra, "digest", side_effect=changing), self.assertRaises(infra.CheckFailure):
            infra.snapshot(self.root, "race", "protocol", ["result.md"])
        self.assertFalse((self.root / "snapshots/race.json").exists())

    def test_blank_or_malformed_contract_cannot_generate_submission_basis(self):
        with self.assertRaises(ValueError):
            infra.task_bases(self.root, task_id="G0")
        self.tasks(self.card(extra="- 自检依据：随便填"))
        with self.assertRaises(ValueError):
            infra.task_bases(self.root, task_id="T-001")

    def test_legacy_acceptance_reports_unchecked_scope_in_board(self):
        self.accepted()
        path = self.root / "TASKS.md"
        self.put("TASKS.md", "\n".join(line for line in path.read_text(encoding="utf-8").splitlines()
                                        if not line.startswith(("- 要求版本", "- 自检依据", "- 计划文件", "- 已同步"))))
        rendered, report = infra.export_board(self.root)
        self.assertTrue(report["ok"])
        self.assertIn("未绑定任务要求版本", rendered)
        self.assertIn("未登记计划同步", rendered)


if __name__ == "__main__":
    unittest.main()
