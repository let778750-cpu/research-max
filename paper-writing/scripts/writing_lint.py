"""writing_lint.py — 写作质量机械自检：节奏（rhythm）、内容守恒（parity）、中文PDF排版（layout）。

边界：只用本地文件，不联网、不调用模型、不改动被检文件。阈值是W9量化参考带的初版实现，
判定分两级——警告=提示人工复查，失败=按规则不得交付；工具通过只代表机械项通过，
不替代科学内容审查。layout模块依赖PyMuPDF（fitz），未安装时报错退出。
节奏类均匀指标按2026-11-15证据重标为只警告不失败（见SOURCES.md成稿去AI味条目）；
成稿去AI味的分级检测与语义判读是另一工具 ai_tone_detect.py（候选报告，非交付闸门），
判据见 references/成稿去AI味检测与语义判据.md。

用法（建议设置 PYTHONUTF8=1）：
  python writing_lint.py rhythm <稿件.md>
  python writing_lint.py parity <原稿.md> <新稿.md>
  python writing_lint.py layout <成品.pdf> --right <版心右缘pt> [--header <页眉首行文本>]

退出码：0=无发现；1=有警告或失败；2=输入、路径或依赖错误。
"""

import json
import re
import sys
from pathlib import Path

# ---- W9量化参考带（初版标定，随使用修正；见 references/论文组织与语言规范.md）----
# 2026-11-15 重标：句长/段长均匀度实测人机无差异（见SOURCES.md成稿去AI味条目），
# 均匀类指标降为可读性警告，不再设失败门；失败级仅保留内容守恒与排版类。
CV_MIN_WARN = 0.30          # 段长变异系数低于此值→警告（正文段≥30段时才判）
BAND_WARN = 0.60            # 单一80字宽度带段落占比超过→警告
SENT_RUN = 5                # 连续N句落同一20字带→警告（提示复查，不逐句必改）
META_PER_1000 = 3.0         # 元话语标记每千字超过→警告
BOLD_COLON_MAX = 2          # 加粗冒号公式句全篇上限→警告
DUNHAO_PARA_GROUPS = 3      # 单段内“四项以上顿号并列”达到→警告
META_WORDS = ["我们讨论得到", "由此形成", "值得注意的是", "需要指出的是", "众所周知",
              "综上所述", "总的来说", "进一步", "本节将讨论", "下面我们来看"]
KINSOKU_START = "，。：；！？、）》」』】〕］”’…"


def _read(path):
    p = Path(path)
    if not p.is_file():
        print(json.dumps({"error": f"文件不存在: {path}"}, ensure_ascii=False))
        sys.exit(2)
    return p.read_text(encoding="utf-8-sig")


def _body_paras(text):
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return [p for p in paras if not p.startswith(("#", "|", "!", ">", "<!--", "["))]


