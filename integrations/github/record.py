"""Opt-in GitHub process records. No model calls and no task-status writes.

Git is real; the GitHub transport is injectable for isolated behavioral tests.
Only the CLI's explicit mutation commands publish. status is read-only.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "research-execution" / "scripts"))
import research_infra as infra
import markdown_tasks as md

META = ".research-github"
ISSUE_MARKER = "<!-- research-max:overview:v1 -->"
PR_MARKER = "<!-- research-max:module:"
RESERVED = {".git", META, ".research-harness", ".claude"}


class CommandError(ValueError):
    pass


def clean_error(text):
    text = re.sub(r"(?i)(authorization|api[_-]?key|token|password)(\s*[:=]\s*)\S+", r"\1\2[redacted]", text)
    text = re.sub(r"https://[^\s/@]+:[^\s/@]+@", "https://[redacted]@", text)
    text = re.sub(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,})\b", "[redacted]", text)
    return text[-1800:]


def command(args, cwd=None, text=None, check=True):
    result = subprocess.run(args, cwd=cwd, input=text, capture_output=True,
                            encoding="utf-8", errors="strict", timeout=120,
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if check and result.returncode:
        raise CommandError(f"{args[0]}失败（{result.returncode}）：{clean_error(result.stderr or result.stdout)}")
    return result


class Git:
    def __init__(self, root):
        self.root = root

    def run(self, *args, check=True):
        return command(["git", "--literal-pathspecs", "-c", "core.quotepath=false", *args], self.root, check=check)

    def text(self, *args):
        return self.run(*args).stdout.strip()

    def head(self):
        result = self.run("rev-parse", "--verify", "HEAD", check=False)
        return result.stdout.strip() if result.returncode == 0 else None

    def current(self):
        return self.text("symbolic-ref", "--short", "HEAD")

    def origin(self):
        return self.run("remote", "get-url", "origin", check=False)

    def remote_head(self, branch):
        self.run("fetch", "--no-tags", "origin", branch)
        return self.text("rev-parse", "FETCH_HEAD")

    def exists_remote(self, branch):
        return bool(self.text("ls-remote", "--heads", "origin", "refs/heads/" + branch))

    def paths(self, *args):
        return [p for p in self.run(*args, "-z").stdout.split("\0") if p]

    def tracked_at(self, sha):
        return self.paths("ls-tree", "-r", "--name-only", sha)

    def blob(self, spec):
        result = subprocess.run(["git", "cat-file", "blob", spec], cwd=self.root,
                                capture_output=True, timeout=120,
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if result.returncode:
            raise ValueError("无法读取提交中的文件")
        return result.stdout

    def commit(self, files, message):
        if not infra.valid_text(message):
            raise ValueError("提交说明须描述实际变化")
        self.run("add", "--all", "--", *files)
        diff = self.run("diff", "--cached", "--quiet", "--", *files, check=False)
        if diff.returncode not in (0, 1):
            raise CommandError(clean_error(diff.stderr))
        if diff.returncode:
            # --only leaves unrelated staged changes in the user's index.
            self.run("commit", "--only", "-m", message, "--", *files)
        return self.head()


class GitHub:
    def __init__(self, repo):
        self.repo = repo

    def run(self, *args, text=None):
        return command(["gh", *args], text=text).stdout.strip()

    def info(self):
        return json.loads(self.run("api", "repos/" + self.repo))

    def create(self):
        self.run("repo", "create", self.repo, "--private", "--description", "Research execution records")

    def issues(self):
        pages = json.loads(self.run("api", "repos/" + self.repo + "/issues?state=all&per_page=100", "--paginate", "--slurp"))
        return [i for page in pages for i in page if "pull_request" not in i]

    def issue_create(self, body):
        self.run("issue", "create", "--repo", self.repo, "--title", "research-max 进度总览", "--body-file", "-", text=body)

    def issue_edit(self, number, body):
        self.run("issue", "edit", str(number), "--repo", self.repo, "--body-file", "-", text=body)

    def issue_pin(self, number):
        try:
            self.run("issue", "pin", str(number), "--repo", self.repo)
        except CommandError as exc:
            if "already pinned" not in str(exc).casefold():
                raise

    def prs(self, branch, base):
        return json.loads(self.run("pr", "list", "--repo", self.repo, "--head", branch, "--base", base,
                                   "--state", "all", "--limit", "100", "--json", "number,url,state,isDraft,headRefOid,body"))

    def pr_create(self, branch, base, title, body):
        self.run("pr", "create", "--repo", self.repo, "--head", branch, "--base", base,
                 "--draft", "--title", title, "--body-file", "-", text=body)

    def pr_edit(self, number, body):
        self.run("pr", "edit", str(number), "--repo", self.repo, "--body-file", "-", text=body)

    def pr(self, number):
        return json.loads(self.run("pr", "view", str(number), "--repo", self.repo,
                                   "--json", "number,url,state,isDraft,headRefOid,baseRefOid,baseRefName,headRefName,mergeCommit,body"))

    def ready(self, number):
        self.run("pr", "ready", str(number), "--repo", self.repo)

    def merge(self, number, head):
        # No --admin, force push, bypass, auto-merge queue or reviewer request.
        self.run("pr", "merge", str(number), "--repo", self.repo, "--merge", "--match-head-commit", head)


def atomic_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    os.replace(temporary, path)


def checksum(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def safe_path(root, name, existing=True):
    if not isinstance(name, str) or not name or "\\" in name or ":" in name:
        raise ValueError("发布路径须为使用/的项目相对文件路径")
    path = Path(name)
    if path.is_absolute() or any(p in {"..", "."} for p in path.parts) or not path.parts:
        raise ValueError("拒绝越界发布路径")
    if any(p.casefold() in RESERVED for p in path.parts):
        raise ValueError(f"运行配置/原始日志不发布：{name}")
    if any(p.casefold().startswith(".env") or p.casefold() in {"id_rsa", "id_ed25519", "credentials.json", "settings.local.json"} for p in path.parts):
        raise ValueError(f"凭据文件不发布：{name}")
    target = root / path
    cursor = target
    while cursor != root:
        if cursor.is_symlink() or (hasattr(cursor, "is_junction") and cursor.is_junction()):
            raise ValueError(f"发布路径含链接/目录联接：{name}")
        cursor = cursor.parent
    if not target.resolve().is_relative_to(root):
        raise ValueError("发布路径越出项目")
    if existing and not target.is_file():
        raise ValueError(f"发布文件不存在：{name}")
    if target.exists():
        if not target.is_file():
            raise ValueError("须逐个指定文件，不接受目录或通配符")
        if target.stat().st_size > 10 * 1024 * 1024:
            raise ValueError(f"大文件请使用外部位置及SHA256引用：{name}")
        sample = target.read_bytes()
        if re.search(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,})\b", sample):
            raise ValueError(f"检测到疑似凭据，未发布：{name}")
    return target


class Recorder:
    def __init__(self, root, owner=None, tasks=None, github=None, git=None):
        self.root = Path(root).resolve()
        self.board = infra.load_tasks(self.root, tasks)
        self.control = self.board.get("_github")
        if not self.control:
            raise ValueError("未启用GitHub记录；读取项目或确认方案不构成发布授权")
        report = infra.check(self.root, _board=self.board)
        if not report["ok"]:
            raise ValueError("任务检查未通过：" + "; ".join(report["errors"]))
        self.owner, self.git = owner, git or Git(self.root)
        self.repo, self.base = self.control["仓库"], self.control["基线分支"]
        self.gh = github or GitHub(self.repo)
        self.meta = self.root / META
        if self.meta.is_symlink() or (hasattr(self.meta, "is_junction") and self.meta.is_junction()) or not self.meta.resolve().is_relative_to(self.root):
            raise ValueError("运行记录目录不能是链接或越界路径")
        self.project_file = self.meta / "project.json"
        self.project = infra.read_json(self.project_file) if self.project_file.exists() else None
        if self.project and (self.project["repo"] != self.repo or self.project["base"] != self.base or self.project["tasks"] != self.board["_source"]):
            raise ValueError("仓库/基线/任务源与已登记接入不一致；不能静默改绑")
        self.by_id = {t["id"]: t for t in self.board["tasks"]}

    def authorized(self):
        if self.control["当前接手者"] != self.owner or self.control["发布"] != "允许":
            raise ValueError("发布已暂停/结束，或当前接手者不匹配")
        if not infra.sources_unchanged(self.root, self.board):
            raise ValueError("任务/计划已改变，须重新读取后操作")
        if (self.root / ".research-harness" / "active").exists():
            raise ValueError("Claude桥接仍占用项目；在安全交接点发布，不改写执行中的输入")
        workspace_key = hashlib.sha256(os.path.normcase(str(self.root)).encode("utf-8")).hexdigest()[:32]
        if (self.root.parent / f".research-harness-{workspace_key}.lock").exists():
            raise ValueError("此目录被另一个项目的Claude桥接作为执行副本占用")

    @contextmanager
    def mutation(self):
        self.authorized()
        self.meta.mkdir(exist_ok=True)
        lock = self.meta / "operation.lock"
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            raise ValueError("GitHub操作仍占用；先核实原进程，不能并发发布或盲删锁") from None
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as out:
                json.dump({"pid": os.getpid(), "owner": self.owner, "created": infra.now()}, out)
            yield
        finally:
            lock.unlink(missing_ok=True)

    def save_project(self):
        atomic_json(self.project_file, self.project)

    def module(self, module_id):
        found = [m for m in self.board.get("modules", []) if m["id"] == module_id]
        if len(found) != 1:
            raise ValueError("须指定存在且唯一的模块")
        module = found[0]
        if not set(module["tasks"]).issubset(self.control["指定任务"]):
            raise ValueError("模块包含未授权任务；不能由分组扩大范围")
        return module

    def location(self, module_id, iteration):
        self.module(module_id)
        if not isinstance(iteration, int) or iteration < 1:
            raise ValueError("实施轮次须为正整数")
        path = self.meta / "modules" / module_id / f"r{iteration}.json"
        if not path.resolve().is_relative_to(self.meta.resolve()) or any(p.is_symlink() or (hasattr(p, "is_junction") and p.is_junction()) for p in (path, path.parent, path.parent.parent)):
            raise ValueError("模块运行记录路径不能是链接或越界")
        return path

    def state(self, module_id, iteration):
        path = self.location(module_id, iteration)
        if not path.exists():
            raise ValueError("模块尚未启动；不能猜测最近PR")
        return infra.read_json(path)

    def save(self, state):
        atomic_json(self.location(state["module"], state["iteration"]), state)

    def module_binding(self, module):
        return checksum({"module": {k: v for k, v in module.items() if not k.startswith("_")},
                         "requirements": {tid: infra.requirements_basis(self.by_id[tid]) for tid in module["tasks"]}})

    def files(self, names):
        result = list(dict.fromkeys(names))
        for name in result:
            target = safe_path(self.root, name, existing=False)
            if not target.exists() and self.git.run("ls-files", "--error-unmatch", "--", name, check=False).returncode:
                raise ValueError(f"文件既不存在也非已跟踪删除：{name}")
        return result

    def required(self):
        return list(dict.fromkeys([self.board["_source"], "project.json"] + ([self.board["_plan_source"]] if self.board.get("_plan_source") else [])))

    def repo_guard(self):
        info = self.gh.info()
        if not info.get("private") or not info.get("permissions", {}).get("push"):
            raise ValueError("须为当前身份可写的私有仓库")
        if not info.get("allow_merge_commit", True):
            raise ValueError("仓库禁用merge commit；保留现有策略，先讨论接入方式")
        if info.get("archived"):
            raise ValueError("仓库已归档")
        return info

    def repo_ready(self):
        if not self.project:
            raise ValueError("先接入明确的私有仓库")
        actual = Path(self.git.text("rev-parse", "--show-toplevel")).resolve()
        if actual != self.root:
            raise ValueError("项目根必须等于Git工作区根；不能发布父项目")
        if not self.origin_matches(self.git.origin().stdout.strip()):
            raise ValueError("origin与指定仓库不匹配")
        self.repo_guard()

    def origin_matches(self, url):
        return url.casefold() in {f"https://github.com/{self.repo}.git".casefold(),
                                  f"https://github.com/{self.repo}".casefold(),
                                  f"git@github.com:{self.repo}.git".casefold(),
                                  f"ssh://git@github.com/{self.repo}.git".casefold()}

    def blob_link(self, sha, name, label=None):
        label = escape(label or name).replace("[", "\\[").replace("]", "\\]")
        return f"[{label}](https://github.com/{self.repo}/blob/{sha}/{quote(name, safe='/')})"

    def ensure_issue(self):
        matches = [i for i in self.gh.issues() if ISSUE_MARKER in (i.get("body") or "")]
        if len(matches) > 1:
            raise ValueError("发现多份进度总览，须先核对，不能猜测")
        if not matches:
            self.gh.issue_create(ISSUE_MARKER + "\n# 实验推进总览\n\n正在建立初始记录；未宣称任何任务完成。")
            matches = [i for i in self.gh.issues() if ISSUE_MARKER in (i.get("body") or "")]
        if len(matches) != 1:
            raise ValueError("总览创建结果未能确认；下次先查询远端，不重复盲建")
        issue = matches[0]
        self.project["issue"] = {"number": issue["number"], "url": issue.get("html_url", issue.get("url"))}
        self.save_project()
        self.gh.issue_pin(issue["number"])

    def find_pr(self, state):
        if state.get("pr"):
            result = self.gh.pr(state["pr"]["number"])
        else:
            found = self.gh.prs(state["branch"], self.base)
            if len(found) > 1:
                raise ValueError("分支存在多份PR；须核对而非猜测")
            if not found:
                return None
            result = self.gh.pr(found[0]["number"])
        marker = f"{PR_MARKER}{state['module']}:r{state['iteration']} -->"
        if marker not in (result.get("body") or "") or result["headRefName"] != state["branch"] or result["baseRefName"] != self.base:
            raise ValueError("PR身份/基线不匹配")
        return result

    def overview(self, sha):
        if not infra.sources_unchanged(self.root, self.board):
            raise ValueError("任务/计划在发布期间变化；不生成过期总览")
        for name in self.required():
            self.committed_file(sha, name)
        lines = [ISSUE_MARKER, "# 实验推进总览（派生）", "", f"更新时间：{infra.now()}；来源提交：`{sha}`。",
                 f"任务来源：{self.blob_link(sha, self.board['_source'])}；SHA256：`{self.board['_sha256']}`。",
                 "只展示最后成功发布的快照；不是实时终端，也不从GitHub反向改写任务状态。", "",
                 "| 模块 | 任务记录 | GitHub集成情况 | 共同产出 |", "|---|---|---|---|"]
        for module in self.board.get("modules", []):
            attempts = sorted((self.meta / "modules" / module["id"]).glob("r*.json"), key=lambda p: int(p.stem[1:]))
            integration = "尚未建立PR"
            if attempts:
                state = infra.read_json(attempts[-1])
                pr = self.find_pr(state)
                if pr:
                    integration = f"[{'已合并' if pr['state'] == 'MERGED' else '关闭未合并' if pr['state'] == 'CLOSED' else '草稿' if pr['isDraft'] else '待合并'}]({pr['url']})"
                    if pr["state"] == "MERGED" and state.get("verified_merge") != (pr.get("mergeCommit") or {}).get("oid"):
                        integration += "（集成版本尚未核实）"
            members = "；".join(tid + "：" + md.LABELS.get(self.by_id[tid]["status"], "未知") for tid in module["tasks"])
            lines.append(f"| {module['id']} | {escape(members)} | {integration} | {escape(module['outcome'])} |")
        lines += ["", "## 当前工作与下一步", ""]
        for task in self.board["tasks"]:
            if task["id"] in self.control["指定任务"]:
                lines.append(f"- {task['id']}（{md.LABELS.get(task['status'], '未知')}）：{escape(task.get('progress') or task.get('blocked_reason') or task.get('defer_reason') or '见任务正文')} ")
        lines += ["", "任务已验收与PR已合并分别记录；负结果可以验收，合并不代表科学假设成立。", ""]
        self.gh.issue_edit(self.project["issue"]["number"], "\n".join(lines))

    def pr_body(self, state, sha):
        module = self.module(state["module"])
        lines = [f"{PR_MARKER}{state['module']}:r{state['iteration']} -->", f"# {module['outcome']}", "",
                 f"本轮：{state['module']} / r{state['iteration']}；起点：`{state['base_sha']}`；本次快照：`{sha}`。",
                 f"[实验总览]({self.project['issue']['url']})；{self.blob_link(sha, self.board['_source'], '权威任务快照')}。",
                 "本PR复用既有验收，不增加模型审核轮次。", "", "## 成员任务", ""]
        for tid in module["tasks"]:
            task = self.by_id[tid]
            basis = infra.requirements_basis(task)
            plan_link = self.blob_link(sha, self.board["_plan_source"], "计划依据") if self.board.get("_plan_source") else "见任务正文"
            lines += [f"- **{tid}：{md.LABELS[task['status']]}**；要求 {basis['version']} / `{basis['sha256']}`。",
                      f"  对应计划：{plan_link}；进展与下一步：{escape(task.get('progress') or task.get('blocked_reason') or task.get('defer_reason') or '见任务正文')}。"]
            for evidence in task.get("outputs", []) + ([task["review"]] if task.get("review") else []):
                lines.append("  证据：" + self.blob_link(sha, evidence["path"]) + f"；SHA256 `{evidence['sha256']}`。")
        lines += ["", "## 集成条件", module["integration"], "", "尚未合并不等于任务未验收；实际合并情况以GitHub为准。", ""]
        if state.get("previous_pr"):
            lines.append(f"前一轮：{state['previous_pr']}。")
        return "\n".join(lines)

    def connect(self, files, create_private=False):
        with self.mutation():
            command(["git", "check-ref-format", "--branch", self.base])
            top = self.git.run("rev-parse", "--show-toplevel", check=False)
            if top.returncode == 0 and Path(top.stdout.strip()).resolve() != self.root:
                raise ValueError("项目位于其他Git仓库内；拒绝发布父项目或嵌套初始化")
            try:
                self.repo_guard()
            except CommandError as exc:
                if not create_private or "HTTP 404" not in str(exc):
                    raise
                self.gh.create()
                self.repo_guard()
            if top.returncode:
                self.git.run("init", "-b", self.base)
            if self.git.current() != self.base:
                raise ValueError("初次接入须位于约定基线分支；不自动切换现有工作")
            url = f"https://github.com/{self.repo}.git"
            remote = self.git.origin()
            if remote.returncode:
                self.git.run("remote", "add", "origin", url)
            elif not self.origin_matches(remote.stdout.strip()):
                raise ValueError("origin不匹配；不覆盖已有远端")
            names = self.files(files + self.required())
            remote_sha = None
            if self.git.exists_remote(self.base):
                remote_sha = self.git.remote_head(self.base)
                if self.git.head() != remote_sha:
                    # A retry may have committed locally before its first push.
                    pending = self.project and self.project.get("bootstrap_commit")
                    if not pending or self.git.head() != pending or self.git.text("rev-parse", "HEAD^") != remote_sha:
                        raise ValueError("接入前须同步基线；不发布未登记的本地历史或覆盖远端")
            elif self.git.head() and not (self.project and self.project.get("bootstrap_commit") == self.git.head()):
                raise ValueError("新远端不能隐式接收已有本地历史；先核对历史发布范围")
            if not self.project:
                self.project = dict(schema_version=1, repo=self.repo, base=self.base, tasks=self.board["_source"])
                self.save_project()
            exclude = Path(self.git.text("rev-parse", "--git-path", "info/exclude"))
            if not exclude.is_absolute():
                exclude = self.root / exclude
            prior = exclude.read_text(encoding="utf-8") if exclude.exists() else ""
            if "/" + META + "/" not in prior.splitlines():
                exclude.parent.mkdir(parents=True, exist_ok=True)
                exclude.write_text(prior.rstrip() + "\n/" + META + "/\n", encoding="utf-8")
            self.ensure_issue()
            readme = safe_path(self.root, "README.md", existing=False)
            current = readme.read_text(encoding="utf-8") if readme.exists() else "# 实验项目\n"
            nav = f"[实验推进总览]({self.project['issue']['url']})"
            if nav not in current:
                readme.write_text(current.rstrip() + f"\n\n{nav}：查看当前模块、缺口和下一步；main保存最近合并版本。\n", encoding="utf-8")
            names = self.files(names + ["README.md"])
            self.project["bootstrap_files"] = names
            self.save_project()
            self.authorized()
            sha = self.git.commit(names, "docs: establish research execution baseline")
            self.project["bootstrap_commit"] = sha
            self.save_project()
            self.history_guard(remote_sha, sha, set(names))
            for name in self.required():
                self.committed_file(sha, name)
            self.authorized()
            self.git.run("push", "origin", f"{sha}:refs/heads/{self.base}")
            if self.git.remote_head(self.base) != sha:
                raise ValueError("初始基线推送后远端变化，须核对")
            self.overview(sha)
            return {"repo": self.repo, "issue": self.project["issue"], "commit": sha}

    def other_open_modules(self, module_id=None, iteration=None):
        for path in (self.meta / "modules").glob("*/r*.json"):
            state = infra.read_json(path)
            if (state["module"], state["iteration"]) == (module_id, iteration):
                continue
            pr = self.find_pr(state)
            if not pr or pr["state"] == "OPEN":
                raise ValueError("已有尚未结束的模块；首版串行集成，先接续或明确关闭原PR")
            if pr["state"] == "MERGED" and state.get("verified_merge") != (pr.get("mergeCommit") or {}).get("oid"):
                raise ValueError("已有合并结果尚未核实；先恢复原模块的合并查询")

    def dependencies_ready(self, module, base_sha):
        for tid in module["tasks"]:
            for dependency in self.by_id[tid]["depends_on"]:
                if dependency in module["tasks"]:
                    continue
                task = self.by_id[dependency]
                if task["status"] != "ACCEPTED":
                    raise ValueError(f"范围外/上游依赖尚未验收：{dependency}")
                for item in task.get("outputs", []) + ([task["review"]] if task.get("review") else []):
                    self.committed_file(base_sha, item["path"])

    def start(self, module_id, iteration, files):
        with self.mutation():
            self.repo_ready()
            module = self.module(module_id)
            self.other_open_modules(module_id, iteration)
            path = self.location(module_id, iteration)
            if path.exists():
                state = infra.read_json(path)
                pr = self.find_pr(state)
                if pr and pr["state"] != "OPEN":
                    raise ValueError("该轮已结束；后续修改使用新轮次，不复用旧分支")
            else:
                base_sha = self.git.remote_head(self.base)
                self.dependencies_ready(module, base_sha)
                if self.git.run("merge-base", "--is-ancestor", self.git.head(), base_sha, check=False).returncode:
                    raise ValueError("当前提交未进入基线；不把无关本地历史带入新模块")
                if not any(self.by_id[t]["status"] != "ACCEPTED" for t in module["tasks"]):
                    raise ValueError("模块已全部验收；先明确本轮修回要求或新增有范围的核查任务")
                branch = f"codex/{module_id.lower()}-r{iteration}"
                if self.git.run("show-ref", "--verify", "--quiet", "refs/heads/" + branch, check=False).returncode == 0 or self.git.exists_remote(branch):
                    raise ValueError("目标分支已存在但无本地登记；须核对，不能占用他人分支")
                earlier = sorted(path.parent.glob("r*.json"), key=lambda p: int(p.stem[1:]))
                if earlier and iteration <= int(earlier[-1].stem[1:]):
                    raise ValueError("新实施轮次须递增")
                previous = infra.read_json(earlier[-1]) if earlier else None
                state = dict(module=module_id, iteration=iteration, branch=branch, base_sha=base_sha,
                             created=infra.now(), files=[], previous_pr=(previous or {}).get("pr", {}).get("url"))
                self.save(state)
            if self.git.current() != state["branch"]:
                exists = self.git.run("show-ref", "--verify", "--quiet", "refs/heads/" + state["branch"], check=False).returncode == 0
                self.git.run("switch", state["branch"]) if exists else self.git.run("switch", "-c", state["branch"], state["base_sha"])
            launch = f"research-records/modules/{module_id}/r{iteration}.md"
            target = safe_path(self.root, launch, existing=False)
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(f"# 模块启动记录（历史快照）\n\n- 模块：{module_id}\n- 实施轮次：r{iteration}\n"
                                  f"- 起点提交：{state['base_sha']}\n- 创建时间：{state['created']}\n"
                                  f"- 成员任务：{'、'.join(module['tasks'])}\n- 要求摘要：{self.module_binding(module)}\n\n"
                                  "当前状态以项目权威任务Markdown为准；此记录不持续维护状态。\n", encoding="utf-8")
            state["files"] = self.files(state["files"] + files + self.required() + [launch])
            self.save(state)
            return self._publish(state, "docs: start " + module_id + f" r{iteration}")

    def publish(self, module_id, iteration, files, message):
        with self.mutation():
            self.repo_ready()
            state = self.state(module_id, iteration)
            state["files"] = self.files(state["files"] + files + self.required())
            self.save(state)
            return self._publish(state, message)

    def _publish(self, state, message):
        if self.git.current() != state["branch"]:
            raise ValueError("当前工作区不在登记模块分支；不自动切换执行工作区")
        pr = self.find_pr(state)
        if pr and pr["state"] != "OPEN":
            raise ValueError("PR已结束；先核实合并或使用新轮次")
        self.files(state["files"])
        sha = self.git.commit(state["files"], message)
        latest_base = self.git.remote_head(self.base)
        scope_base = state.get("scope_base", state["base_sha"])
        if self.git.run("merge-base", "--is-ancestor", latest_base, sha, check=False).returncode == 0:
            scope_base = latest_base
        changed = set(self.git.paths("diff", "--name-only", scope_base, sha))
        if not changed.issubset(state["files"]):
            raise ValueError("分支含未登记变更，未推送：" + "、".join(sorted(changed - set(state["files"]))))
        for name in changed:
            safe_path(self.root, name, existing=False)
        self.history_guard(scope_base, sha, set(state["files"]))
        for name in self.required():
            self.committed_file(sha, name)
        for tid in self.module(state["module"])["tasks"]:
            task = self.by_id[tid]
            for item in task.get("outputs", []) + ([task["review"]] if task.get("review") else []):
                self.committed_file(sha, item["path"])
        if not infra.sources_unchanged(self.root, self.board):
            raise ValueError("提交期间任务/计划变化，未推送")
        state["head"] = sha
        state["scope_base"] = scope_base
        self.save(state)
        self.git.run("push", "origin", f"{sha}:refs/heads/{state['branch']}")
        body = self.pr_body(state, sha)
        if not pr:
            self.gh.pr_create(state["branch"], self.base, f"{state['module']} r{state['iteration']}：{self.module(state['module'])['outcome']}", body)
            pr = self.find_pr(state)
        else:
            pr = self.find_pr(state)
        if not pr:
            raise ValueError("PR创建结果未确认；下次先查询")
        if pr["state"] != "OPEN" or pr["headRefOid"] != sha:
            raise ValueError("发布期间PR关闭/合并或头提交漂移；先核对实际远端")
        state["pr"] = {"number": pr["number"], "url": pr["url"]}
        self.save(state)
        self.gh.pr_edit(pr["number"], body)
        state["published_head"] = sha
        self.save(state)
        self.overview(sha)
        return {"module": state["module"], "commit": sha, "pr": state["pr"]}

    def history_guard(self, base, head, allowed):
        """Publishing a branch publishes its intermediate history too."""
        for commit in self.git.text("rev-list", base + ".." + head if base else head).splitlines():
            paths = set(self.git.paths("diff-tree", "--root", "-m", "--no-commit-id", "--name-only", "-r", commit))
            for name in paths:
                entry = self.git.text("ls-tree", commit, "--", name)
                if name not in allowed:
                    # A merge from the already-published mainline may import files
                    # outside this module. Only unchanged baseline bytes qualify.
                    if base and entry == self.git.text("ls-tree", base, "--", name):
                        continue
                    raise ValueError("分支中间历史含未登记文件；即使最后删除也不能发布")
                safe_path(self.root, name, existing=False)
                if not entry:  # A deletion has no new blob.
                    continue
                if not entry.startswith(("100644 blob ", "100755 blob ")):
                    raise ValueError("不发布符号链接、子模块或特殊Git条目")
                spec = commit + ":" + name
                if int(self.git.text("cat-file", "-s", spec)) > 10 * 1024 * 1024:
                    raise ValueError("中间提交含大文件，请以外部版本引用替代")
                if re.search(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,})\b", self.git.blob(spec)):
                    raise ValueError("中间提交含疑似凭据，未发布")

    def committed_file(self, sha, name):
        path = safe_path(self.root, name)
        actual = infra.digest(path)
        expected = hashlib.sha256(self.git.blob(sha + ":" + name)).hexdigest()
        if actual != expected:
            raise ValueError(f"文件未以相同字节提交到所审版本：{name}；核对未提交变化及Git换行/clean过滤，不能重签证据凑通过")
        return actual

    def evidence(self, module):
        records = self.required()
        for tid in module["tasks"]:
            task = self.by_id[tid]
            if task["status"] != "ACCEPTED":
                raise ValueError(f"必要任务尚未验收：{tid}")
            infra.requirements_basis(task)
            records += [x["path"] for x in task.get("outputs", [])]
            if task.get("review"):
                records.append(task["review"]["path"])
        return list(dict.fromkeys(records))

    def clean_module(self, state):
        if self.git.current() != state["branch"]:
            raise ValueError("当前分支与模块不匹配")
        dirty = set(self.git.paths("diff", "HEAD", "--name-only"))
        if dirty & set(state["files"]):
            raise ValueError("模块仍有未提交变更；先发布再封存验收")
        changed = set(self.git.paths("diff", "--name-only", state.get("scope_base", state["base_sha"]), self.git.head()))
        if not changed.issubset(state["files"]):
            raise ValueError("模块包含未登记变更")

    def attest(self, module_id, iteration, evidence):
        """Seal existing review/check evidence, never run another model review."""
        with self.mutation():
            self.repo_ready()
            module, state = self.module(module_id), self.state(module_id, iteration)
            self.clean_module(state)
            pr = self.find_pr(state)
            head, base = self.git.head(), self.git.remote_head(self.base)
            if not pr or pr["state"] != "OPEN" or pr["headRefOid"] != head or state.get("published_head") != head:
                raise ValueError("本地、已发布快照和PR提交不一致")
            if self.git.run("merge-base", "--is-ancestor", base, head, check=False).returncode:
                raise ValueError("基线已有新提交；先集成并按影响检查，再重新封存")
            if not evidence:
                raise ValueError("须引用已有集成/覆盖检查证据；不要求新建审核报告")
            paths = self.files(self.evidence(module) + evidence)
            bindings = {name: self.committed_file(head, name) for name in paths}
            seal = dict(head=head, base=base, module_binding=self.module_binding(module), evidence=bindings,
                        reviewer=self.owner, recorded=infra.now())
            if state.get("seal"):
                previous = state["seal"]
                if {k: v for k, v in previous.items() if k != "recorded"} == {k: v for k, v in seal.items() if k != "recorded"}:
                    seal = previous
                else:
                    state.setdefault("prior_seals", []).append(previous)
            state["seal"] = seal
            self.save(state)
            return {"head": head, "base": base, "note": "封存已有验收声明及文件版本；未增加模型审核，也不认证科学判断"}

    def _confirm_merge(self, state, pr):
        seal = state.get("seal")
        merged = (pr.get("mergeCommit") or {}).get("oid")
        if not seal or not merged:
            raise ValueError("远端已合并，但缺少可核对的本轮封存；不得继续下游")
        remote = self.git.remote_head(self.base)
        parents = self.git.text("rev-list", "--parents", "-n", "1", merged).split()[1:]
        if parents != [seal["base"], seal["head"]] or self.git.text("rev-parse", merged + "^{tree}") != self.git.text("rev-parse", seal["head"] + "^{tree}"):
            raise ValueError("实际合并基线/内容与封存不一致；停止后继派发，核对受影响集成，不回滚他人工作")
        if self.git.run("merge-base", "--is-ancestor", merged, remote, check=False).returncode:
            raise ValueError("合并结果不在当前远端基线历史中")
        state["verified_merge"] = merged
        self.save(state)
        self.overview(merged)
        return {"merged": merged, "pr": pr["url"], "note": "已核实远端合并；未改写任务状态"}

    def merge(self, module_id, iteration):
        with self.mutation():
            self.repo_ready()
            state, module = self.state(module_id, iteration), self.module(module_id)
            pr = self.find_pr(state)
            if pr and pr["state"] == "MERGED":
                return self._confirm_merge(state, pr)
            if not pr or pr["state"] != "OPEN":
                raise ValueError("没有可合并的明确PR")
            self.clean_module(state)
            self.evidence(module)
            seal = state.get("seal")
            if not seal or self.git.head() != seal["head"] or pr["headRefOid"] != seal["head"] or self.module_binding(module) != seal["module_binding"]:
                raise ValueError("封存缺失或审查后提交/要求发生变化")
            if self.git.remote_head(self.base) != seal["base"] or pr["baseRefOid"] != seal["base"]:
                raise ValueError("基线已变化；只补受影响检查后重新封存")
            for name, digest in seal["evidence"].items():
                if self.committed_file(seal["head"], name) != digest:
                    raise ValueError("封存证据已改变")
            self.authorized()
            if pr["isDraft"]:
                self.gh.ready(pr["number"])
            # Server checks/protections remain in force; never request an extra review.
            self.gh.merge(pr["number"], seal["head"])
            actual = self.find_pr(state)
            if not actual or actual["state"] != "MERGED":
                raise ValueError("GitHub尚未确认合并；不显示为已完成，不自动启用队列")
            return self._confirm_merge(state, actual)

    def status(self, module_id=None, iteration=1):
        self.repo_ready()
        result = {"repo": self.repo, "issue": self.project["issue"], "task_source": self.board["_source"],
                  "source_sha256": self.board["_sha256"], "note": "只读查询；不接管、不派发、不修改任务或总览"}
        if module_id:
            state = self.state(module_id, iteration)
            result.update(module=module_id, pr=self.find_pr(state), verified_merge=state.get("verified_merge"),
                          task_states={tid: self.by_id[tid]["status"] for tid in self.module(module_id)["tasks"]})
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("connect", "start", "publish", "attest", "merge", "status"):
        p = sub.add_parser(name)
        p.add_argument("--root", type=Path, required=True)
        p.add_argument("--tasks")
        p.add_argument("--owner", required=name != "status")
        if name not in {"connect"}:
            p.add_argument("--module", required=name != "status", dest="module_id")
            p.add_argument("--iteration", type=int, default=1)
        if name in {"connect", "start", "publish"}:
            p.add_argument("--file", action="append", default=[], dest="files")
        if name == "connect":
            p.add_argument("--create-private", action="store_true")
        if name == "publish":
            p.add_argument("--message", required=True)
        if name == "attest":
            p.add_argument("--evidence", action="append", required=True)
    args = vars(parser.parse_args())
    try:
        name = args.pop("command")
        obj = Recorder(args.pop("root"), args.pop("owner"), args.pop("tasks"))
        result = getattr(obj, name)(**args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"error": clean_error(str(exc)), "note": "不重启实验；先核对本地和远端事实后接续"}, ensure_ascii=False))
        return 1
    return 0


def escape(value):
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("|", "&#124;").replace("\n", "<br>")


if __name__ == "__main__":
    raise SystemExit(main())
