"""Real isolated Git + fake GitHub. Never contacts GitHub or invokes a model."""
import copy
import contextlib
import io
import json
from pathlib import Path
import subprocess
import runpy
import sys
import tempfile
import unittest
from unittest.mock import patch

import record as r


TASKS = """# 示例任务
- 计划文件：[计划](PLAN.md)
- 已同步计划修订：R1

## GitHub记录约定
- 仓库：example/research-fixture
- 指定任务：T-001
- 授权来源：用户明确指定此隔离软件示例使用GitHub记录
- 当前接手者：示例主持者
- 发布：允许
- 合并方式：自动
- 基线分支：main

## 模块分组
| 模块 | 任务 | 共同产出 | 集成条件 |
|---|---|---|---|
| M-001 | T-001 | 示例均值程序与手算对照 | 三数均值与空输入行为一致；已有任务验收覆盖集成 |

## T-001 示例均值程序
- 状态：待做
- 要求版本：V1
- 依赖：无
- 负责人：示例作者
- 复核方式：自检

### 目标与边界
核对小型软件夹具，不构成真实科学结论。
### 验收条件
- 1、2、3的均值为2，空输入给出明确失败。
### 当前进展与下一步
等待示例执行。

## T-002 示例范围外任务
- 状态：待做
- 要求版本：V1
- 依赖：无
- 复核方式：自检
### 目标与边界
保留范围外工作。
### 验收条件
- 不自动派发此任务。
"""


class FakeGitHub:
    def __init__(self, bare):
        self.bare = bare
        self.issue_data, self.pr_data = [], []
        self.calls, self.fail_after, self.private = [], None, True

    def hit(self, name):
        self.calls.append(name)
        if self.fail_after == name:
            self.fail_after = None
            raise r.CommandError("示例：远端已执行，但响应丢失")

    def git(self, *args):
        return r.command(["git", "--git-dir=" + str(self.bare), *args]).stdout.strip()

    def info(self):
        return {"private": self.private, "permissions": {"push": True}, "allow_merge_commit": True}

    def create(self):
        self.hit("create_repo")

    def issues(self):
        return copy.deepcopy(self.issue_data)

    def issue_create(self, body):
        self.issue_data.append({"number": 1, "html_url": "https://github.com/example/research-fixture/issues/1", "body": body})
        self.hit("create_issue")

    def issue_edit(self, number, body):
        self.issue_data[number - 1]["body"] = body
        self.hit("edit_issue")

    def issue_pin(self, number):
        self.hit("pin_issue")

    def prs(self, branch, base):
        return [self.pr(x["number"]) for x in self.pr_data if x["headRefName"] == branch and x["baseRefName"] == base]

    def pr_create(self, branch, base, title, body):
        number = len(self.pr_data) + 1
        self.pr_data.append(dict(number=number, url=f"https://github.com/example/research-fixture/pull/{number}",
                                 headRefName=branch, baseRefName=base, state="OPEN", isDraft=True, body=body, mergeCommit=None))
        self.hit("create_pr")

    def pr(self, number):
        result = copy.deepcopy(self.pr_data[number - 1])
        result["headRefOid"] = self.git("rev-parse", "refs/heads/" + result["headRefName"])
        result["baseRefOid"] = self.git("rev-parse", "refs/heads/" + result["baseRefName"])
        return result

    def pr_edit(self, number, body):
        self.pr_data[number - 1]["body"] = body
        self.hit("edit_pr")

    def ready(self, number):
        self.pr_data[number - 1]["isDraft"] = False
        self.hit("ready")

    def merge(self, number, head):
        pr = self.pr(number)
        assert head == pr["headRefOid"]
        tree = self.git("rev-parse", head + "^{tree}")
        merged = self.git("commit-tree", tree, "-p", pr["baseRefOid"], "-p", head, "-m", "Example module merge")
        self.git("update-ref", "refs/heads/" + pr["baseRefName"], merged, pr["baseRefOid"])
        self.pr_data[number - 1].update(state="MERGED", mergeCommit={"oid": merged})
        self.hit("merge")


class LocalGitTransport(r.Git):
    def origin(self):
        # Tests route the named GitHub remote to a local bare repo, never a network.
        return self.run("config", "--get", "remote.origin.url", check=False)


class RecorderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="github-record-示例-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root, self.bare = self.base / "权威 项目", self.base / "remote.git"
        self.root.mkdir()
        r.command(["git", "init", "--bare", str(self.bare)])
        for key, value in (("user.name", "Example"), ("user.email", "example@invalid.local")):
            r.command(["git", "--git-dir=" + str(self.bare), "config", key, value])
        self.git = LocalGitTransport(self.root)
        self.git.run("init", "-b", "main")
        for key, value in (("user.name", "Example"), ("user.email", "example@invalid.local"), ("core.autocrlf", "false")):
            self.git.run("config", key, value)
        self.git.run("config", "url." + self.bare.as_posix() + ".insteadOf", "https://github.com/example/research-fixture.git")
        self.write("TASKS.md", TASKS)
        self.write("PLAN.md", "# 示例计划\n- 当前修订：R1\n\n核对三数均值，不生成真实科研结论。\n")
        self.write("project.json", '{"schema_version":1,"name":"隔离示例"}')
        self.gh = FakeGitHub(self.bare)

    def write(self, name, text):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p

    def edit(self, before, after):
        p = self.root / "TASKS.md"
        p.write_text(p.read_text(encoding="utf-8").replace(before, after), encoding="utf-8")

    def recorder(self, owner="示例主持者"):
        return r.Recorder(self.root, owner=owner, github=self.gh, git=self.git)

    def connected(self):
        self.recorder().connect([])

    def started(self):
        self.connected()
        self.recorder().start("M-001", 1, [])

    def accept(self):
        product = self.write("artifacts/均值结果.md", "示例：独立加总6，除以3为2；空输入明确失败。没有性能提升结论。\n")
        basis = r.infra.task_bases(self.root, task_id="T-001")["bases"][0]
        self.edit("- 状态：待做\n- 要求版本：V1\n- 依赖：无\n- 负责人：示例作者", "- 状态：已验收\n- 要求版本：V1\n- 自检依据：V1 | " + basis["sha256"] + "\n- 依赖：无\n- 负责人：示例作者")
        self.edit("## T-002", "### 自检记录\n对照手算，均值2，空输入失败；现有任务核验已覆盖本模块接口。\n\n"
                  "### 产物与证据\n| 产物 | SHA256 |\n|---|---|\n| [结果](artifacts/均值结果.md) | " + r.infra.digest(product) + " |\n\n## T-002")
        self.recorder().publish("M-001", 1, ["artifacts/均值结果.md"], "test: record example checks")

    def sealed(self):
        self.started()
        self.accept()
        self.recorder().attest("M-001", 1, ["artifacts/均值结果.md"])

    def test_full_loop_and_read_only_status(self):
        self.sealed()
        before = (self.root / "TASKS.md").read_bytes()
        result = self.recorder().merge("M-001", 1)
        self.assertTrue(result["merged"])
        self.assertEqual(before, (self.root / "TASKS.md").read_bytes())
        calls = list(self.gh.calls)
        data = self.recorder(owner=None).status("M-001", 1)
        self.assertEqual(data["pr"]["state"], "MERGED")
        self.assertEqual(calls, self.gh.calls)
        self.assertEqual(self.gh.calls.count("merge"), 1)
        self.assertIn("T-001：已验收", self.gh.issue_data[0]["body"])

    def test_missing_opt_in_and_paused_do_not_publish(self):
        self.edit("## GitHub记录约定", "## 历史讨论")
        with self.assertRaisesRegex(ValueError, "未启用"):
            self.recorder()
        self.assertEqual(self.gh.calls, [])
        self.edit("## 历史讨论", "## GitHub记录约定")
        self.edit("- 发布：允许", "- 发布：暂停")
        with self.assertRaisesRegex(ValueError, "暂停"):
            self.recorder().connect([])
        self.assertEqual(self.gh.calls, [])

    def test_scope_and_owner(self):
        with self.assertRaisesRegex(ValueError, "接手者"):
            self.recorder(owner="另一个窗口").connect([])
        self.connected()
        self.edit("| M-001 | T-001 |", "| M-001 | T-001、T-002 |")
        with self.assertRaisesRegex(ValueError, "未授权"):
            self.recorder().start("M-001", 1, [])

    def test_public_repo_is_not_used(self):
        self.gh.private = False
        with self.assertRaisesRegex(ValueError, "私有"):
            self.recorder().connect([])
        self.assertEqual(self.gh.calls, [])

    def test_unrelated_staged_and_untracked_files_preserved(self):
        self.write("unrelated.txt", "untouched")
        self.write("private-note.txt", "do not publish")
        self.git.run("add", "unrelated.txt")
        self.connected()
        self.recorder().start("M-001", 1, [])
        self.assertIn("unrelated.txt", self.git.paths("diff", "--cached", "--name-only"))
        self.assertNotIn("unrelated.txt", self.git.tracked_at(self.git.head()))
        self.assertNotIn("private-note.txt", self.git.tracked_at(self.git.head()))
        self.assertEqual((self.root / "unrelated.txt").read_text(), "untouched")

    def test_issue_creation_response_loss_is_recovered(self):
        self.gh.fail_after = "create_issue"
        with self.assertRaises(r.CommandError):
            self.connected()
        self.connected()
        self.assertEqual(len(self.gh.issue_data), 1)

    def test_pr_creation_response_loss_is_recovered(self):
        self.connected()
        self.gh.fail_after = "create_pr"
        with self.assertRaises(r.CommandError):
            self.recorder().start("M-001", 1, [])
        self.recorder().start("M-001", 1, [])
        self.assertEqual(len(self.gh.pr_data), 1)

    def test_merge_response_loss_queries_remote_without_repeating(self):
        self.sealed()
        self.gh.fail_after = "merge"
        with self.assertRaises(r.CommandError):
            self.recorder().merge("M-001", 1)
        self.recorder().merge("M-001", 1)
        self.assertEqual(self.gh.calls.count("merge"), 1)

    def test_partial_work_cannot_be_attested(self):
        self.started()
        with self.assertRaisesRegex(ValueError, "尚未验收"):
            self.recorder().attest("M-001", 1, ["TASKS.md"])
        self.assertNotIn("merge", self.gh.calls)

    def test_changed_product_cannot_pass(self):
        self.sealed()
        self.write("artifacts/均值结果.md", "changed")
        with self.assertRaisesRegex(ValueError, "改变"):
            self.recorder()
        self.assertNotIn("merge", self.gh.calls)

    def test_changed_head_requires_new_attestation(self):
        self.sealed()
        self.write("notes.md", "示例追加说明")
        self.recorder().publish("M-001", 1, ["notes.md"], "docs: clarify example")
        with self.assertRaisesRegex(ValueError, "封存"):
            self.recorder().merge("M-001", 1)

    def test_no_merge_without_attestation(self):
        self.started()
        self.accept()
        with self.assertRaisesRegex(ValueError, "封存"):
            self.recorder().merge("M-001", 1)

    def test_live_harness_lock_prevents_writes(self):
        (self.root / ".research-harness" / "active").mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, "占用"):
            self.recorder().connect([])
        self.assertEqual(self.gh.calls, [])

    def test_publish_same_snapshot_does_not_create_more_prs_or_commits(self):
        self.started()
        head = self.git.head()
        self.recorder().publish("M-001", 1, [], "docs: retry delivery")
        self.assertEqual(head, self.git.head())
        self.assertEqual(len(self.gh.pr_data), 1)

    def test_secret_and_directory_paths_are_rejected(self):
        self.write(".env", "secret=example")
        self.write("token.txt", "ghp_" + "A" * 32)
        for file in (".env", "token.txt", "../outside", ".research-harness/raw.json", "."):
            with self.subTest(file=file), self.assertRaises(ValueError):
                self.recorder().files([file])

    def test_unpublished_intermediate_history_is_checked(self):
        self.started()
        self.write("unrelated.txt", "must never publish")
        self.git.run("add", "unrelated.txt")
        self.git.run("commit", "-m", "example unrelated temporary file")
        self.git.run("rm", "unrelated.txt")
        self.git.run("commit", "-m", "example delete temporary file")
        with self.assertRaisesRegex(ValueError, "中间历史"):
            self.recorder().publish("M-001", 1, [], "docs: example")

    def test_base_change_blocks_merge(self):
        self.sealed()
        base = self.gh.git("rev-parse", "refs/heads/main")
        tree = self.gh.git("rev-parse", base + "^{tree}")
        newer = self.gh.git("commit-tree", tree, "-p", base, "-m", "example concurrent base update")
        self.gh.git("update-ref", "refs/heads/main", newer, base)
        with self.assertRaisesRegex(ValueError, "基线已变化"):
            self.recorder().merge("M-001", 1)
        self.assertNotIn("merge", self.gh.calls)

    def test_new_iteration_after_merge_uses_new_base_and_keeps_history(self):
        self.sealed()
        merged = self.recorder().merge("M-001", 1)["merged"]
        self.edit("- 状态：已验收", "- 状态：待做")
        result = self.recorder().start("M-001", 2, [])
        self.assertEqual(len(self.gh.pr_data), 2)
        self.assertIn("codex/m-001-r2", self.git.current())
        self.assertEqual(self.recorder().state("M-001", 2)["base_sha"], merged)
        self.assertEqual(self.gh.pr_data[0]["state"], "MERGED")
        self.assertIn(self.gh.pr_data[0]["url"], self.gh.pr_data[1]["body"])

    def test_status_while_paused_is_read_only(self):
        self.started()
        self.edit("- 发布：允许", "- 发布：暂停")
        calls = list(self.gh.calls)
        self.assertEqual(self.recorder(owner=None).status("M-001", 1)["pr"]["state"], "OPEN")
        self.assertEqual(calls, self.gh.calls)

    def test_missing_remote_evidence_is_not_published_as_valid(self):
        self.started()
        product = self.write("result.md", "示例本地输出")
        self.edit("## T-002", "### 产物与证据\n| 产物 | SHA256 |\n|---|---|\n| [结果](result.md) | " + r.infra.digest(product) + " |\n\n## T-002")
        remote_head = self.gh.pr(1)["headRefOid"]
        with self.assertRaises(ValueError):
            self.recorder().publish("M-001", 1, [], "docs: pending output")
        self.assertEqual(self.gh.pr(1)["headRefOid"], remote_head)

    def test_merge_base_race_does_not_release_downstream(self):
        self.sealed()
        original = self.gh.merge

        def racing_merge(number, head):
            base = self.gh.git("rev-parse", "refs/heads/main")
            tree = self.gh.git("rev-parse", base + "^{tree}")
            newer = self.gh.git("commit-tree", tree, "-p", base, "-m", "example race")
            self.gh.git("update-ref", "refs/heads/main", newer, base)
            original(number, head)

        self.gh.merge = racing_merge
        with self.assertRaisesRegex(ValueError, "实际合并"):
            self.recorder().merge("M-001", 1)
        self.assertEqual(self.gh.pr(1)["state"], "MERGED")
        self.assertIsNone(self.recorder().state("M-001", 1).get("verified_merge"))

    def test_line_ending_filter_cannot_mislabel_source_hash(self):
        self.git.run("config", "core.autocrlf", "true")
        path = self.root / "TASKS.md"
        path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
        with self.assertRaisesRegex(ValueError, "相同字节"):
            self.connected()
        self.assertFalse(self.git.exists_remote("main"))

    def test_actual_main_entry_connect_with_fake_gh(self):
        original_run = subprocess.run

        def transport(args, *pos, **kwargs):
            if args[0] != "gh":
                result = original_run(args, *pos, **kwargs)
                if "get-url" in args and result.returncode == 0:
                    result.stdout = "https://github.com/example/research-fixture.git\n"
                return result
            if args[1:3] == ["api", "repos/example/research-fixture"]:
                output = json.dumps(self.gh.info())
            elif args[1] == "api" and "/issues?" in args[2]:
                output = json.dumps([self.gh.issues()])
            elif args[1:3] == ["issue", "create"]:
                self.gh.issue_create(kwargs.get("input")); output = "https://github.com/example/research-fixture/issues/1"
            elif args[1:3] == ["issue", "pin"]:
                self.gh.issue_pin(int(args[3])); output = ""
            elif args[1:3] == ["issue", "edit"]:
                self.gh.issue_edit(int(args[3]), kwargs.get("input")); output = ""
            else:
                raise AssertionError("Unexpected network command: " + str(args))
            return subprocess.CompletedProcess(args, 0, output, "")

        argv = [str(Path(r.__file__)), "connect", "--root", str(self.root), "--owner", "示例主持者"]
        with patch("subprocess.run", side_effect=transport), patch.object(sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as stopped:
                runpy.run_path(r.__file__, run_name="__main__")
        self.assertEqual(stopped.exception.code, 0)
        self.assertIn("T-001", self.gh.issue_data[0]["body"])

    def test_updated_main_can_be_integrated_without_claiming_its_files(self):
        self.sealed()
        base = self.gh.git("rev-parse", "refs/heads/main")
        other = self.base / "另一个控制者"
        r.command(["git", "clone", "-b", "main", str(self.bare), str(other)])
        other_git = r.Git(other)
        other_git.run("config", "user.name", "Example other")
        other_git.run("config", "user.email", "other@invalid.local")
        (other / "other-module.txt").write_text("Example accepted upstream", encoding="utf-8")
        other_git.commit(["other-module.txt"], "example separate module")
        other_git.run("push", "origin", "main")
        latest = self.git.remote_head("main")
        self.assertNotEqual(base, latest)
        self.git.run("merge", "--no-edit", latest)
        self.recorder().publish("M-001", 1, [], "docs: integrate new mainline")
        self.recorder().attest("M-001", 1, ["artifacts/均值结果.md"])
        state = self.recorder().state("M-001", 1)
        self.assertEqual(state["scope_base"], latest)
        self.assertNotIn("other-module.txt", state["files"])
        self.assertEqual(len(state["prior_seals"]), 1)
        self.assertTrue(self.recorder().merge("M-001", 1)["merged"])


if __name__ == "__main__":
    unittest.main()
