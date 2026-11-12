"""Read the documented Markdown task/review subset; never rewrite source documents."""
from __future__ import annotations

import hashlib
from pathlib import Path, PureWindowsPath
import re
from urllib.parse import unquote, urlsplit

LABELS = {"TODO": "待做", "RUNNING": "进行中", "REVIEW": "待核验",
          "ACCEPTED": "已验收", "BLOCKED": "受阻", "DEFERRED": "暂缓"}
STATES = {label: state for state, label in LABELS.items()}
TASK_ID = r"(?=[A-Za-z0-9_-]*[0-9])[A-Za-z][A-Za-z0-9_-]*"
TASK_HEADING = re.compile(r"^## (" + TASK_ID + r")\s+(.+?)\s*#*\s*$")
LINK = re.compile(r"(?<!!)\[[^\]\n]*\]\((<[^>\n]+>|[^)\n]+)\)")
FIELDS = {"状态", "依赖", "负责人", "复核方式", "对应计划", "阶段", "复核记录", "要求版本", "自检依据", "承接任务"}
REVIEW_FIELDS = {"任务", "结论", "复核者", "复核方式", "独立上下文", "验收依据"}
DOCUMENT_FIELDS = {"计划文件", "已同步计划修订", "当前修订"}
EMPTY = {"", "待填", "待填写", "待核实", "null", "待填/null", "【填写】"}
HASH = re.compile(r"[a-fA-F0-9]{64}\Z")


def meaningful(value):
    text = str(value or "").strip()
    return bool(text and text not in EMPTY and not text.startswith(("<待", "【待", "待填写", "待填：", "待填:")))


def document_fields(source):
    """Optional document controls live before the first level-two heading."""
    fields = {}
    for number, line in visible_lines(source.read_text(encoding="utf-8-sig")):
        if re.match(r"^##\s", line):
            break
        match = re.fullmatch(r"- ([^：:]+)[：:]\s*(.*)", line)
        if match and match[1] in DOCUMENT_FIELDS:
            key = match[1]
            if key in fields:
                raise ValueError(f"{source.name}:{number}: 重复文档字段 {key}")
            fields[key] = match[2].strip()
    return fields


def basis_record(value):
    parts = value.split("|")
    if len(parts) != 2 or not re.fullmatch(r"V[1-9][0-9]*", parts[0].strip()) or not HASH.fullmatch(parts[1].strip()):
        raise ValueError("依据须为 V正整数 | 64位要求摘要")
    return {"version": parts[0].strip(), "sha256": parts[1].strip().lower()}


def visible_lines(text):
    """Keep original line numbers; skip fences, quotes, indented code and comments."""
    fence, comment = None, False
    for number, original in enumerate(text.splitlines(), 1):
        line = original
        if line.lstrip().startswith(">"):
            continue
        if fence:
            if re.fullmatch(r" {0,3}" + re.escape(fence[0]) + "{" + str(fence[1]) + r",}\s*", line):
                fence = None
            continue
        if line.startswith(("    ", "\t")):
            continue
        if comment:
            if "-->" not in line:
                continue
            line = line.split("-->", 1)[1]
            comment = False
        while "<!--" in line:
            before, after = line.split("<!--", 1)
            if "-->" in after:
                line = before + after.split("-->", 1)[1]
            else:
                line, comment = before, True
                break
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if marker:
            fence = (marker[1][0], len(marker[1]))
            continue
        yield number, line


def anchors(path):
    text = path.read_text(encoding="utf-8-sig")
    result = set(re.findall(r'<a\s+(?:id|name)=["\']([^"\']+)["\']', text))
    used = {}
    for _, line in visible_lines(text):
        match = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
        if match:
            title = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", match[1])
            slug = re.sub(r"[^\w\- ]", "", title.lower()).replace(" ", "-")
            count = used.get(slug, 0)
            used[slug] = count + 1
            result.add(slug + (f"-{count}" if count else ""))
    return result


def resolve_link(root, source, target, evidence=False):
    target = target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    parsed = urlsplit(target)
    if parsed.scheme in {"http", "https", "mailto"}:
        if evidence:
            raise ValueError("版本绑定必须引用项目内实际文件，不能用远程链接")
        return None
    name = unquote(parsed.path).replace("\\", "/")
    win = PureWindowsPath(name)
    if parsed.scheme or parsed.netloc or parsed.query or win.drive or win.root or ":" in name:
        raise ValueError(f"不支持的本地引用: {target}")
    if evidence and (not name or parsed.fragment):
        raise ValueError("证据哈希绑定整个文件，不接受空路径或章节锚点")
    root = Path(root).resolve()
    path = (Path(source).parent / name).resolve() if name else Path(source).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"引用越出项目: {target}")
    if not path.is_file():
        raise ValueError(f"引用文件不存在: {target}")
    if parsed.fragment and path.suffix.lower() == ".md" and unquote(parsed.fragment) not in anchors(path):
        raise ValueError(f"引用锚点不存在: {target}")
    return path.relative_to(root).as_posix()


