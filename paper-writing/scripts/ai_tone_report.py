# -*- coding: utf-8 -*-
"""成稿去AI味 · 前后对比报告：指标前后对比 + 分级问题清单 + 标记前后对照。

改编自 lieflat-less-ai-tone 的 report.py（CC BY-NC 4.0，
https://github.com/larashero3-dotcom/lieflat-less-ai-tone ，改动见文末清单）。
规则与判据权威在本技能 references/（论文组织与语言规范.md、成稿去AI味检测与语义判据.md），
来源证据登记见仓库 SOURCES.md。

默认输出 Markdown 报告（与用户文稿同格式，md 标记原样保留，
可直接复制回写作流程；`--format html` 生成单文件网页版）。
结构：metric_rows / findings / semantic_groups / diff_blocks 先算出与格式无关的数据，
再由 render_md / render_html 输出；两种格式内容同源，不再各写一套。

用法（改动前后各跑一次 ai_tone_detect.py --json，再生成报告；建议设置 PYTHONUTF8=1）：
    python ai_tone_detect.py 原稿.md --json > 改前.json
    python ai_tone_detect.py 改后.md --json > 改后.json
    python ai_tone_report.py 原稿.md 改后.md 改前.json 改后.json \
        [--semantic 判读结果.json] [--out 报告.md] [--format md|html]

--semantic 可选：ai_tone_detect.py --candidates 抽取的候选经会话内模型按
成稿去AI味检测与语义判据.md 判读后的 JSON（条目带 label/confidence/reason）。

纯标准库，无外部依赖；只用本地文件，不联网、不调用模型。
md 版对照约定：<del>删除线</del> = 被改掉原文，<ins>下划线</ins> = 改后新文字。
"""
import argparse
import difflib
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from ai_tone_detect import REGEX_HITS  # 名字 → 级别映射（A/B/H/X）

# ---------------- 指标呈现配置 ----------------

# HTML 顶部指标对比表：键 → (展示名, 方向说明, 人类参考)
# 参考值来自来源研究 270 对配对实测中位值（通识语料；证据登记见仓库 SOURCES.md）。
METRIC_ROWS = [
    ("翻案腔", "不是A而是B 对举", "low", 0.22),
    ("提示语冒号", "结论提示冒号", "low", 0.08),
    ("顿号并列≥3", "密集并列", "low", 1.78),
    ("过长前置定语", "前置定语长", "low", 0.1),
]

# 第三列为 arrow 方向（"low"=低更好，None=不判方向）；CV 与分节密度按实测证据
# 人机无差异/属刊会规范，不判改善方向，说明并入参考列。
STRUCT_ROWS = [
    ("句长CV", "句长起伏", None, "人类≈0.54 / AI≈0.46；均匀度人机无差异，只报告"),
    ("节长CV", "节长参差", None, "人类≈0.83 / AI≈0.31；只报告"),
    ("小标题/千字", "分节密度", None, "人类≈0.32 / AI≈1.26；论文编号小节属刊会规范"),
    ("两句同构/百段", "相邻句同构", "low", "人类≈5.52 / AI≈8.71"),
    ("三句同构/百段", "三连同构(粗筛)", "low", "人类≈0.41 / AI≈0.84；精判走语义层"),
    ("mtld粗估", "换词多样性", "low", "人类≈143 / AI≈227"),
]

FINGERPRINT_ROWS = [
    ("破折号", "分模型方向相反（一多一少），按本篇用法逐处判断"),
    ("分号", "单模型指纹；可安全拆句时建议改"),
    ("引号", "单模型偏少信号，报告用不改"),
]

