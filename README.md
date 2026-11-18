# research-max：科研全流程技能集合

四个自包含技能，供研究者与其 AI 助手在科研各环节按需加载。本仓库为**规则唯一权威源**，完全自包含、不依赖任何外部方法库。分发以整仓为单位。

独立工具：Zotero 中文对照（原 integrations/zotero-bilingual）已独立为公开项目 [transfer-plus](https://github.com/let778750-cpu/transfer-plus)，0.4.x 起以该仓库为唯一权威，本仓库不再维护其源码。

| 技能 | 覆盖 | 入口 |
|---|---|---|
| research-topic | 选题与调研：四步法、问题合同与最近邻反证、近邻命中的处置、深度调研与文献综合 D1—D8、论文精读 P1—P9 | [research-topic/SKILL.md](research-topic/SKILL.md) |
| research-execution | 研究执行：G0—G9 流程关卡、数据准入、Markdown 计划拆分与模块状态、证据反馈、实验层次与冻结、统计分析、归档复用、项目配置与检查工具 | [research-execution/SKILL.md](research-execution/SKILL.md) |
| paper-writing | 论文写作全链路：W1—W10 逐章、M 公式引用、F1—F7 图表版式、F8—F14 科研绘图生产、A 附录、投稿核对与审稿修回 | [paper-writing/SKILL.md](paper-writing/SKILL.md) |
| report-writing | 非论文文体 R1—R5：进展报告、记录、评审意见 | [report-writing/SKILL.md](report-writing/SKILL.md) |

使用方式：按当前任务从对应 SKILL.md 进入；技能内按"规则地图"只读需要的文件。新研究项目可用 research-execution 的项目骨架或 `scripts/research_infra.py init` 起步。维护约定见 [AGENTS.md](AGENTS.md)；各规则的来源、适用边界与反例见 [SOURCES.md](SOURCES.md)。

## 总则：规则三层

1. **科学不可妥协项**：不编造数据、引用、执行、模型身份或评审；结论与证据匹配；负结果可追溯；分母、单位与独立样本量明确；测试信息不进入开发；对照公平；数学与测量假设准确；哈希一致≠内容正确，编译通过≠公式正确。细化条文分布在各技能的"贯穿红线"节，逐项执行以技能原文为准。
2. **用户协作偏好**：领域同行视角、具体自然表达、证据驱动修订；个人化样式条目的记录方式见 paper-writing 偏好表示例，具体项目值写入项目 `submission_profile.json`。
3. **项目可配置项**：十个配置域（研究对象外推、模型与执行团队、费用与重复、引用与字数、字体版式、图件载体、PDF 生成链、引文位置、中西文间距、图中文字）由当前项目决定，未知填 null，不继承任何来源项目取值；判据表见 research-execution 协作与接续的"项目配置域"。

## 迁移说明

本集合于 2026-11-01 由一个中文科研方法库的 v1.8 工作区技能化迁移而来（精读编号 R1—R9 改为 P1—P9 以消除撞号；W/M/F/A、R1—R5、G0—G9 不变）。迁移时的分叉调和、共享物归属裁决与逐轮来源边界的提炼版全部收录在本仓库内（见 SOURCES.md），仓库的使用与维护不需要原方法库。

## 按任务选用的跨 Harness 执行

用户讨论完方案后，可以指定整个实验、阶段或几个模块，由当前Codex主持并让Claude Code执行，模块返回后再审核。任务长、打开项目、存在TASKS或历史上使用过均不自动启动；授权范围内正常修回与推进不逐项确认。

方法与启用边界见[跨Harness任务执行](research-execution/references/跨Harness任务执行.md)，空白片段见[交接模板](research-execution/templates/跨Harness交接.md)，可选运行入口见[Claude Code桥接](integrations/claude-code/README.md)。现有离线任务工具保持不调用模型；桥接的真实run会使用已配置账户的模型额度。

## 按任务选用的GitHub过程记录

用户明确指定任务采用GitHub记录并开始执行后，用一个总览Issue和模块PR展示推进，复用现有Codex审核，通过后自动合并并汇报。几个紧密关联任务可共享PR，任务状态仍只在Markdown维护；未启用项目不增加字段或外部操作。方法与分组边界见[GitHub模块记录](research-execution/references/GitHub模块记录.md)，填写入口见[空白接入模板](research-execution/templates/GitHub记录接入.md)，工具命令与恢复见[GitHub记录组件](integrations/github/README.md)。这项能力独立于Claude Code桥接；本库不自动创建真实实验仓库。