def cmd_rhythm(md_path):
    text = _read(md_path)
    body = _body_paras(text)
    prose_chars = sum(len(re.sub(r"\s", "", p)) for p in body)
    findings = []
    if len(body) >= 30:
        lens = [len(re.sub(r"\s", "", p)) for p in body]
        mean = sum(lens) / len(lens)
        var = sum((x - mean) ** 2 for x in lens) / (len(lens) - 1)
        cv = (var ** 0.5) / mean
        bands = {}
        for l in lens:
            bands[min(l // 80, 4)] = bands.get(min(l // 80, 4), 0) + 1
        top_share = max(bands.values()) / len(lens)
        if cv < CV_MIN_WARN:
            findings.append({"级": "警告", "项": "段长变异系数", "值": round(cv, 2),
                             "说明": "可读性参考（参考带0.30—0.60）；均匀度实测人机无差异，不为节奏制造参差"})
        if top_share > BAND_WARN:
            findings.append({"级": "警告", "项": "单一宽度带段落占比", "值": f"{top_share:.0%}",
                             "说明": "可读性参考，不设失败门"})
    sentences = [s for p in body for s in re.split(r"[。；？！]", p) if s.strip()]
    runs = 0
    cur_band, cur_run = None, 0
    for s in sentences:
        band = len(re.sub(r"\s", "", s)) // 20
        cur_run = cur_run + 1 if band == cur_band else 1
        cur_band = band
        if cur_run >= SENT_RUN:
            runs += 1
            cur_run = 0
    if runs:
        findings.append({"级": "警告", "项": "连续同带句串", "值": runs, "说明": f"连续{SENT_RUN}句字数落同一20字带"})
    meta_hits = {w: text.count(w) for w in META_WORDS if text.count(w)}
    per_k = sum(meta_hits.values()) / max(prose_chars, 1) * 1000
    if per_k > META_PER_1000:
        findings.append({"级": "警告", "项": "元话语密度", "值": f"{per_k:.1f}次/千字", "明细": meta_hits})
    bold_colon = re.findall(r"\*\*[^*：]{2,12}：\*\*", text)
    if len(bold_colon) > BOLD_COLON_MAX:
        findings.append({"级": "警告", "项": "加粗冒号公式句", "值": len(bold_colon), "明细": bold_colon[:5]})
    dh_paras = sum(1 for p in body if len(re.findall(r"([^、\s]{1,12}、){3,}", p)) >= DUNHAO_PARA_GROUPS)
    if dh_paras:
        findings.append({"级": "警告", "项": "顿号长列密集段", "值": dh_paras, "说明": "单段≥3处四项以上并列"})
    return {"命令": "rhythm", "文件": str(md_path), "正文段数": len(body), "正文约字数": prose_chars,
            "发现": findings, "判定": "失败" if any(f["级"] == "失败" for f in findings)
            else ("警告" if findings else "通过")}


def cmd_parity(orig_path, new_path):
    o, n = _read(orig_path), _read(new_path)
    problems = []
    urls = sorted(set(re.findall(r"\((https?://[^)]+)\)", o)))
    missing = [u for u in urls if u not in n]
    if missing:
        problems.append({"级": "失败", "项": "URL缺失", "明细": missing})
    refs = sorted(set(re.findall(r"^\[(\d+)\]", o, re.M)), key=int)
    miss_ref = [f"[{r}]" for r in refs if f"[{r}]" not in n]
    if miss_ref:
        problems.append({"级": "失败", "项": "引文编号缺失", "明细": miss_ref})
    n_compact = re.sub(r"[,\s]", "", n)
    miss_num = sorted({t for t in set(re.findall(r"\d[\d,.]*\d|\d", o)) if t.replace(",", "") not in n_compact})
    if miss_num:
        problems.append({"级": "失败", "项": "数字token缺失", "值": len(miss_num), "明细": miss_num[:20]})
    oq = [re.sub(r"\s", "", q[2:]) for q in o.splitlines() if q.startswith("> ")]
    miss_q = [q for q in oq if q and q not in re.sub(r"\s", "", n)]
    if miss_q:
        problems.append({"级": "失败", "项": "引语未逐字保留", "明细": miss_q[:3]})
    return {"命令": "parity", "原稿": str(orig_path), "新稿": str(new_path), "URL数": len(urls),
            "引文编号数": len(refs), "发现": problems,
            "判定": "失败" if problems else "通过"}


def cmd_layout(pdf_path, right, header=None):
    try:
        import fitz
    except ImportError:
        print(json.dumps({"error": "layout模块需要PyMuPDF：pip install pymupdf"}, ensure_ascii=False))
        sys.exit(2)
    doc = fitz.open(pdf_path)
    bad_start, protrude, unflushed = [], [], []
    for pno, page in enumerate(doc, 1):
        for b in page.get_text("dict")["blocks"]:
            lines = [l for l in b.get("lines", []) if "".join(s["text"] for s in l["spans"]).strip()]
            for i, l in enumerate(lines):
                t = "".join(s["text"] for s in l["spans"]).strip()
                if not t or (header and t.startswith(header)):
                    continue
                if t[0] in KINSOKU_START:
                    bad_start.append({"页": pno, "行首": t[:16]})
                if l["bbox"][2] > right + 1.2:
                    protrude.append({"页": pno, "右缘": round(l["bbox"][2], 1), "行尾": t[-14:]})
                if i < len(lines) - 1 and l["bbox"][2] < right - 2.0:
                    unflushed.append({"页": pno, "距右缘": round(right - l["bbox"][2], 1), "行": t[:14]})
    findings = []
    if bad_start:
        findings.append({"级": "失败", "项": "行首禁则标点", "值": len(bad_start), "明细": bad_start[:6]})
    if protrude:
        findings.append({"级": "失败", "项": "右缘越界", "值": len(protrude), "明细": protrude[:6]})
    if unflushed:
        findings.append({"级": "警告", "项": "段中行未齐右缘", "值": len(unflushed),
                         "说明": "表格单元格按列宽自然结束会造成误报，人工确认后可放行", "明细": unflushed[:6]})
    return {"命令": "layout", "文件": str(pdf_path), "页数": len(doc), "发现": findings,
            "判定": "失败" if any(f["级"] == "失败" for f in findings)
            else ("警告" if findings else "通过")}


def main():
    args = sys.argv[1:]
    try:
        if len(args) >= 2 and args[0] == "rhythm":
            out = cmd_rhythm(args[1])
        elif len(args) >= 3 and args[0] == "parity":
            out = cmd_parity(args[1], args[2])
        elif len(args) >= 2 and args[0] == "layout":
            right = float(args[args.index("--right") + 1]) if "--right" in args else None
            if right is None:
                raise ValueError("layout需要 --right <版心右缘pt>")
            header = args[args.index("--header") + 1] if "--header" in args else None
            out = cmd_layout(args[1], right, header)
        else:
            print(__doc__)
            sys.exit(2)
    except (ValueError, IndexError) as e:
        print(json.dumps({"error": f"参数错误: {e}"}, ensure_ascii=False))
        sys.exit(2)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(1 if out["判定"] != "通过" else 0)


if __name__ == "__main__":
    main()
