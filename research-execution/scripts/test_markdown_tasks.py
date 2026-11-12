"""Isolated software fixtures, never real scientific evidence."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import research_infra as infra


class MarkdownTasksTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="research-markdown-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / "project"
        infra.initialize(self.root, "示例：软件夹具")

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def task(self, tid="T-001", state="待做", deps="无", mode="自检", extra="", body=""):
        return (f"## {tid} 示例模块\n\n- 状态：{state}\n- 依赖：{deps}\n- 负责人：fixture-author\n"
                f"- 复核方式：{mode}\n{extra}\n### 实施与验收条件\n检查示例算例和边界。\n"
                f"\n### 当前进展与下一步\n先检查输入，再核对输出。\n{body}\n")

    def output(self, name="artifacts/结果.md", text="示例：检查结果，无真实科研结论。"):
        path = self.write(name, text)
        return name, infra.digest(path)

    def accept(self, mode="自检", reviewer="fixture-reviewer", context="是"):
        name, sha = self.output()
        body = f"### 产物与证据\n| 产物 | SHA256 |\n|---|---|\n| [结果]({name}) | {sha} |\n\n### 自检记录\n独立计算示例边界，输出一致。\n"
        extra = ""
        if mode == "独立复核":
            review = self.write("reviews/T-001.md", f"""# 示例复核
- 任务：T-001
- 结论：通过
- 复核者：{reviewer}
- 复核方式：独立复核
- 独立上下文：{context}