CSS = """
body{font-family:-apple-system,"PingFang SC",sans-serif;max-width:760px;margin:40px auto;line-height:1.9;font-size:16px;padding:0 20px;color:#222}
h1{font-size:22px}h2{font-size:19px;border-bottom:2px solid #ccc;padding-bottom:6px;margin-top:2.2em}
h3{font-size:16px;margin-bottom:0.4em}
table{border-collapse:collapse;width:100%;font-size:14px;margin:0.6em 0 1.4em}
th,td{border:1px solid #ddd;padding:5px 10px;text-align:left;vertical-align:top}
th{background:#f5f5f5}
.warn{background:#fff3cd;padding:14px 18px;border-radius:8px;margin-bottom:1.5em;font-size:14px}
.legend{color:#555;margin-bottom:2em;font-size:14px}
.chg,.ins{color:#d32f2f;font-weight:600}
.del{color:#aaa;text-decoration:line-through}
.up{color:#c62828;font-weight:600}.down{color:#2e7d32;font-weight:600}.flat{color:#777}
.tagA{background:#e3f2fd;padding:1px 7px;border-radius:4px;font-size:12px}
.tagB{background:#fff3e0;padding:1px 7px;border-radius:4px;font-size:12px}
.tagC{background:#f3e5f5;padding:1px;border-radius:4px;font-size:12px}
.tagF{background:#eceff1;padding:1px 7px;border-radius:4px;font-size:12px}
.tagX{background:#fafafa;color:#888;padding:1px 7px;border-radius:4px;font-size:12px}
.tagH{background:#fce4ec;padding:1px 7px;border-radius:4px;font-size:12px}
.small{color:#777;font-size:13px}
.human{color:#2e7d32}
details{margin:0.3em 0}
summary{cursor:pointer}
p{margin:0 0 1.1em}
"""


LEVELS = [("A", "机械改（模型复核误报后处理）", "tagA"),
          ("B", "建议改（模型逐条筛选后处理）", "tagB"),
          ("H", "人审区（默认保留，用户主动要求时再审）", "tagH"),
          ("X", "已否决特征（实测不是 AI 味——不要改）", "tagX")]

SEM_GROUPS = {"rename": "同义重命名（段级）", "cohesion": "衔接方式（段间接口）",
              "colon": "冒号分类", "iso3": "高度同构三连"}
# 重命名重灾 / 衔接连环（连续长度另算）/ 冒号真信号 / 同构真信号
SEM_FLAGGED = {"2组", "3组及以上", "明确承接", "结论提示", "高度同构"}

METRIC_NOTE = ("参考值=来源研究 270 对同题配对实测人类中位（通识语料，学术语料未重标定），"
               "证据登记见仓库 SOURCES.md。")
SEM_NOTE = ("四项在 270 对配对语料统计显著；同义重命名为单模型判据（弱一档）。"
            "判据见本技能 references/成稿去AI味检测与语义判据.md。")
C_LEVEL_NOTE = ("C 级（结构/节奏）见指标表，只报告不追求推到目标值；F 指纹见表内指纹行；"
                "比喻贴切度只能人审；本轮默认保留。用户主动要求时再列出相关原句供判断。")


def esc(s):
    return html.escape(str(s), quote=False)


# ---------------- 数据层（与格式无关） ----------------

def direction(before, after, better="low"):
    """better: 'low'=数值低更好, 'high'=数值高更好, None=不判方向 → (css 类, 箭头)"""
    if before is None or after is None or before == after:
        return "flat", "→"
    if better == "low":
        return ("down", "↓") if after < before else ("up", "↑")
    if better == "high":
        return ("up", "↑") if after > before else ("down", "↓")
    return "flat", "→"


def _shown(v):
    return v if v is not None else "—"


def metric_rows(d0, d1):
    rows = []
    for key, name, better, ref in METRIC_ROWS:
        v0, v1 = d0["density"].get(key), d1["density"].get(key)
        rows.append(dict(name=name, v0=_shown(v0), v1=_shown(v1),
                         dir=direction(v0, v1, better), ref=f"≈{ref}", fingerprint=False))
    for key, name, better, ref in STRUCT_ROWS:
        v0, v1 = d0["structure"].get(key), d1["structure"].get(key)
        rows.append(dict(name=name, v0=_shown(v0), v1=_shown(v1),
                         dir=direction(v0, v1, better), ref=ref, fingerprint=False))
    for key, note in FINGERPRINT_ROWS:
        v0, v1 = d0["char_density"].get(key), d1["char_density"].get(key)
        rows.append(dict(name=key, v0=v0, v1=v1, dir=direction(v0, v1, None),
                         ref=note, fingerprint=True))
    return rows


def findings(d):
    """[(级别, 标题, css 类, [(名称, 命中列表)])]，只含有命中的级别。"""
    out = []
    for lvl, title, cls in LEVELS:
        items = [(nm, d["hits"].get(nm, [])) for lv, nm, *_ in REGEX_HITS if lv == lvl]
        items = [(nm, hs) for nm, hs in items if hs]
        if items:
            out.append((lvl, title, cls, items))
    return out