def file_record(root, source, link, sha):
    found = LINK.fullmatch(link.strip())
    if not found:
        raise ValueError("文件证据须使用 [名称](相对路径) 或 [名称](<含空格的相对路径>)")
    sha = sha.strip().strip("`")
    if not HASH.fullmatch(sha):
        raise ValueError("SHA256须为文件实际64位摘要")
    return {"path": resolve_link(root, source, found[1], evidence=True), "sha256": sha.lower()}


def section_text(sections, *names):
    return "\n".join(line for name in names for _, line in sections.get(name, [])).strip()


def content_items(sections, *names):
    items = []
    for name in names:
        for _, line in sections.get(name, []):
            value = re.sub(r"^\s*[-*+]\s+(?:\[[ xX]\]\s*)?", "", line).strip()
            if meaningful(value):
                items.append(value)
    return items


def records(root, source, lines, errors):
    result, table = [], False
    for number, line in lines:
        if not line.strip().startswith("|"):
            table = False
            continue
        columns = [x.strip() for x in line.strip().strip("|").split("|")]
        if columns == ["产物", "SHA256"]:
            table = True
            continue
        if all(re.fullmatch(r":?-+:?", col) for col in columns):
            continue
        try:
            if not table or len(columns) != 2:
                raise ValueError("证据表须为两列：产物 | SHA256")
            result.append(file_record(root, source, *columns))
        except ValueError as exc:
            errors.append(f"{source.relative_to(root).as_posix()}:{number}: {exc}")
    return result


def read_blocks(root, source, review=False):
    """Only control lists before a ### section are parsed as fields."""
    text = source.read_text(encoding="utf-8-sig")
    blocks, errors, current, section = [], [], None, None
    if review:
        current = {"line": 1, "fields": {}, "sections": {}, "field_lines": {}}
        blocks.append(current)
    source_name = source.relative_to(root).as_posix()
    for number, line in visible_lines(text):
        task = TASK_HEADING.fullmatch(line) if not review else None
        if task:
            if current:
                current["end"] = number
            current = {"id": task[1], "title": task[2], "line": number,
                       "fields": {}, "sections": {}, "field_lines": {}}
            blocks.append(current)
            section = None
            continue
        if not review and re.match(r"^#{1,2}\s", line):
            if current:
                current["end"] = number
            current, section = None, None
            continue
        heading = re.match(r"^###\s+(.+?)\s*#*\s*$", line)
        if current and heading:
            section = heading[1]
            if section in current["sections"]:
                errors.append(f"{source_name}:{number}: 重复章节 {section}")
            current["sections"].setdefault(section, [])
            current.setdefault("section_starts", {}).setdefault(section, number)
            continue
        field = re.fullmatch(r"- ([^：:]+)[：:]\s*(.*)", line)
        if field and section is None:
            key, value = field[1].strip(), field[2].strip()
            allowed = REVIEW_FIELDS if review else FIELDS
            if current is None:
                if key in allowed:
                    errors.append(f"{source_name}:{number}: 控制字段不在有效任务标题下（ID须含数字）")
                continue
            if key not in allowed:
                errors.append(f"{source_name}:{number}: 未知控制字段 {key}；说明文字请放入三级章节")
            elif key in current["fields"]:
                errors.append(f"{source_name}:{number}: 重复字段 {key}")
            else:
                current["fields"][key] = value
                current["field_lines"][key] = number
        elif current and section:
            current["sections"][section].append((number, line))
        if current:
            for match in LINK.finditer(line):
                try:
                    resolve_link(root, source, match[1])
                except ValueError as exc:
                    errors.append(f"{source_name}:{number}: {exc}")
    raw_lines = text.splitlines()
    for block in blocks:
        starts = sorted(block.get("section_starts", {}).items(), key=lambda item: item[1])
        block["raw_sections"] = {}
        for index, (name, start) in enumerate(starts):
            stop = starts[index + 1][1] if index + 1 < len(starts) else block.get("end", len(raw_lines) + 1)
            block["raw_sections"][name] = list(enumerate(raw_lines[start:stop - 1], start + 1))
    return blocks, errors, text


