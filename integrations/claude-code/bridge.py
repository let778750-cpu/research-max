"""Opt-in, one-module Claude Code bridge. No scheduler and no task-state writer.

Only `run` invokes a model. All other commands operate on local files. The host
must establish actual user authorization; a Markdown declaration is not proof
of consent. Requires Python 3.10+ and the complete research-max distribution.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path, PureWindowsPath
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import uuid

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "research-execution" / "scripts"))
import research_infra as infra
import markdown_tasks as md
from process_scope import ProcessScope, alive

RUN_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}\Z")
AGREEMENT_KEYS = {"执行方式", "指定任务", "授权来源", "当前接手者", "派发"}
META_DIR = ".research-harness"
TERMINAL = {"returned", "failed", "cancelled", "timed_out", "interrupted"}


def adapter_profile(parallel):
    return "scoped-agents-v1" if parallel else "bare-v1"


def sha_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def atomic_json(path, data):
    path = Path(path)
    fd, name = tempfile.mkstemp(prefix=".write-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        # Windows readers may briefly hold a handle without FILE_SHARE_DELETE.
        # Keep the old complete record visible; retry only this bounded rename.
        deadline = time.monotonic() + 1.0
        while True:
            try:
                os.replace(name, path)
                break
            except PermissionError:
                if os.name != "nt" or time.monotonic() >= deadline:
                    raise
                time.sleep(0.01)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def inside(root, name):
    if not isinstance(name, str) or not name.strip():
        raise ValueError("路径不能为空")
    normal = name.replace("\\", "/")
    p, win = Path(normal), PureWindowsPath(normal)
    if p.is_absolute() or win.drive or win.root or ".." in p.parts or ":" in normal or p == Path("."):
        raise ValueError("须为范围内相对路径: " + name)
    if any(part.rstrip(" .") != part or re.fullmatch(r"(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?", part) for part in p.parts):
        raise ValueError("不接受Windows设备名或末尾点/空格路径: " + name)
    root = Path(root).resolve()
    target = root / p
    for item in [target, *target.parents]:
        if item == root:
            break
        if item.is_symlink() or (hasattr(item, "is_junction") and item.is_junction()):
            raise ValueError("不接受链接或目录联接: " + name)
    if not target.resolve().is_relative_to(root):
        raise ValueError("路径越界: " + name)
    return target


def inventory(workspace):
    """Hash actual workspace files, excluding only Git's administrative area."""
    result = {}
    for base, dirs, files in os.walk(workspace, followlinks=False):
        for name in list(dirs):
            if name == ".git":
                dirs.remove(name)
                continue
            inside(workspace, (Path(base) / name).relative_to(workspace).as_posix())
        for name in files:
            if name == ".git":
                continue
            relative = (Path(base) / name).relative_to(workspace).as_posix()
            result[relative] = infra.digest(inside(workspace, relative))
    return result


def agreement(source):
    fields, enabled, count = {}, False, 0
    for line_no, line in md.visible_lines(source.read_text(encoding="utf-8-sig")):
        if re.match(r"^##\s", line):
            enabled = line.strip() == "## 执行约定"
            count += int(enabled)
            continue
        if enabled and line.startswith("- "):
            match = re.fullmatch(r"- ([^：:]+)[：:]\s*(.*)", line)
            if not match or match[1] not in AGREEMENT_KEYS or match[1] in fields:
                raise ValueError(f"{source.name}:{line_no}: 执行约定字段未知或重复")
            fields[match[1]] = match[2].strip()
    if count != 1 or set(fields) != AGREEMENT_KEYS or not all(md.meaningful(v) for v in fields.values()):
        raise ValueError("须有一份完整的可选执行约定；读取文件或历史记录不构成启动授权")
    if fields["执行方式"] != "跨 Harness" or fields["派发"] not in {"允许", "暂停", "结束"}:
        raise ValueError("执行方式须为跨 Harness，派发须为允许、暂停或结束")
    ids = [s.strip() for s in re.split(r"[,，、]", fields["指定任务"])]
    if len(ids) != len(set(ids)) or not all(re.fullmatch(md.TASK_ID, x) for x in ids):
        raise ValueError("指定任务须为不重复的明确ID列表，不能写全部或通配符")
    fields["指定任务"] = ids
    return fields