def _longest_chain(items):
    best = cur = 0
    for c in items:
        cur = cur + 1 if c.get("label") == "明确承接" else 0
        best = max(best, cur)
    return best


def semantic_groups(sem):
    """语义层判读：每组的计数、衔接最长连环与需展示的条目。"""
    groups = []
    for key, title in SEM_GROUPS.items():
        items = [c for c in (sem or {}).get(key, []) if c.get("label")]
        if not items:
            continue
        counts = {}
        for c in items:
            counts[c["label"]] = counts.get(c["label"], 0) + 1
        flagged = []
        for c in [c for c in items if c.get("label") in SEM_FLAGGED][:15]:
            text = c.get("para") or " → ".join(filter(None, [
                c.get("prev_tail"), c.get("next_head")])) or c.get("sentence") \
                or "／".join(c.get("sents") or [])
            flagged.append(dict(label=c["label"], conf=c.get("confidence", ""),
                                loc=f"{c.get('file', '')}:{c.get('line', '')}",
                                text=text[:110], reason=c.get("reason", "")[:100]))
        groups.append(dict(title=title, n=len(items),
                           counts=sorted(counts.items(), key=lambda x: -x[1]),
                           chain=_longest_chain(items) if key == "cohesion" else None,
                           flagged=flagged))
    return groups


def para_split(text):
    """按空行分段，保留原文形态（不去 markdown 标记）。"""
    return [p for p in re.split(r"\n\s*\n", text) if p.strip()]


def inline_segments(a, b):
    """段内字符级 diff → [(op, 文本)]，op ∈ equal/del/ins/chg（chg=替换后的新文字）。"""
    segs = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag == "equal":
            segs.append(("equal", a[i1:i2]))
        elif tag == "delete":
            segs.append(("del", a[i1:i2]))
        elif tag == "insert":
            segs.append(("ins", b[j1:j2]))
        else:
            segs += [("del", a[i1:i2]), ("chg", b[j1:j2])]
    return segs


def diff_blocks(text0, text1):
    """段级 diff → 段落列表，每段为 [(op, 文本)]；段数不等时多出的段落单独标。"""
    p0, p1 = para_split(text0), para_split(text1)
    blocks = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, p0, p1, autojunk=False).get_opcodes():
        if tag == "equal":
            blocks += [[("equal", p)] for p in p0[i1:i2]]
        elif tag == "delete":
            blocks += [[("del", p)] for p in p0[i1:i2]]
        elif tag == "insert":
            blocks += [[("ins", p)] for p in p1[j1:j2]]
        else:
            blocks += [inline_segments(pa, pb) for pa, pb in zip(p0[i1:i2], p1[j1:j2])]
            blocks += [[("del", p)] for p in p0[i1 + (j2 - j1):i2]]
            blocks += [[("ins", p)] for p in p1[j1 + (i2 - i1):j2]]
    return blocks


# ---------------- Markdown 渲染 ----------------
# 对照用 <del>/<ins> 行内 HTML 而非 ~~/**：改动常落在原有 **加粗**、## 标题等标记内部，
# ~~/** 会与原文标记配对错乱；<del>/<ins> 与任何 md 标记零冲突，常见预览器均正常渲染。

MD_TAG = {"equal": "{}", "del": "<del>{}</del>", "ins": "<ins>{}</ins>", "chg": "<ins>{}</ins>"}


def _md_semantic(sem):
    if not sem:
        return []
    lines = ["## 语义层判读（会话内模型按封闭判据逐条判断）", "", SEM_NOTE, ""]
    for g in semantic_groups(sem):
        stats = "，".join(f"{k} {v}" for k, v in g["counts"])
        lines += [f"### {g['title']}（{g['n']} 条：{stats}）", ""]
        if g["chain"] is not None:
            note = f"最长连环 {g['chain']} 个接口；≥6 为报告门槛，人类中位 2。"
            lines += [f"⚠ {note}" if g["chain"] >= 6 else note, ""]
        for c in g["flagged"]:
            lines.append(f"- **{c['label']}**（置信:{c['conf']}）`{c['loc']}`　{c['text']}"
                         + (f"　理由：{c['reason']}" if c["reason"] else ""))
        lines.append("")
    return lines