def read_tasks(root, source):
    root, source = Path(root).resolve(), Path(source).resolve()
    blocks, errors, text = read_blocks(root, source)
    tasks = []
    for block in blocks:
        fields, sections = block["fields"], block["sections"]
        contract_sections = block["raw_sections"] if "要求版本" in fields else sections
        where = f"{source.relative_to(root).as_posix()}:{block['line']} ({block['id']})"
        for key in ("状态", "依赖", "复核方式"):
            if key not in fields:
                errors.append(f"{where}: 缺少字段 {key}")
        state = STATES.get(fields.get("状态"))
        if not state:
            errors.append(f"{where}: 状态须为 {'、'.join(STATES)}")
        mode = fields.get("复核方式")
        if mode not in {"独立复核", "自检"}:
            errors.append(f"{where}: 复核方式须为独立复核或自检")
        deps = fields.get("依赖", "")
        dependencies = [] if deps == "无" else [x.strip() for x in re.split(r"[,，、]", deps)]
        if any(not re.fullmatch(TASK_ID, x) for x in dependencies):
            errors.append(f"{where}: 依赖须为任务ID列表或“无”")
        output = records(root, source, sections.get("产物与证据", []), errors)
        review_record = None
        if meaningful(fields.get("复核记录")):
            try:
                link, sha = fields["复核记录"].rsplit("|", 1)
                review_record = file_record(root, source, link, sha)
            except ValueError as exc:
                errors.append(f"{where}: 复核记录需使用 链接 | SHA256；{exc}")
        owner = fields.get("负责人")
        additions = {}
        if "要求版本" in fields:
            additions["requirements_version"] = fields["要求版本"]
        if "自检依据" in fields:
            try:
                additions["self_check_basis"] = basis_record(fields["自检依据"])
            except ValueError as exc:
                errors.append(f"{where}: {exc}")
        if "承接任务" in fields:
            additions["successors"] = [x.strip() for x in re.split(r"[,，、]", fields["承接任务"])]
        tasks.append({"id": block["id"], "title": block["title"], "status": state,
                      "stage": fields.get("阶段"), "depends_on": dependencies,
                      "owner": owner if meaningful(owner) else None, "review_required": mode == "独立复核",
                      "acceptance_criteria": content_items(contract_sections, "实施与验收条件", "验收条件"),
                      "outputs": output, "review": review_record,
                      "self_check": section_text(sections, "自检记录") if content_items(sections, "自检记录") else None,
                      "blocked_reason": section_text(sections, "阻断原因") if content_items(sections, "阻断原因") else None,
                      "defer_reason": section_text(sections, "暂缓原因") if content_items(sections, "暂缓原因") else None,
                      "progress": section_text(sections, "当前进展与下一步"), "plan": fields.get("对应计划", ""),
                      "history": section_text(sections, "变更记录"), "_where": where,
                      "goal": section_text(contract_sections, "目标与边界"),
                      "inputs": section_text(contract_sections, "输入与版本"), **additions})
    if not tasks:
        raise ValueError(f"{source.relative_to(root)}:1: 未找到任务；使用 ## T-001 任务名称")
    metadata = document_fields(source)
    plan = None
    if "计划文件" in metadata:
        link = LINK.fullmatch(metadata["计划文件"])
        if not link:
            raise ValueError(f"{source.relative_to(root)}:1: 计划文件须为本地Markdown链接")
        plan = {"path": resolve_link(root, source, link[1], evidence=True),
                "revision": metadata.get("已同步计划修订")}
    elif "当前修订" in metadata:
        plan = {"path": source.relative_to(root).as_posix(), "revision": metadata["当前修订"]}
    elif "已同步计划修订" in metadata:
        errors.append(f"{source.relative_to(root)}:1: 已同步计划修订缺少计划文件")
    if "当前修订" in metadata and ("计划文件" in metadata or "已同步计划修订" in metadata):
        errors.append(f"{source.relative_to(root)}:1: 合并文档只填当前修订；分开文档只填计划文件和已同步计划修订")
    return {"schema_version": 1, "tasks": tasks, "_errors": errors, "plan": plan,
            "_text_hash": hashlib.sha256(text.encode("utf-8")).hexdigest()}


def read_review(root, source):
    root, source = Path(root).resolve(), Path(source).resolve()
    blocks, errors, _ = read_blocks(root, source, review=True)
    block = blocks[0]
    fields, sections = block["fields"], block["sections"]
    for key in ("任务", "结论", "复核者", "复核方式"):
        if not meaningful(fields.get(key)):
            errors.append(f"{source.relative_to(root)}:1: 缺少复核字段 {key}")
    if fields.get("结论") not in {"通过", "退回"}:
        errors.append(f"{source.relative_to(root)}:1: 复核结论须为通过或退回")
    if fields.get("复核方式") not in {"独立复核", "自检"}:
        errors.append(f"{source.relative_to(root)}:1: 复核方式不合法")
    output = records(root, source, sections.get("产物与证据", []), errors)
    if len({x["path"] for x in output}) != len(output):
        errors.append(f"{source.relative_to(root)}:1: 复核产物重复登记")
    if not content_items(sections, "局限"):
        errors.append(f"{source.relative_to(root)}:1: 复核须说明局限；没有则写“无”")
    basis = None
    if "验收依据" in fields:
        try:
            basis = basis_record(fields["验收依据"])
        except ValueError as exc:
            errors.append(f"{source.relative_to(root)}:1: {exc}")
    if errors:
        raise ValueError("; ".join(errors))
    return {"task_id": fields.get("任务"), "verdict": "ACCEPT" if fields.get("结论") == "通过" else "REJECT",
            "reviewer": fields.get("复核者"),
            "independent_context": fields.get("独立上下文") == "是" and fields.get("复核方式") == "独立复核",
            "context_record": section_text(sections, "上下文依据") if content_items(sections, "上下文依据") else None,
            "checks": content_items(sections, "检查内容"), "limitations": content_items(sections, "局限"),
            "artifact_sha256": {record["path"]: record["sha256"] for record in output},
            "requirements_basis": basis}
