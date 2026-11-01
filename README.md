# research-max：科研全流程技能集合

四个自包含技能，供研究者与其 AI 助手在科研各环节按需加载。本仓库为**规则唯一权威源**，源自"通用投稿的一些规范技巧"方法库 v1.8 工作区的技能化迁移（源库 v1.9 轮）。分发以整仓为单位。

| 技能 | 覆盖 | 入口 |
|---|---|---|
| research-topic | 选题与调研：四步法、问题合同与最近邻反证、论文精读 P1—P9 | [research-topic/SKILL.md](research-topic/SKILL.md) |
| research-execution | 研究执行：G0—G9 流程关卡、数据准入、任务推进与证据反馈、实验层次与冻结、统计分析、归档复用、检查工具 | [research-execution/SKILL.md](research-execution/SKILL.md) |
| paper-writing | 论文写作全链路：W1—W10 逐章、M 公式引用、F 图表版式、A 附录、投稿核对与审稿修回 | [paper-writing/SKILL.md](paper-writing/SKILL.md) |
| report-writing | 非论文文体 R1—R5：进展报告、记录、评审意见 | [report-writing/SKILL.md](report-writing/SKILL.md) |

使用方式：按当前任务从对应 SKILL.md 进入；技能内按"规则地图"只读需要的文件。新研究项目可用 research-execution 的项目骨架或 `scripts/research_infra.py init` 起步。维护约定见 [AGENTS.md](AGENTS.md)。

## 迁移说明（源自方法库 v1.9 轮，2026-11-01）

- **拆分**：方法库 01—08 域规则、09 模板与 10 工具按下表归入四技能；库内对应文件改为导航指针页，演进史保留在源库 90 目录。
- **paper-writing 调和**：迁入时与源库 06/07 逐文件 diff，按三类裁定合入（链接改指取技能版；自包含改写逐句核实无实质修订；删节三处——原图规则节迁 research-topic、归档节迁 research-execution、库外路径句删除）。逐条裁定记录见源库 `90_来源与演进/维护与变更.md` 1.9 节，可 `git diff v1.8.0` 重放。
- **编号变更**：论文精读 R1—R9 → **P1—P9**（消除与非论文报告 R1—R5 撞号）；W/M/F/A、R1—R5、G0—G9 不变。
- **共享物唯一权威**：主张与证据表、交接与修回模板、submission_profile.json、项目骨架、research_infra.py → research-execution；writing_lint.py、范文学习卡、审查单、正文与附录规划 → paper-writing；风格契约卡 → report-writing。消费方按名提及，不复制副本。
- **自包含口径**：每技能规则完备、无断链；"自包含"不等于"资产完备"——按名引用的共享模板与脚本不随单技能目录分发（report-writing 的机械自检即属此类，见 AGENTS.md 例外登记）。