def render_md(t0, t1, d0, d1, sem, name0, name1):
    table = ["| 指标 | 改前 | 改后 | 变化 | 人类参考 |", "|---|---|---|---|---|"]
    for r in metric_rows(d0, d1):
        label = f"{r['name']}（指纹）" if r["fingerprint"] else r["name"]
        table.append(f"| {label} | {r['v0']} | {r['v1']} | {r['dir'][1]} | {r['ref']} |")
    table += ["", "↓/↑ = 向人类参考方向改善/恶化；指纹行不判方向。" + METRIC_NOTE]

    found = []
    for lvl, title, _, items in findings(d0):
        found.append(f"### {lvl} 级 · {title}\n")
        for nm, hs in items:
            lines = [f"**{nm}** {len(hs)} 处", ""]
            lines += [f"- `{h['file']}:{h['line']}`　{h['excerpt']}" for h in hs[:20]]
            found.append("\n".join(lines + [""]))

    diff = ["".join(MD_TAG[op].format(t) for op, t in blk) for blk in diff_blocks(t0, t1)]
    parts = ["# 成稿去AI味 · 前后对比报告", "", f"{name0} → {name1}", "",
             "标记约定：<del>删除线</del> = 被改掉/删掉的原文；<ins>下划线</ins> = 改后的新文字；"
             "指标表 ↓/↑ = 相对人类参考的改善/恶化。", "",
             "## 一、指标前后对比", "", "\n".join(table)]
    sem_lines = _md_semantic(sem)
    if sem_lines:
        parts.append("\n".join(sem_lines))
    parts += ["## 二、分级问题清单（改前检测）", "", "\n".join(found), C_LEVEL_NOTE, "",
              "## 三、前后对照（改后稿全文，改动处标记）", "", "\n\n".join(diff)]
    return "\n\n".join(parts)


# ---------------- HTML 渲染 ----------------

HTML_TAG = {"equal": "{}", "del": '<span class="del">{}</span>',
            "ins": '<span class="ins">{}</span>', "chg": '<span class="chg">{}</span>'}


def _html_table(d0, d1):
    rows = []
    for r in metric_rows(d0, d1):
        arrow = f'<span class="{r["dir"][0]}">{r["dir"][1]}</span>'
        if r["fingerprint"]:
            rows.append(f"<tr><td>{esc(r['name'])}<span class='small'>（指纹）</span></td>"
                        f"<td>{r['v0']}</td><td>{r['v1']}</td><td>{arrow}</td>"
                        f'<td class="small">{esc(r["ref"])}</td></tr>')
        else:
            rows.append(f"<tr><td>{esc(r['name'])}</td><td>{r['v0']}</td><td>{r['v1']}</td>"
                        f'<td>{arrow}</td><td class="human">{esc(r["ref"])}</td></tr>')
    return ("<table><tr><th>指标</th><th>改前</th><th>改后</th><th>变化</th>"
            "<th>人类参考</th></tr>" + "".join(rows) + "</table>"
            '<p class="small">↓/↑ 绿色=向人类参考方向改善，红色=恶化；指纹行不判方向。'
            + METRIC_NOTE + "</p>")


def _html_semantic(sem):
    if not sem:
        return ""
    out = ["<h2>语义层判读（会话内模型按封闭判据逐条判断）</h2>", f'<p class="small">{SEM_NOTE}</p>']
    for g in semantic_groups(sem):
        stats = "，".join(f"{esc(k)} {v}" for k, v in g["counts"])
        out.append(f"<h3>{esc(g['title'])} <span class='small'>{g['n']} 条：{stats}</span></h3>")
        if g["chain"] is not None:
            note = f"（最长连环 {g['chain']} 个接口；≥6 为报告门槛，人类中位 2）"
            out.append(f'<p><span class="up">⚠ {note}</span></p>' if g["chain"] >= 6 else f"<p>{note}</p>")
        for c in g["flagged"]:
            out.append(f"<p class='small'><strong>{esc(c['label'])}</strong>"
                       f"（置信:{esc(c['conf'])}）{esc(c['loc'])}　{esc(c['text'])}"
                       + (f"<br>理由：{esc(c['reason'])}" if c["reason"] else "") + "</p>")
    return "\n".join(out)