def load_context(root, tasks, task_id, owner, launching=True):
    board = infra.load_tasks(root, tasks)
    if not board["_source"].lower().endswith(".md"):
        raise ValueError("桥接入口使用Markdown执行约定；旧JSON离线功能不受影响")
    report = infra.check(root, board["_source"], _board=board)
    if not report["ok"]:
        raise ValueError("任务检查未通过: " + "; ".join(report["errors"]))
    control = agreement(root / board["_source"])
    by_id = {t["id"]: t for t in board["tasks"]}
    if any(t not in by_id for t in control["指定任务"]):
        raise ValueError("执行约定含不存在的任务")
    if task_id not in control["指定任务"] or control["当前接手者"] != owner:
        raise ValueError("任务不在指定范围或当前接手者不匹配")
    task = by_id[task_id]
    if launching and (control["派发"] != "允许" or task["status"] not in {"TODO", "RUNNING"}):
        raise ValueError("当前派发已暂停/结束，或任务不是待做/进行中")
    if any(by_id[d]["status"] != "ACCEPTED" for d in task["depends_on"]):
        raise ValueError("上游尚未验收；不得自动扩展授权范围")
    if not infra.valid_text(task.get("owner")):
        raise ValueError("派发前须填写任务负责人")
    basis = infra.requirements_basis(task)
    if not infra.sources_unchanged(root, board):
        raise ValueError("读取期间任务/计划发生变化")
    return board, control, task, basis


def run_folder(root, run_id):
    if not isinstance(run_id, str) or not RUN_ID.fullmatch(run_id):
        raise ValueError("尝试ID须为字母、数字、短横线或下划线，至多80字符")
    return inside(root, f"{META_DIR}/runs/{run_id}")


def allowed(path, names):
    if os.name == "nt":
        path, names = path.casefold(), [n.casefold() for n in names]
    return any(path == n or path.startswith(n.rstrip("/") + "/") for n in names)


def workspace_lock(workspace):
    workspace = Path(workspace).resolve()
    key = sha_text(os.path.normcase(str(workspace)))[:32]
    return workspace.parent / (".research-harness-" + key + ".lock")


