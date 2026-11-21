#!/usr/bin/env python3
"""reply_lint.py — 逐轮汇报机械自检（只检测不改写）。

规则权威在本技能 references/：
    过度防御表述诊断与改写.md（D1—D8、校准五档、A/B/C/P 分级）
    结论优先汇报结构.md（四段骨架、篇幅参考）
    缩写与术语首现规范.md（T7、白名单、待核标记）

本脚本只数结构信号：结论行、免责分布、空泛词、锚点密度、结尾软化、缩写首现。
它不判科学对错，不判作者身份，也不做自动改写。机械通过不等于表达合格。

用法：
    python reply_lint.py --file 草稿.md
    python reply_lint.py --stdin < 草稿.md
    python reply_lint.py --file 草稿.md --json
    python reply_lint.py --file 草稿.md --allow 允许缩写.txt --strict

退出码：0 通过；1 警告（人工复查）；2 失败（不得交付）。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

CJK_RE = re.compile(r"[\u4e00-\u9fff]")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s")
LIMITS_HEADING_RE = re.compile(r"^#{1,6}\s*.*?(边界|未做|未验证|局限|限制|风险|待核)")
TABLE_RE = re.compile(r"^\s*\|")
QUOTE_RE = re.compile(r"^\s*>")
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
URL_RE = re.compile(r"https?://[^\s)）,，；;]+")

OPENERS = (
    "我理解你的",
    "我理解你",
    "首先我们",
    "首先，我们",
    "让我们",
    "下面我",
    "以下是我",
    "关于你的问题",
    "感谢你的",
    "这个问题的背景",
    "好的，",
    "明白了",
)

CONCL_RE = re.compile(r"(结论|判断|已完成|未完成|不能|可以|建议|必须|交付|跑通|失败|通过|只有|无需|没有|已修|改为|已补|未做)")

HEDGE_PATTERNS = (
    re.compile(r"需要注意的是"),
    re.compile(r"需要指出的是"),
    re.compile(r"值得注意的是"),
    re.compile(r"不能完全排除"),
    re.compile(r"不排除"),
    re.compile(r"在一定程度上"),
    re.compile(r"可能存在"),
    re.compile(r"仅供参考"),
    re.compile(r"有待进一步"),
    re.compile(r"待进一步核实"),
    re.compile(r"视情况"),
    re.compile(r"受限于"),
    re.compile(r"由于[^。；\n]{0,8}有限"),
    re.compile(r"有一定"),
)

VAGUE_PATTERNS = (
    re.compile(r"赋能"),
    re.compile(r"抓手"),
    re.compile(r"闭环"),
    re.compile(r"鲁棒性"),
    re.compile(r"鲁棒"),
    re.compile(r"协同能力"),
    re.compile(r"体系化"),
    re.compile(r"全链路"),
    re.compile(r"一站式"),
    re.compile(r"多维度"),
    re.compile(r"全方位"),
    re.compile(r"生态化"),
    re.compile(r"底层逻辑"),
    re.compile(r"顶层设计"),
)

TEMPLATE_PATTERNS = (
    re.compile(r"我理解你的"),
    re.compile(r"首先我们"),
    re.compile(r"让我们"),
    re.compile(r"综上所述"),
    re.compile(r"总的来说"),
    re.compile(r"希望(能)?帮到你"),
    re.compile(r"希望(对你)?有帮助"),
    re.compile(r"请随时"),
    re.compile(r"如有需要"),
    re.compile(r"如需我"),
)

SOFT_PATTERNS = (
    re.compile(r"仅供参考"),
    re.compile(r"希望对你"),
    re.compile(r"希望有帮助"),
    re.compile(r"如有需要"),
    re.compile(r"请指正"),
    re.compile(r"如需我"),
    re.compile(r"随时告诉我"),
    re.compile(r"可以继续"),
)

ANCHOR_PATTERNS = (
    re.compile(
        r"\d+(?:\.\d+)?\s*(?:%|‰|s|ms|min|h|MB|GB|TB|Mbps|Gbps|km|m|kg|Wh|W|°|单|条|行|字|项|个|次|秒|分|倍)"
    ),
    re.compile(r"`[^`\n]{2,}`"),
    re.compile(r"[\w./\\-]+\.(?:py|md|json|csv|png|txt|yaml|yml|toml|jsonl)(?::\d+)?", re.IGNORECASE),
    re.compile(r":\d+(?:-\d+)?"),
    re.compile(r"\b(?:python|pytest|git|pnpm|npm|pip|uv)\s+[\w./-]+"),
)

ACR_RE = re.compile(r"\b[A-Z][A-Z0-9]{1,7}\b")
ID_LIKE_RE = re.compile(r"^(?:[A-Z]\d+|FIG\d+)$")  # 规则标号（G0、T1、E1、FIG4）不是缩写
BRACKET_RE = re.compile(r"[（(][^（()）\n]{2,160}[）)]")
LATIN_WORD_RE = re.compile(r"[A-Za-z]{2,}")

DEFAULT_ALLOW = frozenset(
    {
        # 计量单位
        "MB", "GB", "TB", "KB", "MS", "KM", "KG", "WH", "KW", "MW", "HZ", "KHZ", "MHZ", "GHZ",
        # 文件格式
        "PDF", "DOCX", "XLSX", "PPTX", "PNG", "JPG", "JPEG", "GIF", "SVG", "CSV", "JSON", "JSONL",
        "YAML", "YML", "TOML", "XML", "HTML", "HTTP", "HTTPS", "MD", "PY", "ZIP", "TXT",
        # 通用标识与约定
        "UTC", "GPS", "API", "GPU", "CPU", "URL", "URI", "ID", "OK", "OS", "IO", "SDK",
        # 仓库常见文件名（是文件名，不是缩写，按 T7 的文件名例外免展开）
        "AGENTS", "CLAUDE", "README", "SOURCES", "TASKS", "PLAN", "LICENSE", "CHANGELOG", "SKILL",
        # 专名与标准编号
        "WGS84", "WGS72", "J2000", "ISO", "IEC", "IEEE", "GB",  # GB 同时是吉字节，白名单只免展开
    }
)


def cjk_count(text: str) -> int:
    """统计汉字个数；标点、数字、英文不计。"""
    return len(CJK_RE.findall(text))


def _clean_inline(text: str, *, keep_code: bool) -> str:
    """去 URL；行内代码保留内容（供锚点统计）或整体删除（供缩写扫描）。"""
    text = URL_RE.sub(" ", text)
    if keep_code:
        return text.replace("`", " ")
    return INLINE_CODE_RE.sub(" ", text)


def split_text(text: str) -> tuple[str, str, str, str]:
    """切成四段：正文（含代码内容）、正文（不含代码）、边界段、去代码块后的全文。"""
    main_parts: list[str] = []
    main_nocode_parts: list[str] = []
    limits_parts: list[str] = []
    tail_parts: list[str] = []
    in_fence = False
    in_limits = False

    for line in text.splitlines():
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        tail_parts.append(line)
        if HEADING_RE.match(line):
            in_limits = bool(LIMITS_HEADING_RE.match(line))
            continue
        if in_limits:
            limits_parts.append(_clean_inline(line, keep_code=False))
            continue
        if TABLE_RE.match(line) or QUOTE_RE.match(line):
            continue
        main_parts.append(_clean_inline(line, keep_code=True))
        main_nocode_parts.append(_clean_inline(line, keep_code=False))

    return "\n".join(main_parts), "\n".join(main_nocode_parts), "\n".join(limits_parts), "\n".join(tail_parts)


def _first_sentence(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line:
            return line
    return ""


def _acronym_defined(text: str, token: str, index: int) -> bool:
    """判断 token 在 index 处是否已有全称定义：附近括号内既有该缩写，又有至少两个英文词。"""
    window_start = max(0, index - 90)
    window_end = min(len(text), index + 90)
    window = text[window_start:window_end]
    for m in BRACKET_RE.finditer(window):
        bracket = m.group(0)
        if token not in bracket:
            continue
        inside = LATIN_WORD_RE.findall(bracket.replace(token, " "))
        if len(inside) >= 2:
            return True
        before = window[: m.start()]
        before_words = LATIN_WORD_RE.findall(before[-70:])
        if len(before_words) >= 2:
            return True
    return False


def find_undefined_acronyms(text: str, allow: frozenset[str] | set[str]) -> list[tuple[str, int]]:
    """返回未定义缩写的 (token, 首次出现下标)，按出现顺序。

    判定只做一件事：首现附近 90 字内是否有括号把该缩写与至少两个英文词放在一起。
    全称真假、是否白名单外的新概念，由人和项目术语表判断。
    """
    first: dict[str, int] = {}
    for m in ACR_RE.finditer(text):
        token = m.group(0)
        index = m.start()
        if token in first:
            continue
        before = text[index - 1] if index > 0 else " "
        after = text[index + len(token)] if index + len(token) < len(text) else " "
        if before in "/\\-._" or after in "/\\":
            continue
        if ID_LIKE_RE.match(token) or token in DEFAULT_ALLOW or token in allow:
            first.setdefault(token, index)
            continue
        if _acronym_defined(text, token, index):
            first.setdefault(token, index)
            continue
        first.setdefault(token, index)

    undefined: list[tuple[str, int]] = []
    for token, index in sorted(first.items(), key=lambda kv: kv[1]):
        if token in DEFAULT_ALLOW or token in allow or ID_LIKE_RE.match(token):
            continue
        if not _acronym_defined(text, token, index):
            undefined.append((token, index))
    return undefined


def lint_text(text: str, *, allow: set[str] | None = None, max_chars: int | None = None) -> dict:
    """对一段汇报文本做机械自检，返回结构化结果。"""
    allow_set: frozenset[str] = frozenset(allow or ())
    if not text.strip():
        return {
            "verdict": 0,
            "verdict_text": "通过",
            "stats": {"cjk": 0, "anchors": 0, "density_per_kcjk": 0.0},
            "checks": [
                {"id": "R0", "name": "输入", "level": "info", "message": "输入为空，未检测", "hits": []}
            ],
        }

    main_text, main_nocode, _limits_text, tail_text = split_text(text)
    main_cjk = cjk_count(main_text)
    stats = {"cjk": main_cjk, "anchors": 0, "density_per_kcjk": 0.0, "chars": len(text)}
    checks: list[dict] = []

    # R1 结论行
    head = main_text[:200]
    opener = next((o for o in OPENERS if o in head), None)
    first_line = _first_sentence(main_text)
    if opener and not CONCL_RE.search(head):
        checks.append(
            {"id": "R1", "name": "结论行", "level": "fail",
             "message": f"开场是导览且前 200 字无判断句（命中：{opener}）", "hits": [opener]}
        )
    elif opener:
        checks.append(
            {"id": "R1", "name": "结论行", "level": "warn",
             "message": f"开场是导览，判断被推迟（命中：{opener}）", "hits": [opener]}
        )
    else:
        checks.append(
            {"id": "R1", "name": "结论行", "level": "pass",
             "message": f"首句直接进入内容：{first_line[:40]}", "hits": []}
        )

    # R2 免责分布（只统计边界段外）
    hedge_hits: list[str] = []
    for pat in HEDGE_PATTERNS:
        hedge_hits.extend(m.group(0) for m in pat.finditer(main_text))
    hedge_counter = Counter(hedge_hits)
    hedge_total = len(hedge_hits)
    if hedge_total >= 5:
        checks.append(
            {"id": "R2", "name": "免责分布", "level": "fail",
             "message": f"边界段外免责 {hedge_total} 处，应合并进边界段", "hits": hedge_hits}
        )
    elif hedge_total >= 3:
        checks.append(
            {"id": "R2", "name": "免责分布", "level": "warn",
             "message": f"边界段外免责 {hedge_total} 处，建议合并", "hits": hedge_hits}
        )
    elif any(count >= 2 for count in hedge_counter.values()):
        repeated = [w for w, c in hedge_counter.items() if c >= 2]
        checks.append(
            {"id": "R2", "name": "免责分布", "level": "warn",
             "message": f"同一免责重复出现：{'、'.join(repeated)}", "hits": repeated}
        )
    else:
        checks.append(
            {"id": "R2", "name": "免责分布", "level": "pass",
             "message": f"边界段外免责 {hedge_total} 处", "hits": hedge_hits}
        )

    # R3 空泛词
    vague_hits: list[str] = []
    for pat in VAGUE_PATTERNS:
        vague_hits.extend(m.group(0) for m in pat.finditer(main_text))
    if len(vague_hits) >= 6:
        level, message = "fail", f"空泛抽象词 {len(vague_hits)} 处，须换成具体事实"
    elif len(vague_hits) >= 3:
        level, message = "warn", f"空泛抽象词 {len(vague_hits)} 处，建议替换"
    else:
        level, message = "pass", f"空泛抽象词 {len(vague_hits)} 处"
    checks.append({"id": "R3", "name": "空泛词", "level": level, "message": message, "hits": vague_hits})

    # R4 模板残留
    template_hits: list[str] = []
    for pat in TEMPLATE_PATTERNS:
        template_hits.extend(m.group(0) for m in pat.finditer(main_text))
    unique_template = sorted(set(template_hits))
    if len(unique_template) >= 2:
        checks.append(
            {"id": "R4", "name": "模板残留", "level": "fail",
             "message": f"模板化表达 {len(unique_template)} 种：{'、'.join(unique_template)}", "hits": unique_template}
        )
    elif unique_template:
        checks.append(
            {"id": "R4", "name": "模板残留", "level": "warn",
             "message": f"模板化表达：{unique_template[0]}", "hits": unique_template}
        )
    else:
        checks.append({"id": "R4", "name": "模板残留", "level": "pass", "message": "未命中", "hits": []})

    # R5 锚点密度
    anchors = sum(len(p.findall(main_text)) for p in ANCHOR_PATTERNS)
    density = anchors / (main_cjk / 1000) if main_cjk else 0.0
    stats["anchors"] = anchors
    stats["density_per_kcjk"] = round(density, 1)
    if main_cjk > 600 and density < 8:
        checks.append(
            {"id": "R5", "name": "锚点密度", "level": "warn",
             "message": f"每千字锚点 {density:.1f} 处（阈值 8），结论缺少可定位依据", "hits": []}
        )
    else:
        checks.append(
            {"id": "R5", "name": "锚点密度", "level": "pass",
             "message": f"每千字锚点 {density:.1f} 处，共 {anchors} 处", "hits": []}
        )

    # R6 结尾软化
    tail = tail_text.strip()[-300:]
    soft_hits: list[str] = []
    for pat in SOFT_PATTERNS:
        soft_hits.extend(m.group(0) for m in pat.finditer(tail))
    if soft_hits:
        checks.append(
            {"id": "R6", "name": "结尾软化", "level": "warn",
             "message": f"结尾有软化表述：{'、'.join(sorted(set(soft_hits)))}", "hits": soft_hits}
        )
    else:
        checks.append({"id": "R6", "name": "结尾软化", "level": "pass", "message": "未命中", "hits": []})

    # R7 缩写首现（行内代码与路径已排除）
    undefined = find_undefined_acronyms(main_nocode, allow_set)
    if len(undefined) >= 3:
        checks.append(
            {"id": "R7", "name": "缩写首现", "level": "fail",
             "message": f"{len(undefined)} 个缩写首现无全称：{'、'.join(t for t, _ in undefined)}",
             "hits": [t for t, _ in undefined]}
        )
    elif undefined:
        checks.append(
            {"id": "R7", "name": "缩写首现", "level": "warn",
             "message": f"缩写首现无全称：{'、'.join(t for t, _ in undefined)}",
             "hits": [t for t, _ in undefined]}
        )
    else:
        checks.append({"id": "R7", "name": "缩写首现", "level": "pass", "message": "未命中", "hits": []})

    # 可选的篇幅上限
    if max_chars is not None and main_cjk > max_chars:
        checks.append(
            {"id": "R8", "name": "篇幅", "level": "warn",
             "message": f"正文 {main_cjk} 字，超过参考上限 {max_chars} 字", "hits": []}
        )

    levels = {c["level"] for c in checks}
    if "fail" in levels:
        verdict, verdict_text = 2, "失败"
    elif "warn" in levels:
        verdict, verdict_text = 1, "警告"
    else:
        verdict, verdict_text = 0, "通过"

    return {"verdict": verdict, "verdict_text": verdict_text, "stats": stats, "checks": checks}


def load_allow(path: Path) -> set[str]:
    """从纯文本读白名单：一行一个缩写，# 开头为注释。"""
    allow: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        allow.add(line)
    return allow


