# turn-report：逐轮任务汇报技能

管 Agent 每轮任务结束交给用户的那段话：先把判断和"能不能用"说清，再给可核查的证据，局限与未做一次交代完；措辞强度跟着证据走，去掉模板腔，篇幅随判断量，缩写首次出现给全称。

| 文件 | 内容 |
|---|---|
| [SKILL.md](SKILL.md) | 入口：规则地图、T1—T7 速览、场景流程、交付闸门、边界 |
| [references/过度防御表述诊断与改写.md](references/过度防御表述诊断与改写.md) | 八类病灶判据、校准五档、前后对照、A/B/C/P 分级、归因 |
| [references/结论优先汇报结构.md](references/结论优先汇报结构.md) | 四段骨架、按任务类型的篇幅参考、禁用结构、样例 |
| [references/缩写与术语首现规范.md](references/缩写与术语首现规范.md) | 首现格式、白名单、待核标记、常见错误 |
| [templates/汇报自检卡.md](templates/汇报自检卡.md) | 空白十项自检 |
| [scripts/reply_lint.py](scripts/reply_lint.py) | 机械自检（R1—R7），本地运行 |
| [scripts/test_reply_lint.py](scripts/test_reply_lint.py) | 自测十二例 |

## 三步用法

1. 写前定结构：按 [结论优先汇报结构](references/结论优先汇报结构.md) 选场景骨架。
2. 写后过卡：[汇报自检卡](templates/汇报自检卡.md) 十项逐项判。
3. 落盘或长稿跑脚本：`python scripts/reply_lint.py --file <草稿>`；退出码 0、1、2 对应通过、警告、失败。

## 测试

```powershell
cd scripts
python -m unittest discover -s . -p "test_*.py" -v
```

## 与另四个技能的分工

- paper-writing：论文成稿的语言与格式，含成稿去 AI 味分级清理。
- report-writing：给导师、课题组、合作者的非论文文档正文。
- research-topic：调研与选题。research-execution：研究流程与证据管理。
- 本技能：每轮对话结束时的汇报本身，不改研究内容，不改文档正文。

## 来源

规则来源、适用边界与反例记在仓库根目录 SOURCES.md 的 `turn-report` 节。