def prepare(root, *, task_id, run_id, owner, workspace, inputs, writes, instructions,
            model, timeout, tasks=None, parallel=False, resume_run=None):
    root, workspace = Path(root).resolve(), Path(workspace).resolve()
    if workspace == root or workspace.is_relative_to(root) or root.is_relative_to(workspace):
        raise ValueError("执行工作副本须位于权威项目之外，且不能包含权威项目")
    if not workspace.is_dir() or not model.strip() or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("须有实际工作副本、明确模型和有限正数超时秒数")
    board, control, task, basis = load_context(root, tasks, task_id, owner)
    instructions_path = infra.local_file(root, instructions)
    notes = instructions_path.read_text(encoding="utf-8-sig")
    if not md.meaningful(notes):
        raise ValueError("执行补充说明不能为空")
    writes = list(dict.fromkeys(s.replace("\\", "/").rstrip("/") for s in writes))
    for name in writes:
        inside(workspace, name)
        if Path(name).parts[0].casefold() in {".git", ".claude", META_DIR}:
            raise ValueError("写入范围不能包括执行配置或运行记录")
    bindings = {}
    for name in inputs:
        name = infra.local_file(root, name).relative_to(root).as_posix()
        copied = inside(workspace, name)
        bindings[name] = infra.digest(root / name)
        if not copied.is_file() or infra.digest(copied) != bindings[name]:
            raise ValueError("工作副本与输入版本不一致: " + name)
    previous_session = None
    if resume_run:
        old_path, old = read_dispatch(root, resume_run)
        state = infra.read_json(old_path / "runtime.json")
        if old["task_id"] != task_id or old["workspace"] != str(workspace) or state["phase"] not in TERMINAL:
            raise ValueError("只能显式恢复同任务、同工作副本且已结束的尝试")
        if bool(old["parallel"]) != bool(parallel):
            raise ValueError("串行与并行使用不同CLI配置范围；切换时开启新会话")
        if old.get("adapter_profile") != adapter_profile(parallel):
            raise ValueError("旧会话适配配置不一致；应开启新会话")
        previous_session = state.get("session_id")
        if not previous_session:
            raise ValueError("旧尝试没有可恢复的Claude会话ID")
        if previous_session != old["session_id"]:
            raise ValueError("旧运行返回会话ID与派发身份不一致，不能恢复")
    folder = run_folder(root, run_id)
    folder.mkdir(parents=True, exist_ok=False)
    payload = {"schema_version": 1, "task_id": task_id, "run_id": run_id,
               "root": str(root), "workspace": str(workspace), "owner": owner,
               "tasks": board["_source"], "basis": basis, "agreement": control,
               "inputs": bindings, "writes": writes, "model": model,
               "timeout_seconds": timeout, "parallel": parallel,
               "adapter_profile": adapter_profile(parallel),
               "instructions": instructions, "instructions_sha256": infra.digest(instructions_path),
               "baseline": inventory(workspace), "resume_run": resume_run,
               "session_id": previous_session or str(uuid.uuid4()), "prepared_at": infra.now()}
    token = f"{basis['version']} | {basis['sha256']}"
    prompt = f"""# 当前模块交接包

- 任务：{task_id}
- 尝试：{run_id}
- 要求依据：{token}
- 对应计划：{task.get('plan', '')}
- 工作副本：{workspace}
- 允许写入：{', '.join(writes) or '无（仅返回检查结果）'}
- 本轮最长运行秒数：{timeout}

## 研究目的与边界
{task['goal']}

## 输入与版本
{task.get('inputs', '')}
{chr(10).join('- ' + name + '：' + sha for name, sha in bindings.items())}
所有相对路径以工作副本为基准。权威任务与计划由主持者维护。

## 验收条件
{chr(10).join('- ' + x for x in task['acceptance_criteria'])}

## 必要上下文与实施说明
{notes}

## 执行与返回规则
只完成本模块；不启动后继任务，不改验收条件、权威计划或任务状态。
不得访问凭据文件、输出密钥、改全局配置，或通过远端服务/WMI/脱离进程树的作业继续运行。
{'允许调用module-worker前台子代理；每份分派交代目标、独立写入范围和验收条件，必须收齐结果，不允许递归委托。' if parallel else '本轮使用单执行者，不创建子代理。'}
所有子代理和命令必须在本轮结束前终止；不得保留后台工作。合理负结果如实报告。
最终回复使用下面的Markdown格式，不用代码围栏；字段填真实结果，不预填通过。
不要在工作副本写回执文件，主持者会保存最终回复。检查章节须给实际检查及结果。

# 模块执行回执
- 任务：{task_id}
- 尝试：{run_id}
- 要求依据：{token}
- 结果：完成／部分完成／受阻（三选一）
- 子作业：已结束／未结束（二选一）
## 实际产物
填写实际相对路径或只读发现。
## 检查结果
填写已执行命令、观察结果与未执行检查，区分自检与科学结论。
## 缺口与偏差
填写剩余问题、偏差与局限，没有则写无。
"""
    (folder / "BRIEF.md").write_text(prompt, encoding="utf-8", newline="\n")
    payload["brief_sha256"] = infra.digest(folder / "BRIEF.md")
    infra.write_new(folder / "dispatch.json", payload)
    infra.write_new(folder / "binding.json", {"dispatch_sha256": infra.digest(folder / "dispatch.json")})
    atomic_json(folder / "runtime.json", {"phase": "prepared", "run_id": run_id,
                                         "task_id": task_id, "ready_for_review": False})
    return {"run_id": run_id, "brief": str(folder / "BRIEF.md"), "model_called": False}


