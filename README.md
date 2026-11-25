# research-max：科研全流程技能集合

七个自包含技能，供研究者与其 AI 助手在科研各环节按需加载。本仓库是规则唯一权威源，不依赖外部方法库，以整仓分发。

| 技能 | 解决什么问题 | 入口 |
|---|---|---|
| research-topic | 选题与调研：从未知出发展开或聚焦问题，做最近邻反证、深度检索与文献综合、单篇精读与核验 | [SKILL.md](research-topic/SKILL.md) |
| research-execution | 研究执行：流程关卡、数据准入、计划拆分与模块状态、实验层次与冻结、统计分析、归档复用；含项目初始化与检查工具 | [SKILL.md](research-execution/SKILL.md) |
| paper-writing | 论文写作全链路：逐章写法、公式与引用、表格与图的科学角色、附录、投稿核对、审稿修回、去 AI 味 | [SKILL.md](paper-writing/SKILL.md) |
| figure-craft | 科研图件：数据图（契约、选型、误差与分布、多面板、配色、期刊版式、导出与自检）、领域图型（收敛、Pareto、性能剖面、临界差、甘特、轨迹）、示意图与架构图、LaTeX 字体一致出图；含样式、配方与离线检查工具 | [SKILL.md](figure-craft/SKILL.md) |
| report-writing | 非论文文体：进展报告、工作记录、评审意见 | [SKILL.md](report-writing/SKILL.md) |
| turn-report | 逐轮汇报：先给判断与可用性，结论带证据锚点，边界集中交代，措辞随证据强度，缩写首现给全称；含机械自检 | [SKILL.md](turn-report/SKILL.md) |
| effort-guard | 投入与止损：开工前算成本，先摆可比路线，同一失败两次停手，用信息闸与成本闸决定继续、收缩或停，汇报带成本账 | [SKILL.md](effort-guard/SKILL.md) |

用法：按当前任务进入对应 SKILL.md，再按其“规则地图”只读需要的文件。新研究项目可用 research-execution 的项目骨架或 `scripts/research_infra.py init` 起步。

| 仓库级文件 | 内容 |
|---|---|
| [AGENTS.md](AGENTS.md) | research-max 自身的维护约定（不适用于你的项目） |
| [SOURCES.md](SOURCES.md) | 各规则的来源、适用边界与反例 |
| [CHANGELOG.md](CHANGELOG.md) | 迁移说明、实施验证记录与提交史 |
| [examples/领域示例.md](examples/领域示例.md) | 航空航天与观测调度领域的可选示例，按技能分节；正文规则保持领域中性 |
| [project-agents/](project-agents/AGENTS.md) | 项目侧 AGENTS.md 模板与逐节解读 |

## 项目侧 AGENTS.md：与技能搭配

技能只规定方法，不知道项目状态、数据位置和验收口径。把 [project-agents/AGENTS.md](project-agents/AGENTS.md) 复制到项目根目录、改名为 `AGENTS.md` 并替换占位符，它补齐这三件事，并把“什么任务读哪个技能”写成路由。常驻文件只放原则与路由（建议 80—120 行），方法细则留在技能内。

| 项目 AGENTS 的节 | 负责什么 | 细则来自 |
|---|---|---|
| 项目入口与规则分工 | 读哪几个文件；任务状态唯一入口；代码、文献、案例、归档的位置；沿用哪个状态后端 | 项目自己 |
| research-max 按任务路由 | 什么任务读哪个 SKILL.md，哪些动作不自动授权 | 本仓库各技能 |
| 逐轮汇报 | 每轮交付怎么讲：判断、证据、边界、强度、缩写 | turn-report |
| 投入与止损 | 怎么开工、卡住几次停手、何时收缩或重写、成本账 | effort-guard |
| 独立判断与研究讨论 | 不附和、先机制后创新、近邻命中的处置、范围交代 | research-topic |
| 研究与验收 | 基线与对照、真值与仿真分离、工程自检与科学 Gate 分级 | research-execution |
| 渐进推进、记录与规范维护 | AGENTS、方案（总体计划）、TASKS 分工；证据绑定；目录维护 | research-execution |
| 项目硬边界 | 数据落盘、凭据与隐私、外部动作授权、被测系统与评价器分离 | 项目自己 |

图件、写作与报告的细则不进常驻文件，在路由表中指向 figure-craft、paper-writing、report-writing。占位符替换、路由删减与可配置值的填写见 [project-agents/README.md](project-agents/README.md)。

## 总则：规则三层

1. **科学不可妥协项**：不编造数据、引用、执行、模型身份或评审；结论与证据匹配；负结果可追溯；分母、单位与独立样本量明确；测试信息不进入开发；对照公平；数学与测量假设准确；哈希一致不等于内容正确，编译通过不等于公式正确。细化条文在各技能“贯穿红线”节。
2. **用户协作偏好**：领域同行视角、具体自然表达、证据驱动修订；个人化样式的记录方式见 paper-writing 的偏好表示例，具体项目值写入项目 `submission_profile.json`。
3. **项目可配置项**：十个配置域（研究对象外推、模型与执行团队、费用与重复、引用与字数、字体版式、图件载体、PDF 生成链、引文位置、中西文间距、图中文字）由当前项目决定，未知填 null，不继承任何来源项目取值；判据表见 research-execution 协作与接续的“项目配置域”。

## 可选执行组件（仅在用户指定具体任务时启用）

| 组件 | 一句话 | 规则 | 命令与恢复 |
|---|---|---|---|
| 跨 Harness 执行 | 主持会话把指定模块派给另一 Harness 执行，返回后审核 | [跨Harness任务执行](research-execution/references/跨Harness任务执行.md) | [Claude Code 桥接](integrations/claude-code/README.md) |
| GitHub 过程记录 | 用一个总览 Issue 与模块 PR 展示推进，任务状态仍只在 Markdown | [GitHub模块记录](research-execution/references/GitHub模块记录.md) | [GitHub 记录组件](integrations/github/README.md) |

两者相互独立；离线任务工具不调用模型，桥接的真实 run 会使用已配置账户的模型额度。Zotero 中文对照组件已独立为公开项目 [transfer-plus](https://github.com/let778750-cpu/transfer-plus)。
