# research-max：科研全流程技能集合

四个自包含技能，供研究者与其 AI 助手在科研各环节按需加载。本仓库为**规则唯一权威源**，完全自包含、不依赖任何外部方法库。分发以整仓为单位。

| 技能 | 覆盖 | 入口 |
|---|---|---|
| research-topic | 选题与调研：四步法、问题合同与最近邻反证、论文精读 P1—P9 | [research-topic/SKILL.md](research-topic/SKILL.md) |
| research-execution | 研究执行：G0—G9 流程关卡、数据准入、任务推进与证据反馈、实验层次与冻结、统计分析、归档复用、项目配置与检查工具 | [research-execution/SKILL.md](research-execution/SKILL.md) |
| paper-writing | 论文写作全链路：W1—W10 逐章、M 公式引用、F 图表版式、A 附录、投稿核对与审稿修回 | [paper-writing/SKILL.md](paper-writing/SKILL.md) |
| report-writing | 非论文文体 R1—R5：进展报告、记录、评审意见 | [report-writing/SKILL.md](report-writing/SKILL.md) |

使用方式：按当前任务从对应 SKILL.md 进入；技能内按"规则地图"只读需要的文件。新研究项目可用 research-execution 的项目骨架或 `scripts/research_infra.py init` 起步。维护约定见 [AGENTS.md](AGENTS.md)；各规则的来源、适用边界与反例见 [SOURCES.md](SOURCES.md)。

## 总则：规则三层

1. **科学不可妥协项**：不编造数据、引用、执行、模型身份或评审；结论与证据匹配；负结果可追溯；分母、单位与独立样本量明确；测试信息不进入开发；对照公平；数学与测量假设准确；哈希一致≠内容正确，编译通过≠公式正确。细化条文分布在各技能的"贯穿红线"节，逐项执行以技能原文为准。
2. **用户协作偏好**：领域同行视角、具体自然表达、证据驱动修订；个人化样式条目的记录方式见 paper-writing 偏好表示例，具体项目值写入项目 `submission_profile.json`。
3. **项目可配置项**：十个配置域（研究对象外推、模型与执行团队、费用与重复、引用与字数、字体版式、图件载体、PDF 生成链、引文位置、中西文间距、图中文字）由当前项目决定，未知填 null，不继承任何来源项目取值；判据表见 research-execution 协作与接续的"项目配置域"。

## 迁移说明

本集合于 2026-11-01 由一个中文科研方法库的 v1.8 工作区技能化迁移而来（精读编号 R1—R9 改为 P1—P9 以消除撞号；W/M/F/A、R1—R5、G0—G9 不变）。迁移时的分叉调和、共享物归属裁决与逐轮来源边界的提炼版全部收录在本仓库内（见 SOURCES.md），仓库的使用与维护不需要原方法库。