def read_dispatch(root, run_id):
    folder = run_folder(root, run_id)
    binding = infra.read_json(folder / "binding.json")
    if infra.digest(folder / "dispatch.json") != binding["dispatch_sha256"]:
        raise ValueError("派发记录被改写")
    data = infra.read_json(folder / "dispatch.json")
    if data["root"] != str(root) or data["run_id"] != run_id:
        raise ValueError("派发记录项目或尝试ID不匹配")
    if infra.digest(folder / "BRIEF.md") != data["brief_sha256"]:
        raise ValueError("交接包被改写；应创建新尝试")
    return folder, data


def freshness(root, data, launching=False):
    _, control, _, basis = load_context(root, data["tasks"], data["task_id"], data["owner"], launching)
    if basis != data["basis"]:
        raise ValueError("任务要求已改变，旧交付不能自动验收")
    # Pausing dispatch does not erase the evidence returned by an in-flight run.
    if {k:v for k,v in control.items() if k != "派发"} != {k:v for k,v in data["agreement"].items() if k != "派发"}:
        raise ValueError("执行范围、接手者或授权说明已改变")
    for name, sha in data["inputs"].items():
        if infra.digest(infra.local_file(root, name)) != sha:
            raise ValueError("关键输入已改变: " + name)
    if infra.digest(infra.local_file(root, data["instructions"])) != data["instructions_sha256"]:
        raise ValueError("执行补充说明已改变")


def receipt(text, data):
    fields, sections, section = {}, {}, None
    for _, line in md.visible_lines(text):
        if line.startswith("## "):
            section = line[3:].strip()
            if section in sections:
                raise ValueError("回执章节重复")
            sections[section] = []
        elif section:
            sections[section].append(line)
        elif line.startswith("- "):
            m = re.fullmatch(r"- ([^：:]+)[：:]\s*(.*)", line)
            if not m or m[1] in fields:
                raise ValueError("回执字段错误或重复")
            fields[m[1]] = m[2].strip()
    expected = {"任务": data["task_id"], "尝试": data["run_id"],
                "要求依据": f"{data['basis']['version']} | {data['basis']['sha256']}"}
    if any(fields.get(k) != v for k,v in expected.items()):
        raise ValueError("回执任务、尝试或要求依据不匹配")
    if fields.get("结果") not in {"完成", "部分完成", "受阻"} or fields.get("子作业") not in {"已结束", "未结束"}:
        raise ValueError("回执缺少明确结果或子作业声明")
    for key in ("实际产物", "检查结果", "缺口与偏差"):
        if not md.meaningful("\n".join(sections.get(key, [])).strip()):
            raise ValueError("回执缺少实际内容: " + key)
    return fields


def local_profile():
    """Read a narrow env allowlist in memory; never return it in public output."""
    env = os.environ.copy()
    profile = Path.home() / ".claude" / "settings.json"
    keys = {"ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_API_KEY", "ANTHROPIC_BASE_URL", "API_TIMEOUT_MS",
            "ANTHROPIC_DEFAULT_HAIKU_MODEL", "ANTHROPIC_DEFAULT_SONNET_MODEL", "ANTHROPIC_DEFAULT_OPUS_MODEL"}
    values = infra.read_json(profile).get("env", {}) if profile.is_file() else {}
    for key in keys:
        if key not in env and key in values:
            env[key] = str(values[key])
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS"] = "0"
    env.pop("CLAUDECODE", None)
    secrets = [v for k,v in env.items() if re.search(r"TOKEN|SECRET|KEY|PASSWORD", k, re.I) and len(v) >= 6]
    return env, secrets


def redact(value, secrets):
    value = str(value)
    for secret in sorted(secrets, key=len, reverse=True):
        value = value.replace(secret, "[REDACTED]")
    return re.sub(r"(?i)(authorization\s*[:=]\s*(?:bearer\s+)?)[^\s\"']+", r"\1[REDACTED]", value)