def _html_findings(d):
    out = []
    for lvl, title, cls, items in findings(d):
        out.append(f'<h3><span class="{cls}">{lvl}</span> {esc(title)}</h3>')
        for nm, hs in items:
            out += [f"<div><strong>{esc(nm)}</strong> {len(hs)} 处",
                    "<details><summary class='small'>展开命中</summary>"]
            out += [f"<p class='small'>{esc(h['file'])}:{h['line']}　{esc(h['excerpt'])}</p>"
                    for h in hs[:20]]
            out.append("</details></div>")
    return "\n".join(out)


def render_html(t0, t1, d0, d1, sem, name0, name1):
    diff = ["<p>" + "".join(HTML_TAG[op].format(esc(t)) for op, t in blk) + "</p>"
            for blk in diff_blocks(t0, t1)]
    parts = ["<!DOCTYPE html><html><head><meta charset=\"utf-8\">",
             f"<title>成稿去AI味报告 · {esc(name0)}</title><style>{CSS}</style></head><body>",
             "<h1>成稿去AI味 · 前后对比报告</h1>",
             f'<p class="small">{esc(name0)} → {esc(name1)}</p>',
             '<div class="legend">图例：<span class="chg">红色</span> = 改后的新文字；'
             '<span class="del">灰色删除线</span> = 被改掉/删掉的原文；'
             '指标表 ↓/↑ = 相对人类参考的改善/恶化。</div>',
             "<h2>一、指标前后对比</h2>", _html_table(d0, d1), _html_semantic(sem),
             "<h2>二、分级问题清单（改前检测）</h2>", _html_findings(d0),
             f'<p class="small">{C_LEVEL_NOTE}</p>',
             "<h2>三、标红前后对照</h2>", "\n".join(diff), "</body></html>"]
    return "\n".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("before", help="改前文本文件")
    ap.add_argument("after", help="改后文本文件")
    ap.add_argument("json_before", help="改前 ai_tone_detect --json 输出")
    ap.add_argument("json_after", help="改后 ai_tone_detect --json 输出")
    ap.add_argument("--semantic", help="语义判读结果 JSON（候选+label 字段）")
    ap.add_argument("--format", choices=["md", "html"], default="md",
                    help="报告格式：md=Markdown（默认，与文稿同格式可复制），html=单文件网页")
    ap.add_argument("--out", default=None,
                    help="输出路径；默认按格式取名 去AI味对比报告.md / .html")
    args = ap.parse_args()

    t0 = Path(args.before).read_text(encoding="utf-8-sig", errors="ignore")
    t1 = Path(args.after).read_text(encoding="utf-8-sig", errors="ignore")
    d0 = json.loads(Path(args.json_before).read_text(encoding="utf-8-sig"))
    d1 = json.loads(Path(args.json_after).read_text(encoding="utf-8-sig"))
    sem = None
    if args.semantic:
        sem = json.loads(Path(args.semantic).read_text(encoding="utf-8-sig"))

    out = args.out or f"去AI味对比报告.{args.format}"
    if args.format == "md":
        page = render_md(t0, t1, d0, d1, sem, args.before, args.after)
    else:
        page = render_html(t0, t1, d0, d1, sem, args.before, args.after)
    Path(out).write_text(page, encoding="utf-8")
    n_han = lambda t: len(re.findall(r"[一-鿿]", t))
    print(f"报告 → {out}（改前 {n_han(t0)} 字 / 改后 {n_han(t1)} 字，"
          f"变化 {n_han(t1) - n_han(t0):+d}）")


if __name__ == "__main__":
    main()

# 改编自 lieflat-less-ai-tone scripts/report.py（CC BY-NC 4.0，
# https://github.com/larashero3-dotcom/lieflat-less-ai-tone ）。
# 相对来源版本的改动：import 改自本库 ai_tone_detect；文档引用改指本技能
# references/ 与仓库 SOURCES.md；报告标题与说明改为本库口径（C级不追求目标值、
# 指纹不反推模型）；修正指标表方向映射（来源版 better 字段中文"低"与 arrow 函数
# 的 "low" 不匹配导致箭头恒为平，结构 CV 类按证据不判方向）；读取编码兼容 BOM。
# diff、指标汇总与语义判读汇总逻辑未改；2026-11-25 重构为一份数据层 + md/html 两个渲染器，
# 以改前改后、有无语义判读四种组合核对输出逐字节不变。
