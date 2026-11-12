"""Optional Markdown delivery groups. Local parsing only; no Git/GitHub calls."""
from __future__ import annotations

import re

import markdown_tasks as md

MODULE_ID = re.compile(r"M-[A-Za-z0-9][A-Za-z0-9_-]*\Z")
REPOSITORY = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9_.-]+\Z")
AGREEMENT_KEYS = {"仓库", "指定任务", "授权来源", "当前接手者", "发布", "合并方式", "基线分支"}
HEADERS = ["模块", "任务", "共同产出", "集成条件"]


def ids(value):
    return [part.strip() for part in re.split(r"[,，、]", value)]


def read(source):
    """Only two named level-two sections are recognized; examples are ignored."""
    agreement, modules, errors, seen = {}, [], [], set()
    section, header_seen = None, False
    for number, line in md.visible_lines(source.read_text(encoding="utf-8-sig")):
        where = f"{source.name}:{number}"
        if re.match(r"^#{1,2}\s", line):
            section = {"## GitHub记录约定": "agreement", "## 模块分组": "modules"}.get(line.strip())
            if section:
                if section in seen:
                    errors.append(f"{where}: 重复的GitHub记录约定或模块分组")
                seen.add(section)
            continue
        if section == "agreement":
            match = re.fullmatch(r"- ([^：:]+)[：:]\s*(.*)", line)
            if match:
                key, value = match[1].strip(), match[2].strip()
                if key not in AGREEMENT_KEYS or key in agreement:
                    errors.append(f"{where}: GitHub约定字段未知或重复 {key}")
                agreement[key] = value
        elif section == "modules" and line.strip().startswith("|"):
            cells = [x.strip() for x in line.strip().strip("|").split("|")]
            if cells == HEADERS:
                if header_seen:
                    errors.append(f"{where}: 重复模块表头")
                header_seen = True
                continue
            if all(re.fullmatch(r":?-{3,}:?", x) for x in cells):
                continue
            if not header_seen or len(cells) != 4:
                errors.append(f"{where}: 模块表须为 模块/任务/共同产出/集成条件 四列")
                continue
            modules.append(dict(id=cells[0], tasks=ids(cells[1]), outcome=cells[2], integration=cells[3], _where=where))
    if "agreement" in seen:
        if set(agreement) != AGREEMENT_KEYS:
            errors.append(f"{source.name}:1: GitHub记录约定须填写全部七项字段")
        if not REPOSITORY.fullmatch(agreement.get("仓库", "")):
            errors.append(f"{source.name}:1: 仓库须为明确的owner/repo")
        selected = ids(agreement.get("指定任务", ""))
        if not selected or len(set(selected)) != len(selected) or not all(re.fullmatch(md.TASK_ID, x) for x in selected):
            errors.append(f"{source.name}:1: GitHub指定任务须为不重复的明确ID，不能使用通配符")
        agreement["指定任务"] = selected
        if agreement.get("发布") not in {"允许", "暂停", "结束"} or agreement.get("合并方式") != "自动":
            errors.append(f"{source.name}:1: 发布须为允许/暂停/结束；本模式合并方式为自动")
        if not all(md.meaningful(agreement.get(k, "")) for k in ("授权来源", "当前接手者", "基线分支")):
            errors.append(f"{source.name}:1: GitHub约定缺少实际授权、接手者或基线分支")
    return agreement if "agreement" in seen else None, modules, errors


def graph(tasks, modules):
    membership = {tid: "module:" + m["id"] for m in modules for tid in m["tasks"]}
    node = lambda tid: membership.get(tid, "task:" + tid)
    result = {node(t["id"]): set() for t in tasks}
    for task in tasks:
        for dependency in task.get("depends_on", []):
            if node(task["id"]) != node(dependency):
                result[node(task["id"])].add(node(dependency))
    return result


def validate(board):
    tasks, modules = board.get("tasks", []), board.get("modules", [])
    known = {t["id"] for t in tasks if isinstance(t, dict) and isinstance(t.get("id"), str)}
    errors, module_ids, assigned = [], set(), set()
    agreement = board.get("_github")
    if agreement and any(t not in known for t in agreement.get("指定任务", [])):
        errors.append(f"{board['_source']}:1: GitHub指定任务含不存在的任务")
    for m in modules:
        label = m["_where"]
        if not MODULE_ID.fullmatch(m["id"]) or m["id"] in module_ids:
            errors.append(f"{label}: 模块ID无效或重复 {m['id']}")
        module_ids.add(m["id"])
        if not m["tasks"] or len(m["tasks"]) != len(set(m["tasks"])):
            errors.append(f"{label}: 模块成员为空或重复")
        for tid in m["tasks"]:
            if tid not in known:
                errors.append(f"{label}: 模块成员不存在 {tid}")
            if tid in assigned:
                errors.append(f"{label}: 同一任务重复归属模块 {tid}")
            assigned.add(tid)
        if not all(md.meaningful(m[key]) for key in ("outcome", "integration")):
            errors.append(f"{label}: 须填写共同产出和集成条件（无额外检查时说明现有验收如何覆盖）")
    if errors or not modules:
        return errors
    edges, visiting, done = graph(tasks, modules), set(), set()

    def visit(node):
        if node in visiting:
            raise ValueError(f"{board['_source']}:1: 模块分组后的依赖成环：{node}")
        if node in done:
            return
        visiting.add(node)
        for dep in edges.get(node, set()):
            visit(dep)
        visiting.remove(node)
        done.add(node)
    try:
        for node in edges:
            visit(node)
    except ValueError as exc:
        errors.append(str(exc))
    return errors