def read_text(path: Path) -> str:
    """读文本：先 UTF-8（含 BOM），失败再按 GB18030。"""
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return path.read_text(encoding="gb18030", errors="replace")


def render_human(result: dict, *, strict: bool = False) -> str:
    lines = ["逐轮汇报自检（只检测不改写；判据见 references/ 三份文件）", ""]
    stats = result["stats"]
    lines.append(
        f"统计：汉字 {stats.get('cjk', 0)}；锚点 {stats.get('anchors', 0)} 处；"
        f"密度 {stats.get('density_per_kcjk', 0.0)}/千字"
    )
    label = {"pass": "通过", "info": "信息", "warn": "警告", "fail": "失败"}
    for check in result["checks"]:
        lines.append(f"[{label.get(check['level'], check['level'])}] {check['id']} {check['name']}：{check['message']}")
    lines.append("")
    verdict = result["verdict"]
    if verdict == 2 or (strict and verdict == 1):
        lines.append("结论：不得交付——先改失败项，再重跑。")
    elif verdict == 1:
        lines.append("结论：人工复查警告项后再交付。")
    else:
        lines.append("结论：机械项通过；判断是否成立仍看证据。")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="逐轮汇报机械自检（只检测不改写）")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--file", type=Path, help="待检文本路径（Markdown 或纯文本）")
    source.add_argument("--stdin", action="store_true", help="从标准输入读取")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    parser.add_argument("--strict", action="store_true", help="警告也按失败处理")
    parser.add_argument("--allow", type=Path, help="追加白名单文件：一行一个缩写")
    parser.add_argument("--max-chars", type=int, default=None, help="正文汉字数参考上限")
    args = parser.parse_args(argv)

    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass

    if args.stdin:
        text = sys.stdin.read()
    else:
        try:
            text = read_text(args.file)
        except OSError as exc:
            print(f"读取失败：{exc}", file=sys.stderr)
            return 2

    allow = load_allow(args.allow) if args.allow else set()
    result = lint_text(text, allow=allow, max_chars=args.max_chars)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render_human(result, strict=args.strict))

    if result["verdict"] == 2:
        return 2
    if result["verdict"] == 1 and args.strict:
        return 2
    return result["verdict"]


if __name__ == "__main__":
    raise SystemExit(main())
