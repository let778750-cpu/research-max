"""Local research bookkeeping. Standard library only; no network or model calls."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PureWindowsPath
import re
import shutil
import sys

BASE = Path(__file__).resolve().parents[1]
STATUSES = {"TODO", "RUNNING", "REVIEW", "ACCEPTED", "BLOCKED", "DEFERRED"}
DIGEST = re.compile(r"[0-9a-fA-F]{64}\Z")


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


def check(root):
    root = Path(root).resolve()
    project = read_json(local_file(root, "project.json"))
    board = read_json(local_file(root, "tasks.json"))
    if not isinstance(project, dict) or project.get("schema_version") != 1:
        raise ValueError("project.json不是受支持的schema_version=1对象")
    if not isinstance(board, dict) or board.get("schema_version") != 1:
        raise ValueError("tasks.json不是受支持的schema_version=1对象")
    tasks = board.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise ValueError("tasks必须为非空列表")
    errors, warnings, by_id = [], [], {}
    for t in tasks:
        if not isinstance(t, dict) or not isinstance(t.get("id"), str) or not t["id"].strip():
            errors.append("任务缺少有效id")
            continue
        tid = t["id"]
        if tid in by_id:
            errors.append(f"重复任务ID: {tid}")
        by_id[tid] = t
    edges = {}
    for tid, task in by_id.items():
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
        state = task.get("status")
        if not isinstance(state, str) or state not in STATUSES:
            errors.append(f"{tid}: 非法任务状态")
            state = None
        if state in {"RUNNING", "REVIEW", "ACCEPTED"}:
            if not isinstance(task.get("owner"), str) or not task["owner"].strip():
                errors.append(f"{tid}: 工作任务缺少负责人")
            criteria = task.get("acceptance_criteria")
            if not isinstance(criteria, list) or not criteria or not all(isinstance(x, str) and x.strip() for x in criteria):
                errors.append(f"{tid}: 尚未填写验收条件")
            for dep in deps:
                if by_id.get(dep, {}).get("status") != "ACCEPTED":
                    errors.append(f"{tid}: 上游 {dep} 尚未验收")
        if state == "BLOCKED" and not task.get("blocked_reason"):
            errors.append(f"{tid}: BLOCKED缺少阻断原因")
        if state == "DEFERRED" and not task.get("defer_reason"):
            errors.append(f"{tid}: DEFERRED缺少移出范围的原因")
        if not isinstance(task.get("review_required"), bool):
            errors.append(f"{tid}: review_required须显式为布尔值")
        if state != "ACCEPTED":
            continue
        outputs = task.get("outputs")
        if not isinstance(outputs, list) or not outputs:
            errors.append(f"{tid}: 验收任务没有产物")
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
        review_record = task.get("review")
        if task.get("review_required") is True and not review_record:
            errors.append(f"{tid}: 缺少独立复核文件")
        if review_record:
            try:
                review = read_json(checked_record(root, review_record))
                if not isinstance(review, dict):
                    raise ValueError("复核记录须为JSON对象")
                if review.get("task_id") != tid or review.get("verdict") != "ACCEPT":
                    raise ValueError("复核任务或结论不匹配")
                if review.get("artifact_sha256") != bound:
                    raise ValueError("复核未绑定本次全部产物")
                if not review.get("checks") or not isinstance(review["checks"], list):
                    raise ValueError("复核缺少实际检查内容")
                if task.get("review_required") is True:
                    reviewer = review.get("reviewer")
                    if not isinstance(reviewer, str) or not reviewer.strip() or reviewer == task.get("owner"):
                        raise ValueError("复核者必须声明为实际非作者")
                    if review.get("independent_context") is not True or not review.get("context_record"):
                        raise ValueError("缺少独立上下文声明或记录")
            except (ValueError, OSError, TypeError) as exc:
                errors.append(f"{tid}: {exc}")
        elif task.get("review_required") is False and not task.get("self_check"):
            errors.append(f"{tid}: 低风险验收缺少自检记录")
    active, done = set(), set()

    def visit(tid):
        if tid in active:
            raise ValueError(f"任务依赖成环: {tid}")
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
    warnings.append("本检查不认证科学正确、复核独立性、完整冻结范围或投稿合规")
    return {"ok": not errors, "errors": errors, "warnings": warnings, "counts": dict(Counter(str(t.get("status")) for t in by_id.values())), "ready_tasks": ready if not errors else []}


def initialize(destination, name):
    destination = Path(destination).resolve()
    if not name.strip():
        raise ValueError("项目名称不能为空")
    if destination.exists() and (not destination.is_dir() or any(destination.iterdir())):
        raise ValueError("初始化仅接受不存在或完全空的目录，拒绝覆盖既有项目")
    source = BASE / "templates" / "项目骨架"
    destination.mkdir(parents=True, exist_ok=True)
    for path in source.iterdir():
        if path.is_file():
            shutil.copyfile(path, destination / path.name)
    project = read_json(destination / "project.json")
    project.update(name=name, created_at=now())
    (destination / "project.json").write_text(json.dumps(project, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for folder in ("protocol", "literature", "data", "src", "runs", "artifacts", "reviews", "manuscript", "snapshots", "submission"):
        (destination / folder).mkdir()
    return {"created": str(destination), "next": "填写G0问题、输入和验收条件；没有任务被自动验收"}


def snapshot(root, snapshot_id, kind, files):
    root = Path(root).resolve()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}", snapshot_id):
        raise ValueError("快照ID仅允许1至80位英文字母、数字、点、下划线与连字符，首位须字母或数字")
    report = check(root)
    if not report["ok"]:
        raise ValueError("任务检查未通过: " + "; ".join(report["errors"]))
    project = read_json(root / "project.json")
    required = project.get("snapshot_required_tasks", {}).get(kind)
    if not isinstance(required, list) or not required or not all(isinstance(x, str) for x in required):
        raise ValueError("快照必须配置非空的前置任务列表")
    tasks = {t["id"]: t for t in read_json(root / "tasks.json")["tasks"]}
    for tid in required:
        if tasks.get(tid, {}).get("status") != "ACCEPTED":
            raise ValueError(f"快照前置任务未验收: {tid}")
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
    write_new(manifest, {"schema_version": 1, "id": snapshot_id, "kind": kind, "created_at": now(), "coverage": "explicit_files_only", "preflight_required_tasks": required, "preflight_counts": report["counts"], "scientific_acceptance": "not_certified_by_this_tool", "files": records})
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="创建空白项目，不覆盖既有文件")
    init.add_argument("--dest", required=True)
    init.add_argument("--name", required=True)
    for command in ("check", "snapshot", "verify"):
        child = sub.add_parser(command)
        child.add_argument("--root", required=True)
        if command == "snapshot":
            child.add_argument("--id", required=True)
            child.add_argument("--kind", choices=("protocol", "release"), required=True)
            child.add_argument("--files", nargs="+", required=True)
        if command == "verify":
            child.add_argument("--manifest", required=True)
    args = parser.parse_args()
    try:
        if args.command == "init":
            result = initialize(args.dest, args.name)
        elif args.command == "check":
            result = check(args.root)
        elif args.command == "snapshot":
            result = snapshot(args.root, args.id, args.kind, args.files)
        else:
            result = verify(args.root, args.manifest)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("ok", True) else 1
    except (ValueError, OSError, TypeError, KeyError, RecursionError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