### 检查内容
核对原始算例、评分定义和实际输出。
### 产物与证据
| 产物 | SHA256 |
|---|---|
| [结果](../{name}) | {sha} |
### 上下文依据
仅获得任务及原始输入，未获得作者结论。
### 局限
仅软件测试，不证明科研有效性。
""")
            extra = f"- 复核记录：[回执](reviews/T-001.md) | {infra.digest(review)}\n"
        self.write("TASKS.md", self.task(state="已验收", mode=mode, extra=extra, body=body))

    def test_default_markdown_and_no_parallel_state(self):
        self.assertFalse((self.root / "tasks.json").exists())
        self.assertTrue((self.root / "PLAN.md").exists())
        report = infra.check(self.root)
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["counts"], {"TODO": 10})
        self.assertEqual(report["ready_tasks"], ["G0"])

    def test_readers_do_not_mutate_task_source(self):
        before = infra.digest(self.root / "TASKS.md")
        infra.check(self.root)
        rendered, report = infra.export_board(self.root)
        self.assertEqual(before, infra.digest(self.root / "TASKS.md"))
        self.assertIn("待做", rendered)
        self.assertTrue(report["ok"])
        self.assertFalse((self.root / "tasks.json").exists())

    def test_combined_plan_with_explicit_source(self):
        self.write("protocol/实施计划.md", "# 示例计划\n\n## 目标与范围\n读取边界。\n\n" + self.task())
        report = infra.check(self.root, "protocol/实施计划.md")
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["ready_tasks"], ["T-001"])

    def test_code_quote_comment_examples_are_not_tasks(self):
        sample = self.task("T-999", state="已验收")
        text = "# 示例\n\n```markdown\n" + sample + "```\n\n~~~\n" + sample + "~~~\n\n"
        text += "\n".join("> " + line for line in sample.splitlines()) + "\n\n"
        text += "\n".join("    " + line for line in sample.splitlines()) + "\n\n"
        text += "<!--\n" + sample + "-->\n\n" + self.task()
        self.write("TASKS.md", text)
        report = infra.check(self.root)
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["counts"], {"TODO": 1})

    def test_status_typo_is_located_and_not_ready(self):
        self.write("TASKS.md", self.task(state="已验受"))
        report = infra.check(self.root)
        self.assertFalse(report["ok"])
        self.assertEqual(report["ready_tasks"], [])
        self.assertIn("TASKS.md:1", str(report["errors"]))

    def test_duplicate_and_unknown_control_fields_rejected(self):
        for extra in ("- 状态：已验收", "- 状太：已验收"):
            with self.subTest(extra=extra):
                self.write("TASKS.md", self.task(extra=extra))
                self.assertFalse(infra.check(self.root)["ok"])

    def test_orphan_control_is_not_silently_ignored(self):
        self.write("TASKS.md", "## T-x 无数字ID\n- 状态：已验收\n\n" + self.task())
        self.assertFalse(infra.check(self.root)["ok"])

    def test_duplicate_ids_and_dependency_failures(self):
        cases = [self.task() + self.task(), self.task(deps="T-999"),
                 self.task(deps="T-002") + self.task("T-002", deps="T-001"), self.task(deps="T-002、T-002")]
        for text in cases:
            with self.subTest(text=text):
                self.write("TASKS.md", text)
                report = infra.check(self.root)
                self.assertFalse(report["ok"])
                self.assertIn("TASKS.md:", str(report["errors"]))

    def test_running_dependency_is_not_complete(self):
        self.write("TASKS.md", self.task() + self.task("T-002", state="进行中", deps="T-001"))
        self.assertFalse(infra.check(self.root)["ok"])

    def test_body_lists_are_free_text_not_control_fields(self):
        self.write("TASKS.md", self.task(body="### 判断\n- 状态：这是讨论对象的状态，不是任务字段。\n- 发现：数据有噪声。"))
        report = infra.check(self.root)
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["counts"], {"TODO": 1})

    def test_placeholders_do_not_qualify_as_checks_or_criteria(self):
        self.write("TASKS.md", self.task(state="进行中").replace("检查示例算例和边界。", "待填写：边界测试"))
        self.assertFalse(infra.check(self.root)["ok"])
        self.accept()
        path = self.root / "TASKS.md"
        path.write_text(path.read_text(encoding="utf-8").replace("独立计算示例边界，输出一致。", "待填写：实际检查"), encoding="utf-8")
        self.assertFalse(infra.check(self.root)["ok"])

    def test_low_risk_acceptance_and_unlock(self):
        self.accept()
        path = self.root / "TASKS.md"
        path.write_text(path.read_text(encoding="utf-8") + self.task("T-002", deps="T-001"), encoding="utf-8")
        report = infra.check(self.root)
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["ready_tasks"], ["T-002"])

    def test_independent_markdown_review_and_relative_paths(self):
        self.accept(mode="独立复核")
        report = infra.check(self.root)
        self.assertTrue(report["ok"], report)

    def test_self_review_and_missing_context_cannot_pass(self):
        for reviewer, context in (("fixture-author", "是"), ("fixture-reviewer", "否")):
            self.accept(mode="独立复核", reviewer=reviewer, context=context)
            self.assertFalse(infra.check(self.root)["ok"])

    def test_modified_review_or_output_invalidates_acceptance(self):
        self.accept(mode="独立复核")
        self.write("reviews/T-001.md", "# 已变化\n")
        self.assertFalse(infra.check(self.root)["ok"])
        self.accept()
        self.write("artifacts/结果.md", "changed")
        rendered, report = infra.export_board(self.root)
        self.assertFalse(report["ok"])
        self.assertIn("不构成有效验收", rendered)
        self.assertNotIn("机械检查通过", rendered)

    def test_review_must_bind_actual_task_outputs(self):
        self.accept(mode="独立复核")
        review = self.root / "reviews/T-001.md"
        old_sha = infra.digest(review)
        _, other_sha = self.output("artifacts/other.md", "different")
        text = review.read_text(encoding="utf-8").replace(infra.digest(self.root / "artifacts/结果.md"), other_sha)
        review.write_text(text, encoding="utf-8")
        tasks = self.root / "TASKS.md"
        tasks.write_text(tasks.read_text(encoding="utf-8").replace(old_sha, infra.digest(review)), encoding="utf-8")
        self.assertFalse(infra.check(self.root)["ok"])

    def test_review_state_requires_actual_output_and_self_check(self):
        self.write("TASKS.md", self.task(state="待核验"))
        self.assertFalse(infra.check(self.root)["ok"])
        self.accept()
        path = self.root / "TASKS.md"
        path.write_text(path.read_text(encoding="utf-8").replace("状态：已验收", "状态：待核验"), encoding="utf-8")
        report = infra.check(self.root)
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["counts"], {"REVIEW": 1})

    def test_blocked_and_deferred_need_reasons_and_do_not_complete(self):
        for state, section in (("受阻", "阻断原因"), ("暂缓", "暂缓原因")):
            self.write("TASKS.md", self.task(state=state))
            self.assertFalse(infra.check(self.root)["ok"])
            self.write("TASKS.md", self.task(state=state, body=f"### {section}\n示例：等待材料，其他独立工作继续。"))
            report = infra.check(self.root)
            self.assertTrue(report["ok"], report)
            self.assertNotIn("ACCEPTED", report["counts"])

    def test_dual_source_requires_explicit_selection(self):
        legacy = infra.BASE / "templates/兼容/tasks.json"
        self.write("tasks.json", legacy.read_text(encoding="utf-8"))
        with self.assertRaisesRegex(ValueError, "双源"):
            infra.check(self.root)
        self.assertTrue(infra.check(self.root, "TASKS.md")["ok"])
        self.assertTrue(infra.check(self.root, "tasks.json")["ok"])

    def test_inline_local_links_and_anchors(self):
        self.write("文档 (一).md", "# 定义\n")
        self.write("TASKS.md", self.task(extra="- 对应计划：[定义](<文档 (一).md#定义>)"))
        self.assertTrue(infra.check(self.root)["ok"])
        self.write("TASKS.md", self.task(extra="- 对应计划：[定义](<文档 (一).md#不存在>)"))
        self.assertFalse(infra.check(self.root)["ok"])

    def test_path_escape_missing_and_external_evidence_rejected(self):
        for target in ("../outside.md", "C:/private.txt", "missing.md"):
            self.write("TASKS.md", self.task(extra=f"- 对应计划：[输入]({target})"))
            self.assertFalse(infra.check(self.root)["ok"])
        self.write("TASKS.md", self.task(body="### 产物与证据\n| 产物 | SHA256 |\n|---|---|\n| [远程](https://example.org/a) | " + "0" * 64 + " |"))
        self.assertFalse(infra.check(self.root)["ok"])

    def test_bom_crlf_unicode(self):
        (self.root / "TASKS.md").write_bytes(("\ufeff" + self.task()).replace("\n", "\r\n").encode("utf-8"))
        self.assertTrue(infra.check(self.root)["ok"])

    def test_board_detects_progress_change_and_manual_edit(self):
        infra.export_board(self.root, output="artifacts/概览.md")
        self.assertTrue(infra.check(self.root, board_file="artifacts/概览.md")["ok"])
        task = self.root / "TASKS.md"
        task.write_text(task.read_text(encoding="utf-8") + "\n新增接续说明。\n", encoding="utf-8")
        self.assertFalse(infra.check(self.root, board_file="artifacts/概览.md")["ok"])
        infra.export_board(self.root, output="artifacts/概览.md")
        self.write("artifacts/概览.md", "manual")
        self.assertFalse(infra.check(self.root, board_file="artifacts/概览.md")["ok"])

    def test_exported_board_links_resolve_from_output_location(self):
        self.accept(mode="独立复核")
        rendered, report = infra.export_board(self.root, output="artifacts/概览.md")
        self.assertTrue(report["ok"], report)
        source = self.root / "artifacts/概览.md"
        links = list(infra.md.LINK.finditer(rendered))
        self.assertEqual(len(links), 3)
        for link in links:
            self.assertIsNotNone(infra.md.resolve_link(self.root, source, link[1]))
        self.assertTrue(infra.check(self.root, board_file="artifacts/概览.md")["ok"])

    def test_export_refuses_human_files_sources_and_escape(self):
        self.write("artifacts/manual.md", "user-owned")
        for target in ("artifacts/manual.md", "TASKS.md", "../outside.md", "project.json"):
            with self.subTest(target=target), self.assertRaises(ValueError):
                infra.export_board(self.root, output=target)
        self.assertEqual((self.root / "artifacts/manual.md").read_text(encoding="utf-8"), "user-owned")

    def test_read_failure_leaves_previous_board_unchanged(self):
        infra.export_board(self.root, output="artifacts/概览.md")
        before = infra.digest(self.root / "artifacts/概览.md")
        self.write("TASKS.md", "# malformed source with no task")
        with self.assertRaises(ValueError):
            infra.export_board(self.root, output="artifacts/概览.md")
        self.assertEqual(before, infra.digest(self.root / "artifacts/概览.md"))

    def test_read_detects_concurrent_source_change(self):
        original = infra.md.read_tasks
        def changing(root, source):
            board = original(root, source)
            source.write_text(source.read_text(encoding="utf-8") + "\nchanged\n", encoding="utf-8")
            return board
        with patch.object(infra.md, "read_tasks", side_effect=changing), self.assertRaisesRegex(ValueError, "变化"):
            infra.load_tasks(self.root)

    def test_markdown_snapshot_gates_and_explicit_source(self):
        project = infra.read_json(self.root / "project.json")
        project["snapshot_required_tasks"]["protocol"] = ["T-001"]
        self.write("project.json", json.dumps(project))
        self.accept()
        path = self.root / "TASKS.md"
        path.rename(self.root / "PLAN-TASKS.md")
        result = infra.snapshot(self.root, "md1", "protocol", ["artifacts/结果.md"], "PLAN-TASKS.md")
        self.assertTrue(Path(result["manifest"]).is_file())
        self.assertTrue(infra.verify(self.root, "snapshots/md1.json")["ok"])
        self.write("PLAN-TASKS.md", self.task())
        with self.assertRaises(ValueError):
            infra.snapshot(self.root, "md2", "protocol", ["artifacts/结果.md"], "PLAN-TASKS.md")

    def test_cli_exit_codes_and_optional_markdown_output(self):
        command = [sys.executable, "-X", "utf8", str(infra.BASE / "scripts/research_infra.py")]
        clean = subprocess.run(command + ["board", "--root", str(self.root)], capture_output=True, encoding="utf-8")
        self.assertEqual(clean.returncode, 0, clean.stderr)
        self.assertTrue(clean.stdout.startswith(infra.BOARD_MARKER))
        self.write("TASKS.md", self.task(state="未知状态"))
        invalid = subprocess.run(command + ["check", "--root", str(self.root)], capture_output=True, encoding="utf-8")
        self.assertEqual(invalid.returncode, 1)
        self.write("TASKS.md", "unreadable task structure")
        broken = subprocess.run(command + ["check", "--root", str(self.root)], capture_output=True, encoding="utf-8")
        self.assertEqual(broken.returncode, 2)
        self.assertFalse(json.loads(broken.stdout)["ok"])


if __name__ == "__main__":
    unittest.main()