def claude_command(data):
    executable = shutil.which("claude.exe") if os.name == "nt" else shutil.which("claude")
    if executable:
        argv = [executable]
    else:
        # npm's .cmd/.ps1 shims need a shell. Resolve the package's declared bin
        # (native in recent releases, JS in older ones) without running a shell.
        shim = shutil.which("claude.cmd") or shutil.which("claude.ps1")
        node = shutil.which("node")
        package = Path(shim).parent / "node_modules/@anthropic-ai/claude-code" if shim else None
        manifest = package / "package.json" if package else None
        entry = infra.read_json(manifest).get("bin", {}).get("claude") if manifest and manifest.is_file() else None
        script = inside(package, entry) if entry else None
        if script is None or not script.is_file():
            raise ValueError("未找到可直接调用的Claude Code；请先安装，不自动下载")
        if script.suffix.lower() == ".exe":
            argv = [str(script)]
        elif node and script.suffix.lower() in {".js", ".cjs", ".mjs"}:
            argv = [node, str(script)]
        else:
            raise ValueError("不支持的Claude Code入口，不通过shell猜测启动")
    toolset = "Read,Write,Edit,Glob,Grep,Bash" + (",Agent" if data["parallel"] else "")
    argv += ([] if data["parallel"] else ["--bare"])
    argv += ["-p", "--output-format", "stream-json", "--verbose", "--model", data["model"],
             "--tools", toolset, "--allowedTools", toolset, "--permission-mode", "dontAsk",
             "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}']
    if data["parallel"]:
        settings = {"disableAllHooks": True, "autoMemoryEnabled": False, "claudeMdExcludes": ["**"],
                    "enabledPlugins": {}, "disableClaudeAiConnectors": True}
        argv += ["--setting-sources", "", "--settings", json.dumps(settings)]
        agents = {"module-worker": {
            "description": "当前模块内有明确范围的前台实现或核验工作；由主执行者按需派发。",
            "prompt": "只执行分派的当前模块子任务。先读给定材料，遵守明确写入范围，返回产物、实际检查和缺口。不得改权威任务或验收标准，不再委托，不启动后台/远端/WMI作业，不访问或输出凭据。缺少范围时返回主执行者澄清。",
            "model": "inherit", "tools": ["Read", "Edit", "Bash", "Glob", "Grep"],
            "disallowedTools": ["Agent", "Task", "SendMessage"], "background": False}}
        argv += ["--agents", json.dumps(agents, ensure_ascii=False)]
    argv += ["--resume" if data["resume_run"] else "--session-id", data["session_id"]]
    return argv


def execute(root, run_id, owner, *, command=None, env_override=None):
    """command/env_override are test-only Python injection points, not CLI flags."""
    root = Path(root).resolve()
    folder, data = read_dispatch(root, run_id)
    if data["owner"] != owner:
        raise ValueError("当前接手者不匹配")
    runtime = infra.read_json(folder / "runtime.json")
    if runtime["phase"] != "prepared" or (folder / "started.json").exists():
        raise ValueError("本尝试已启动过，不能重复执行；先查询实际结果")
    if data.get("adapter_profile") != adapter_profile(data["parallel"]):
        raise ValueError("准备时的适配配置与当前入口不一致，须创建新尝试")
    freshness(root, data, launching=True)
    if inventory(Path(data["workspace"])) != data["baseline"]:
        raise ValueError("准备后工作副本发生变化；须重新准备尝试")
    argv = command or claude_command(data)
    env, secrets = local_profile()
    if data["parallel"]:
        # bare/SIMPLE exposes only Bash/Edit/Read in tested releases, even with
        # --agents. Use a project-owned empty profile for explicit subagents.
        profile = inside(root, META_DIR + "/claude-profile")
        profile.mkdir(parents=True, exist_ok=True)
        env["CLAUDE_CONFIG_DIR"] = str(profile)
        env["CLAUDE_CODE_SIMPLE"] = "0"
        env["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] = "1"
        env["CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"] = "1"
    if env_override:
        env.update(env_override)
        secrets += [v for k,v in env_override.items() if re.search(r"TOKEN|SECRET|KEY", k) and len(v) >= 6]
    active = inside(root, META_DIR + "/active")
    try:
        active.mkdir()
    except FileExistsError:
        raise ValueError("项目有在途或未核清的运行；先status，不自动抢占")
    # Recheck under the project lock: a concurrent caller may have completed
    # this attempt between our first read and acquiring the lock.
    if (folder / "started.json").exists() or infra.read_json(folder / "runtime.json")["phase"] != "prepared":
        active.rmdir()
        raise ValueError("本尝试已启动过，拒绝并发重放")
    work_active = workspace_lock(data["workspace"])
    try:
        work_active.mkdir()
    except FileExistsError:
        active.rmdir()
        raise ValueError("工作副本已被其他运行占用；不同项目也不能并发写同一副本")
    scope, proc, threads = None, None, []
    runtime.update(phase="running", controller_pid=os.getpid(), started_at=infra.now(),
                   ready_for_review=False, errors=[], runner_sha256=infra.digest(Path(__file__)),
                   process_scope_sha256=infra.digest(Path(__file__).with_name("process_scope.py")))
    try:
        infra.write_new(active / "owner.json", {"run_id": run_id, "pid": os.getpid(), "owner": owner})
        infra.write_new(work_active / "owner.json", {"root": str(root), "run_id": run_id, "pid": os.getpid()})
        # Claim the attempt before invocation. Even an uncertain launch is never replayed automatically.
        infra.write_new(folder / "started.json", {"at": infra.now(), "pid": os.getpid()})
        atomic_json(folder / "runtime.json", runtime)
        freshness(root, data, launching=True)
        if inventory(Path(data["workspace"])) != data["baseline"]:
            raise ValueError("取得占用后发现工作副本已变化；须新建尝试")
        scope = ProcessScope()
        proc = scope.start(argv, data["workspace"], env)
        runtime["process_pid"] = proc.pid
        atomic_json(folder / "runtime.json", runtime)
        events = queue.Queue(maxsize=512)

        def read_stream(stream, kind):
            for line in iter(stream.readline, b""):
                events.put((kind, line.decode("utf-8", errors="replace")))
            stream.close()

        def send_prompt():
            try:
                proc.stdin.write((folder / "BRIEF.md").read_bytes())
                proc.stdin.close()
            except (BrokenPipeError, OSError):
                pass

        threads = [threading.Thread(target=read_stream, args=(proc.stdout, "out"), daemon=True),
                   threading.Thread(target=read_stream, args=(proc.stderr, "err"), daemon=True)]
        for thread in threads:
            thread.start()
        threading.Thread(target=send_prompt, daemon=True).start()
        started, end_seen, final, result_count = time.monotonic(), None, None, 0
        phase, stderr, residual_stopped = "returned", [], False
        with (folder / "events.jsonl").open("x", encoding="utf-8") as log:
            while True:
                if (folder / "CANCEL").exists() and phase == "returned":
                    phase = "cancelled"
                    scope.stop()
                if time.monotonic() - started > data["timeout_seconds"] and phase == "returned":
                    phase = "timed_out"
                    scope.stop()
                try:
                    kind, line = events.get(timeout=0.05)
                    line = redact(line, secrets)
                    if kind == "err":
                        if sum(map(len, stderr)) < 65536:
                            stderr.append(line[:8192])
                    else:
                        try:
                            event = json.loads(line)
                            if not isinstance(event, dict):
                                raise ValueError("non-object event")
                        except (ValueError, TypeError):
                            runtime["errors"].append("CLI输出不是JSON事件")
                            continue
                        # Persist metadata, not tool arguments/thinking/environment dumps.
                        safe = {k: event[k] for k in ("type", "subtype", "session_id", "is_error", "num_turns") if k in event}
                        message = event.get("message") if isinstance(event.get("message"), dict) else {}
                        tools = [part.get("name") for part in message.get("content", [])
                                 if isinstance(part, dict) and part.get("type") == "tool_use"]
                        if tools:
                            safe["tool_names"] = tools
                            counts = runtime.setdefault("tool_calls", {})
                            for tool in tools:
                                if isinstance(tool, str):
                                    counts[tool] = counts.get(tool, 0) + 1
                        reported_model = message.get("model") or event.get("model")
                        if isinstance(reported_model, str):
                            safe["reported_model"] = reported_model
                            models = runtime.setdefault("reported_models", [])
                            if reported_model not in models:
                                models.append(reported_model)
                        log.write(json.dumps(safe, ensure_ascii=False) + "\n")
                        log.flush()
                        if event.get("type") == "result":
                            final, result_count = event, result_count + 1
                except queue.Empty:
                    pass
                if proc.poll() is not None:
                    end_seen = end_seen or time.monotonic()
                    if scope.active():
                        if time.monotonic() - end_seen > 0.5 and not residual_stopped:
                            runtime["errors"].append("主调用结束后仍有子作业，已终止本次进程树")
                            residual_stopped = True
                            scope.stop()
                        # A child can close/redirect stdout while continuing to write.
                        # Pipe EOF therefore cannot release the process-tree gate.
                        continue
                    if not any(t.is_alive() for t in threads) and events.empty():
                        break
        runtime.update(phase=phase, exit_code=proc.wait(), result_count=result_count)
        if stderr:
            (folder / "stderr.txt").write_text("".join(stderr), encoding="utf-8")
        if phase != "returned" or runtime["exit_code"] != 0 or result_count != 1 or not final or final.get("is_error") is not False or final.get("subtype") != "success":
            runtime["errors"].append("执行未正常完成或缺少唯一成功结束事件")
        if final:
            runtime["session_id"] = final.get("session_id")
            if runtime["session_id"] != data["session_id"]:
                runtime["errors"].append("返回会话ID不匹配")
            report_text = final.get("result", "")
            if not isinstance(report_text, str):
                report_text = ""
            (folder / "REPORT.md").write_text(report_text, encoding="utf-8", newline="\n")
            runtime["report_sha256"] = infra.digest(folder / "REPORT.md")
            try:
                fields = receipt(report_text, data)
                runtime["reported_outcome"] = fields["结果"]
                if fields["结果"] != "完成" or fields["子作业"] != "已结束":
                    runtime["errors"].append("回执为部分完成/受阻或子作业未结束")
            except ValueError as exc:
                runtime["errors"].append(str(exc))
        try:
            freshness(root, data)
            read_dispatch(root, run_id)
            after = inventory(Path(data["workspace"]))
            changed = {name: after.get(name) for name in set(after) | set(data["baseline"])
                       if after.get(name) != data["baseline"].get(name)}
            runtime["changes"] = changed
            runtime["workspace_after"] = after
            outside = [name for name in changed if not allowed(name, data["writes"])]
            if outside:
                runtime["errors"].append("工作副本发生范围外变动: " + ", ".join(outside))
        except (ValueError, OSError) as exc:
            runtime["errors"].append(str(exc))
        if phase == "returned" and runtime["errors"]:
            runtime["phase"] = "failed"
        runtime["ready_for_review"] = runtime["phase"] == "returned" and not runtime["errors"]
    except BaseException as exc:
        runtime["phase"] = "interrupted" if isinstance(exc, KeyboardInterrupt) else "failed"
        runtime["errors"].append(redact(str(exc), secrets))
        if proc:
            scope.stop()
            proc.wait(timeout=10)
    finally:
        if scope:
            scope.close()
        if proc:
            for thread in threads:
                thread.join(timeout=1)
            for stream in (proc.stdin, proc.stdout, proc.stderr):
                if stream and not stream.closed:
                    stream.close()
        runtime["ended_at"] = infra.now()
        atomic_json(folder / "runtime.json", runtime)
        if (active / "owner.json").exists():
            (active / "owner.json").unlink()
        active.rmdir()
        if (work_active / "owner.json").exists():
            (work_active / "owner.json").unlink()
        work_active.rmdir()
    return status(root, run_id)


def status(root, run_id):
    root = Path(root).resolve()
    folder, data = read_dispatch(root, run_id)
    state = infra.read_json(folder / "runtime.json")
    result = dict(state)
    if state["phase"] == "running" and not alive(state["controller_pid"]):
        result.update(phase="interrupted", ready_for_review=False,
                      recovery="控制进程已退出；核对产物后使用release解除占用，不自动重放")
    if state.get("ready_for_review"):
        try:
            freshness(root, data)
            if infra.digest(folder / "REPORT.md") != state["report_sha256"]:
                raise ValueError("回执已改变")
            if inventory(Path(data["workspace"])) != state["workspace_after"]:
                raise ValueError("返回后工作副本已改变，需重新核对证据")
        except (OSError, ValueError) as exc:
            result.update(ready_for_review=False, freshness_error=str(exc))
    result["note"] = "运行事实不是任务验收；不改TASKS、不自动派发"
    return result


def cancel(root, run_id):
    folder, _ = read_dispatch(Path(root).resolve(), run_id)
    state = infra.read_json(folder / "runtime.json")
    if state["phase"] != "running":
        return {"cancel_requested": False, "phase": state["phase"]}
    (folder / "CANCEL").touch(exist_ok=True)
    return {"cancel_requested": True, "note": "已请求取消，须查询实际停止结果"}


def release(root, run_id):
    root = Path(root).resolve()
    active = inside(root, META_DIR + "/active")
    record = infra.read_json(active / "owner.json")
    if record["run_id"] != run_id or alive(record["pid"]):
        raise ValueError("运行ID不匹配或控制进程仍存活，不解除占用")
    folder, data = read_dispatch(root, run_id)
    state = infra.read_json(folder / "runtime.json")
    if state.get("process_pid") and alive(state["process_pid"]):
        raise ValueError("原运行进程仍存活或身份未核清，不解除占用")
    work_active = workspace_lock(data["workspace"])
    if work_active.exists():
        work_record = infra.read_json(work_active / "owner.json")
        if work_record != {"root": str(root), "run_id": run_id, "pid": record["pid"]}:
            raise ValueError("工作副本占用归属不一致，不解除占用")
    state.update(phase="interrupted", ready_for_review=False, released_at=infra.now())
    atomic_json(folder / "runtime.json", state)
    (active / "owner.json").unlink()
    active.rmdir()
    if work_active.exists():
        (work_active / "owner.json").unlink()
        work_active.rmdir()
    return {"released": True, "note": "仅解除已退出控制进程的占用；未重试、未验收"}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest="command", required=True)
    for name in ("prepare", "run", "status", "cancel", "release"):
        c = s.add_parser(name)
        c.add_argument("--root", type=Path, required=True)
        c.add_argument("--run", required=True, dest="run_id")
        if name in {"prepare", "run"}:
            c.add_argument("--owner", required=True)
        if name == "prepare":
            c.add_argument("--task", required=True, dest="task_id")
            c.add_argument("--tasks")
            c.add_argument("--workspace", type=Path, required=True)
            c.add_argument("--input", action="append", default=[], dest="inputs")
            c.add_argument("--write", action="append", default=[], dest="writes")
            c.add_argument("--instructions", required=True)
            c.add_argument("--model", required=True)
            c.add_argument("--timeout", type=float, required=True)
            c.add_argument("--parallel", action="store_true")
            c.add_argument("--resume-run")
    args = vars(p.parse_args())
    command = args.pop("command")
    try:
        function = {"prepare": prepare, "run": execute, "status": status, "cancel": cancel, "release": release}[command]
        result = function(**args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if command == "run" and not result.get("ready_for_review") else 0
    except (OSError, ValueError, KeyError) as exc:
        print(json.dumps({"error": str(exc), "model_called": False if command != "run" else "查看运行记录"}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
