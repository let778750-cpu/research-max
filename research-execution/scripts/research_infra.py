"""Local research bookkeeping. Standard library only; no network or model calls."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import re
import shutil
import sys
import tempfile
from urllib.parse import quote

import markdown_tasks as md
import module_groups as groups

BASE = Path(__file__).resolve().parents[1]
STATUSES = {"TODO", "RUNNING", "REVIEW", "ACCEPTED", "BLOCKED", "DEFERRED"}
DIGEST = re.compile(r"[0-9a-fA-F]{64}\Z")


class CheckFailure(ValueError):
    """Readable inputs violate a task or snapshot precondition (CLI exit 1)."""


def valid_text(value):
    return isinstance(value, str) and md.meaningful(value)


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_json(path):
    with Path(path).open(encoding="utf-8-sig") as stream:
        return json.load(stream)


def write_new(path, data):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def digest(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def local_file(root, relative):
    if not isinstance(relative, str) or not relative.strip():
        raise ValueError("文件路径必须为非空相对路径")
    normalized = relative.replace("\\", "/")
    item = Path(normalized)
    win = PureWindowsPath(relative)
    if item.is_absolute() or win.drive or win.root or ".." in item.parts or ":" in normalized:
        raise ValueError(f"拒绝越界或绝对路径: {relative}")
    root = Path(root).resolve()
    result = (root / item).resolve()
    if not result.is_relative_to(root):
        raise ValueError(f"链接目标越出项目: {relative}")
    if not result.is_file():
        raise ValueError(f"文件不存在: {relative}")
    return result


def checked_record(root, record):
    if not isinstance(record, dict):
        raise ValueError("文件证据必须含path与sha256")
    path = local_file(root, record.get("path"))
    expected = record.get("sha256", "")
    if not isinstance(expected, str) or not DIGEST.fullmatch(expected):
        raise ValueError(f"SHA256格式错误: {record.get('path')}")
    actual = digest(path)
    if actual != expected.lower():
        raise ValueError(f"文件内容已改变: {record['path']}")
    return path


def requirements_basis(task):
    """Bind the declared contract, never progress, outputs or the whole plan."""
    version = task.get("requirements_version")
    if not isinstance(version, str) or not re.fullmatch(r"V[1-9][0-9]*", version):
        raise ValueError("要求版本须为V正整数")
    if not valid_text(task.get("goal")):
        raise ValueError("版本化任务须填写目标与边界")
    criteria = task.get("acceptance_criteria")
    if not isinstance(criteria, list) or not criteria or not all(valid_text(x) for x in criteria):
        raise ValueError("计算要求摘要前须填写实际验收条件")
    deps = task.get("depends_on")
    if not isinstance(deps, list) or not all(isinstance(x, str) for x in deps):
        raise ValueError("计算要求摘要前须填写依赖列表")
    if not isinstance(task.get("inputs", ""), str) or not isinstance(task.get("review_required"), bool):
        raise ValueError("输入与版本须为文字，复核方式须明确")

    def normalized(value):
        return "\n".join(line.rstrip() for line in value.strip().splitlines())

    contract = {"basis_schema": 1, "id": task["id"], "version": version,
                "goal": normalized(task["goal"]), "inputs": normalized(task.get("inputs", "")),
                "criteria": [normalized(x) for x in criteria], "depends_on": sorted(deps),
                "review_required": task["review_required"]}
    sha = hashlib.sha256(json.dumps(contract, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return {"version": version, "sha256": sha}


def read_plan(root, board):
    plan = board.get("plan")
    if plan is None:
        return
    if not isinstance(plan, dict):
        raise ValueError("plan须为含path与revision的对象")
    path = local_file(root, plan.get("path"))
    if path.suffix.lower() != ".md":
        raise ValueError("计划文件须为Markdown")
    before = digest(path)
    actual = md.document_fields(path).get("当前修订")
    if before != digest(path):
        raise ValueError("读取期间计划发生变化，请重新检查")
    board.update(_plan_source=path.relative_to(root).as_posix(), _plan_sha256=before)
    errors = board.setdefault("_errors", [])
    if not isinstance(actual, str) or not re.fullmatch(r"R[1-9][0-9]*", actual):
        errors.append(f"{board['_plan_source']}:1: 计划当前修订须为R正整数")
    if plan.get("revision") != actual or not isinstance(plan.get("revision"), str):
        errors.append(f"{board['_source']}:1: 计划尚未同步（任务声明 {plan.get('revision')}，计划当前 {actual}）")


def sources_unchanged(root, board):
    for path_key, sha_key in (("_source", "_sha256"), ("_plan_source", "_plan_sha256")):
        if board.get(path_key) and digest(local_file(root, board[path_key])) != board[sha_key]:
            return False
    return True


def task_bases(root, tasks_file=None, task_id=None):
    board = load_tasks(root, tasks_file)
    # Plan mismatch can be present while the author is preparing a revision.
    # Computing a digest does not apply that revision or accept any task.
    tasks = board.get("tasks", [])
    if not isinstance(tasks, list) or not all(isinstance(t, dict) and isinstance(t.get("id"), str) for t in tasks):
        raise ValueError("无有效任务列表")
    ids = [t["id"] for t in tasks]
    if len(set(ids)) != len(ids):
        raise ValueError("任务ID重复，无法计算要求摘要")
    if board.get("_parse_errors"):
        raise ValueError("; ".join(board["_parse_errors"]))
    selected = [t for t in tasks if t["id"] == task_id] if task_id else [t for t in tasks if "requirements_version" in t]
    if not selected:
        raise ValueError("未找到指定任务或版本化任务")
    result = [{"task_id": t["id"], **requirements_basis(t)} for t in selected]
    if not sources_unchanged(root, board):
        raise ValueError("读取期间任务或计划发生变化")
    return {"bases": result, "note": "仅计算当前声明要求；不改文件、不代表复核通过"}


def load_tasks(root, tasks_file=None):
    root = Path(root).resolve()
    if tasks_file is None:
        candidates = [name for name in ("TASKS.md", "tasks.json") if (root / name).exists()]
        if len(candidates) != 1:
            raise ValueError("须有且仅有一个默认任务源 TASKS.md 或 tasks.json；双源或自定义文件须用 --tasks 显式指定")
        tasks_file = candidates[0]
    path = local_file(root, tasks_file)
    original = digest(path)
    if path.suffix.lower() == ".md":
        board = md.read_tasks(root, path)
        agreement, modules, errors = groups.read(path)
        if agreement is not None:
            board["_github"] = agreement
        if modules:
            board["modules"] = modules
        board.setdefault("_errors", []).extend(errors)
    elif path.suffix.lower() == ".json":
        board = read_json(path)
    else:
        raise ValueError("任务源仅支持 .md 或兼容 .json")
    if not isinstance(board, dict) or board.get("schema_version") != 1:
        raise ValueError("任务源不是受支持的schema_version=1对象")
    if original != digest(path):
        raise ValueError("读取期间任务源发生变化，请重新检查")
    board.update(_source=path.relative_to(root).as_posix(), _sha256=original)
    board["_parse_errors"] = list(board.get("_errors", []))
    read_plan(root, board)
    return board


def check(root, tasks_file=None, board_file=None, *, _board=None):
    root = Path(root).resolve()
    project = read_json(local_file(root, "project.json"))
    board = _board if _board is not None else load_tasks(root, tasks_file)
    if not isinstance(project, dict) or project.get("schema_version") != 1:
        raise ValueError("project.json不是受支持的schema_version=1对象")
    tasks = board.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise ValueError("tasks必须为非空列表")
    errors, warnings, by_id = list(board.get("_errors", [])), [], {}
    for t in tasks:
        if not isinstance(t, dict) or not isinstance(t.get("id"), str) or not t["id"].strip():
            errors.append("任务缺少有效id")
            continue
        tid = t["id"]
        if tid in by_id:
            errors.append(f"{t.get('_where', tid)}: 重复任务ID {tid}")
        by_id[tid] = t
    if not board.get("plan"):
        warnings.append("兼容记录未登记计划同步信息；本次不核对PLAN修订一致性")
    unbound = [tid for tid, task in by_id.items() if "requirements_version" not in task and task.get("status") in {"REVIEW", "ACCEPTED"}]
    if unbound:
        warnings.append("兼容记录未绑定任务要求版本：" + "、".join(unbound) + "；旧验收是否适用于新要求仍需核对")
    successors = {}
    for tid, task in by_id.items():
        label = task.get("_where", tid)
        following = task.get("successors", [])
        if not isinstance(following, list) or not all(isinstance(x, str) for x in following):
            errors.append(f"{label}: 承接任务须为ID列表")
            following = []
        if "successors" in task and (not following or len(set(following)) != len(following)):
            errors.append(f"{label}: 承接任务为空或重复")
        for target in following:
            if target not in by_id or target == tid:
                errors.append(f"{label}: 承接任务不存在或指向自身 {target}")
        if following and task.get("status") not in {"DEFERRED", "ACCEPTED"}:
            errors.append(f"{label}: 已移交执行职责的旧任务须暂缓或保留原范围已验收；集成父任务请使用依赖")
        successors[tid] = following
        version = task.get("requirements_version")
        if "requirements_version" in task and (not isinstance(version, str) or not re.fullmatch(r"V[1-9][0-9]*", version)):
            errors.append(f"{label}: 要求版本须为V正整数")
        if "self_check_basis" in task and version is None:
            errors.append(f"{label}: 自检依据缺少要求版本")
    active_successors, done_successors = set(), set()

    def visit_successor(tid):
        if tid in active_successors:
            raise ValueError(f"{by_id[tid].get('_where', tid)}: 承接关系成环")
        if tid in done_successors or tid not in successors:
            return
        active_successors.add(tid)
        for next_id in successors[tid]:
            visit_successor(next_id)
        active_successors.remove(tid)
        done_successors.add(tid)

    try:
        for tid in by_id:
            visit_successor(tid)
    except ValueError as exc:
        errors.append(str(exc))
    edges = {}
    for tid, task in by_id.items():
        label = task.get("_where", tid)
        start_errors = len(errors)
        deps = task.get("depends_on")
        if not isinstance(deps, list) or not all(isinstance(d, str) for d in deps):
            errors.append(f"{tid}: depends_on必须是字符串列表")
            deps = []
        if len(set(deps)) != len(deps):
            errors.append(f"{tid}: 重复依赖")
        edges[tid] = deps
        for dep in deps:
            if dep not in by_id:
                errors.append(f"{tid}: 不存在的依赖 {dep}")
            elif successors.get(dep):
                warnings.append(f"{label}: 仍依赖已登记承接关系的 {dep}；核对旧范围是否适用及依赖是否已重接")
        state = task.get("status")
        if not isinstance(state, str) or state not in STATUSES:
            errors.append(f"{tid}: 非法任务状态")
            state = None
        if state in {"RUNNING", "REVIEW", "ACCEPTED"}:
            if not valid_text(task.get("owner")):
                errors.append(f"{tid}: 工作任务缺少负责人")
            criteria = task.get("acceptance_criteria")
            if not isinstance(criteria, list) or not criteria or not all(valid_text(x) for x in criteria):
                errors.append(f"{tid}: 尚未填写验收条件")
            for dep in deps:
                if by_id.get(dep, {}).get("status") != "ACCEPTED":
                    errors.append(f"{tid}: 上游 {dep} 尚未验收")
        if state == "BLOCKED" and not valid_text(task.get("blocked_reason")):
            errors.append(f"{tid}: BLOCKED缺少阻断原因")
        if state == "DEFERRED" and not valid_text(task.get("defer_reason")):
            errors.append(f"{tid}: DEFERRED缺少移出范围的原因")
        if not isinstance(task.get("review_required"), bool):
            errors.append(f"{tid}: review_required须显式为布尔值")
        if state == "REVIEW" and not valid_text(task.get("self_check")):
            errors.append(f"{tid}: 待核验任务缺少自检记录")
        expected_basis = None
        if "requirements_version" in task and state in {"RUNNING", "REVIEW", "ACCEPTED"}:
            try:
                expected_basis = requirements_basis(task)
                if (state == "REVIEW" or (state == "ACCEPTED" and task.get("review_required") is False)) and task.get("self_check_basis") != expected_basis:
                    errors.append(f"{tid}: 自检依据与当前任务要求不匹配；须实际核验后重新绑定")
            except ValueError as exc:
                errors.append(f"{tid}: {exc}")
        if state not in {"REVIEW", "ACCEPTED"}:
            errors[start_errors:] = [e.replace(f"{tid}:", f"{label}:", 1) for e in errors[start_errors:]]
            continue
        outputs = task.get("outputs")
        if not isinstance(outputs, list) or not outputs:
            errors.append(f"{label}: 待核验/验收任务没有产物")
            errors[start_errors:] = [e.replace(f"{tid}:", f"{label}:", 1) for e in errors[start_errors:]]
            continue
        bound, resolved_paths = {}, set()
        for record in outputs:
            try:
                path = checked_record(root, record)
                if path in resolved_paths:
                    raise ValueError("同一产物重复登记")
                resolved_paths.add(path)
                bound[record["path"]] = record["sha256"].lower()
            except (ValueError, OSError) as exc:
                errors.append(f"{tid}: {exc}")
        if state == "REVIEW":
            errors[start_errors:] = [e.replace(f"{tid}:", f"{label}:", 1) for e in errors[start_errors:]]
            continue
        review_record = task.get("review")
        if task.get("review_required") is True and not review_record:
            errors.append(f"{tid}: 缺少独立复核文件")
        if review_record:
            try:
                review_path = checked_record(root, review_record)
                review = md.read_review(root, review_path) if review_path.suffix.lower() == ".md" else read_json(review_path)
                if not isinstance(review, dict):
                    raise ValueError("复核记录须为JSON对象")
                if review.get("task_id") != tid or review.get("verdict") != "ACCEPT":
                    raise ValueError("复核任务或结论不匹配")
                if review.get("artifact_sha256") != bound:
                    raise ValueError("复核未绑定本次全部产物")
                if expected_basis is not None and review.get("requirements_basis") != expected_basis:
                    raise ValueError("验收依据与当前任务要求不匹配；旧回执不能用于新要求")
                if review.get("requirements_basis") is not None and "requirements_version" not in task:
                    raise ValueError("回执已绑定要求版本，但任务缺少要求版本")
                if not isinstance(review.get("checks"), list) or not review["checks"] or not all(valid_text(item) for item in review["checks"]):
                    raise ValueError("复核缺少实际检查内容")
                if task.get("review_required") is True:
                    reviewer = review.get("reviewer")
                    if not valid_text(reviewer) or reviewer == task.get("owner"):
                        raise ValueError("复核者必须声明为实际非作者")
                    if review.get("independent_context") is not True or not valid_text(review.get("context_record")):
                        raise ValueError("缺少独立上下文声明或记录")
            except (ValueError, OSError, TypeError) as exc:
                errors.append(f"{tid}: {exc}")
        elif task.get("review_required") is False and not valid_text(task.get("self_check")):
            errors.append(f"{tid}: 低风险验收缺少自检记录")
        errors[start_errors:] = [e.replace(f"{tid}:", f"{label}:", 1) for e in errors[start_errors:]]
    active, done = set(), set()

    def visit(tid):
        if tid in active:
            raise ValueError(f"{by_id[tid].get('_where', tid)}: 任务依赖成环")
        if tid in done or tid not in by_id:
            return
        active.add(tid)
        for dep in edges[tid]:
            visit(dep)
        active.remove(tid)
        done.add(tid)

    try:
        for tid in by_id:
            visit(tid)
    except ValueError as exc:
        errors.append(str(exc))
    ready = [tid for tid, t in by_id.items() if t.get("status") == "TODO" and all(by_id.get(d, {}).get("status") == "ACCEPTED" for d in edges[tid])]
    if not project.get("name"):
        warnings.append("项目名称尚未填写")
    if board.get("modules") or board.get("_github"):
        errors.extend(groups.validate(board))
        warnings.append("模块共同目标、检查充分性和长期阻塞需实质判断；分组结构通过不证明粒度合理")
    warnings.append("本检查不认证科学正确、复核独立性、完整冻结范围或投稿合规")
    if not sources_unchanged(root, board):
        errors.append("读取期间任务源或计划发生变化，请重新检查")
    report = {"ok": not errors, "errors": errors, "warnings": warnings, "counts": dict(Counter(str(t.get("status")) for t in by_id.values())), "ready_tasks": ready if not errors else [], "task_source": board["_source"], "plan": board.get("plan")}
    if board_file:
        expected = render_board(root, board, report, board_file)
        if local_file(root, board_file).read_text(encoding="utf-8-sig") != expected:
            report["errors"].append("派生看板已过期或被改写；请从任务源重新生成")
            report.update(ok=False, ready_tasks=[])
    return report


def initialize(destination, name, task_format="markdown"):
    destination = Path(destination).resolve()
    if not name.strip():
        raise ValueError("项目名称不能为空")
    if task_format not in {"markdown", "json"}:
        raise ValueError("task_format须为markdown或json")
    if destination.exists() and (not destination.is_dir() or any(destination.iterdir())):
        raise ValueError("初始化仅接受不存在或完全空的目录，拒绝覆盖既有项目")
    source = BASE / "templates" / "项目骨架"
    destination.mkdir(parents=True, exist_ok=True)
    for path in source.iterdir():
        if path.is_file() and not (task_format == "json" and path.name == "TASKS.md"):
            shutil.copyfile(path, destination / path.name)
    if task_format == "json":
        shutil.copyfile(BASE / "templates" / "兼容" / "tasks.json", destination / "tasks.json")
    project = read_json(destination / "project.json")
    project.update(name=name, created_at=now())
    (destination / "project.json").write_text(json.dumps(project, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for folder in ("protocol", "literature", "data", "src", "runs", "artifacts", "reviews", "manuscript", "snapshots", "submission"):
        (destination / folder).mkdir()
    return {"created": str(destination), "task_source": "TASKS.md" if task_format == "markdown" else "tasks.json", "next": "填写PLAN.md并拆分模块任务；G0—G9仅为阶段占位，没有任务被自动验收"}


def snapshot(root, snapshot_id, kind, files, tasks_file=None):
    root = Path(root).resolve()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}", snapshot_id):
        raise ValueError("快照ID仅允许1至80位英文字母、数字、点、下划线与连字符，首位须字母或数字")
    board = load_tasks(root, tasks_file)
    report = check(root, _board=board)
    if not report["ok"]:
        raise CheckFailure("任务检查未通过: " + "; ".join(report["errors"]))
    project = read_json(root / "project.json")
    required = project.get("snapshot_required_tasks", {}).get(kind)
    if not isinstance(required, list) or not required or not all(isinstance(x, str) for x in required):
        raise ValueError("快照必须配置非空的前置任务列表")
    tasks = {t["id"]: t for t in board["tasks"]}
    for tid in required:
        if tasks.get(tid, {}).get("status") != "ACCEPTED":
            raise CheckFailure(f"快照前置任务未验收: {tid}")
    if not files:
        raise ValueError("必须明确列出快照文件")
    records, seen = [], set()
    for relative in files:
        path = local_file(root, relative)
        rel = path.relative_to(root).as_posix()
        lower = path.name.lower()
        if lower == ".env" or lower.startswith(".env.") or lower.endswith((".pem", ".key")) or any(x in lower for x in ("credential", "secret", "api_key")):
            raise ValueError(f"疑似凭证文件，请排除并单独管理: {relative}")
        if rel.startswith("snapshots/") or path in seen:
            raise ValueError(f"快照文件重复或属于快照目录: {relative}")
        seen.add(path)
        records.append({"path": rel, "sha256": digest(path), "bytes": path.stat().st_size})
    folder = (root / "snapshots").resolve()
    if not folder.is_relative_to(root):
        raise ValueError("快照目录越出项目")
    folder.mkdir(exist_ok=True)
    manifest = folder / f"{snapshot_id}.json"
    if not sources_unchanged(root, board):
        raise CheckFailure("准备快照期间任务或计划发生变化，未创建快照")
    write_new(manifest, {"schema_version": 1, "id": snapshot_id, "kind": kind, "created_at": now(), "coverage": "explicit_files_only", "task_source": board["_source"], "preflight_required_tasks": required, "preflight_counts": report["counts"], "scientific_acceptance": "not_certified_by_this_tool", "files": records})
    return {"manifest": str(manifest), "files": len(records), "note": "已保存指定文件快照；没有自动冻结项目或修改任务状态"}


def verify(root, relative_manifest):
    root = Path(root).resolve()
    manifest = read_json(local_file(root, relative_manifest))
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1 or manifest.get("coverage") != "explicit_files_only":
        raise ValueError("不支持的快照格式")
    records = manifest.get("files")
    if not isinstance(records, list) or not records:
        raise ValueError("快照没有文件")
    errors, seen = [], set()
    for record in records:
        try:
            path = checked_record(root, record)
            if path in seen:
                raise ValueError("快照包含重复文件")
            seen.add(path)
            if path.stat().st_size != record.get("bytes"):
                raise ValueError(f"文件大小不一致: {record.get('path')}")
        except (ValueError, OSError) as exc:
            errors.append(str(exc))
    return {"ok": not errors, "checked_files": len(records), "errors": errors, "coverage": "仅清单所列文件；不认证清单本身真实性或未列文件"}


BOARD_MARKER = "<!-- research-infra:derived-board:v1 -->"


def render_board(root, board, report, output=None):
    def cell(value):
        return str(value or "—").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("|", "&#124;").replace("\n", "<br>")

    root = Path(root).resolve()
    base = (root / output).parent if output else root

    def file_link(relative):
        target = (root / relative).resolve()
        label = cell(relative).replace("[", "\\[").replace("]", "\\]")
        if not target.is_relative_to(root):
            return label
        href = quote(Path(os.path.relpath(target, base)).as_posix(), safe="/")
        return f"[{label}]({href})"

    source = board["_source"]
    lines = [BOARD_MARKER, "# 任务推进概览（派生，只读）", "",
             f"权威任务源：{file_link(source)}；SHA256：`{board['_sha256']}`。", "",
             "检查结果：" + ("机械检查通过；不代表科学正确。" if report["ok"] else "存在不一致；下表仅展示记录标签，不构成有效验收。"), "",
             "| 任务 | 状态标签 | 依赖 | 负责人 | 当前进展与下一步 | 证据位置 |",
             "|---|---|---|---|---|---|"]
    if board.get("_plan_source"):
        lines[5:5] = [f"计划：{file_link(board['_plan_source'])}；已同步声明：{cell(board['plan'].get('revision'))}；SHA256：`{board['_plan_sha256']}`。", ""]
    for task in board["tasks"]:
        evidence = [r.get("path", "?") for r in task.get("outputs", []) if isinstance(r, dict)]
        if isinstance(task.get("review"), dict):
            evidence.append(task["review"].get("path", "?"))
        state = md.LABELS.get(task.get("status"), "无法核实")
        values = [task.get("id", "?") + " " + task.get("title", ""), state,
                  "、".join(task.get("depends_on", [])) or "无", task.get("owner"),
                  task.get("progress") or task.get("blocked_reason") or task.get("defer_reason")]
        lines.append("| " + " | ".join(cell(value) for value in values) + " | " + ("; ".join(file_link(p) for p in evidence) or "—") + " |")
    lines.extend(["", "当前可开始的任务（仅依赖与结构检查）：" + ("、".join(report["ready_tasks"]) or "无／须先处理检查问题"), ""])
    if board.get("modules"):
        by_id = {task["id"]: task for task in board["tasks"]}
        lines += ["## 模块分组（派生）", "", "| 模块 | 成员任务及记录状态 | 共同产出 | 集成条件 |", "|---|---|---|---|"]
        for module in board["modules"]:
            members = "、".join(tid + "：" + md.LABELS.get(by_id.get(tid, {}).get("status"), "无法核实") for tid in module["tasks"])
            lines.append("| " + " | ".join(cell(x) for x in (module["id"], members, module["outcome"], module["integration"])) + " |")
        lines += ["", "此处只展示成员状态，不推断GitHub合并情况；必要成员未验收时模块不能视为完成。", ""]
    if report["errors"]:
        lines += ["## 检查问题", ""] + ["- " + cell(error) for error in report["errors"]] + [""]
    if report["warnings"]:
        lines += ["## 检查范围与提示", ""] + ["- " + cell(warning) for warning in report["warnings"]] + [""]
    lines += ["修改任务正文后重新生成；不要编辑本概览。读取错误不等于任务完成。", ""]
    return "\n".join(lines)


def export_board(root, tasks_file=None, output=None):
    root = Path(root).resolve()
    board = load_tasks(root, tasks_file)
    report = check(root, _board=board)
    rendered = render_board(root, board, report, output)
    if output:
        item = Path(output.replace("\\", "/"))
        win = PureWindowsPath(output)
        if item.is_absolute() or win.drive or win.root or ".." in item.parts or ":" in output:
            raise ValueError("看板输出必须为项目内相对Markdown路径")
        target = (root / item).resolve()
        if not target.is_relative_to(root) or target.suffix.lower() != ".md":
            raise ValueError("看板输出须为项目内.md文件")
        protected = {local_file(root, board["_source"])}
        if board.get("_plan_source"):
            protected.add(local_file(root, board["_plan_source"]))
        for task in board["tasks"]:
            for record in [*task.get("outputs", []), task.get("review")]:
                if isinstance(record, dict) and isinstance(record.get("path"), str):
                    protected.add((root / record["path"]).resolve())
        if target in protected:
            raise ValueError("看板不能覆盖任务源、产物或复核证据")
        previous = target.read_bytes() if target.exists() else None
        if previous is not None and not previous.decode("utf-8-sig").startswith(BOARD_MARKER + "\n"):
            raise ValueError("拒绝覆盖无生成标记的人工文件")
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=".research-board-", suffix=".tmp", dir=target.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
                stream.write(rendered)
                stream.flush()
                os.fsync(stream.fileno())
            if not sources_unchanged(root, board):
                raise ValueError("任务源或计划已变化，未发布过期看板")
            if (target.read_bytes() if target.exists() else None) != previous:
                raise ValueError("看板目标已被其他写入者修改，未覆盖")
            os.replace(temporary, target)
        finally:
            Path(temporary).unlink(missing_ok=True)
    return rendered, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="创建空白项目，不覆盖既有文件")
    init.add_argument("--dest", required=True)
    init.add_argument("--name", required=True)
    init.add_argument("--task-format", choices=("markdown", "json"), default="markdown")
    for command in ("check", "board", "hash", "basis", "snapshot", "verify"):
        child = sub.add_parser(command)
        child.add_argument("--root", required=True)
        if command in {"check", "board", "basis", "snapshot"}:
            child.add_argument("--tasks", help="显式指定唯一任务源；不执行迁移或双向同步")
        if command == "check":
            child.add_argument("--board", help="检查已保存的派生Markdown看板是否过期")
        if command == "board":
            child.add_argument("--output", help="可选的项目内输出路径；省略则仅打印Markdown")
        if command == "hash":
            child.add_argument("--files", nargs="+", required=True)
        if command == "basis":
            child.add_argument("--task", help="计算该任务的要求摘要；省略则计算全部版本化任务")
        if command == "snapshot":
            child.add_argument("--id", required=True)
            child.add_argument("--kind", choices=("protocol", "release"), required=True)
            child.add_argument("--files", nargs="+", required=True)
        if command == "verify":
            child.add_argument("--manifest", required=True)
    args = parser.parse_args()
    try:
        if args.command == "init":
            result = initialize(args.dest, args.name, args.task_format)
        elif args.command == "check":
            result = check(args.root, args.tasks, args.board)
        elif args.command == "board":
            rendered, result = export_board(args.root, args.tasks, args.output)
            if not args.output:
                print(rendered, end="")
                return 0 if result["ok"] else 1
            result["output"] = args.output
        elif args.command == "hash":
            result = {"files": [{"path": name, "sha256": digest(local_file(args.root, name))} for name in args.files]}
        elif args.command == "basis":
            result = task_bases(args.root, args.tasks, args.task)
        elif args.command == "snapshot":
            result = snapshot(args.root, args.id, args.kind, args.files, args.tasks)
        else:
            result = verify(args.root, args.manifest)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("ok", True) else 1
    except CheckFailure as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    except (ValueError, OSError, TypeError, KeyError, RecursionError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
