# SOURCES：各技能规则的来源、适用边界与反例

规则正文以各技能 `references/` 为唯一权威；本文件只记"每类规则从哪里来、适用到哪里、反例是什么"，供修改规则前核对边界。本仓库自包含，不依赖任何外部方法库；完整历史裁定与逐版字节史保存于迁移源仓库的 git 标签（v1.5.0 / v1.8.0），仅作档案，不构成本仓库的使用前提。

## 通用反例清单（任何来源项目的取值都不自动继承）

- 研究场景数量、任务数量、文献/阅读卡/知识块数量：不是通用验收门槛。
- 指定模型、执行团队与并发数、费用授权与重复次数：逐项目配置，不成为通用要求。
- 字数区间、字体、单双栏、图尺寸、页眉页脚、引文位置等版式项：以真实投稿模板为准。
- 图件载体、图中文字风格：用户偏好与任务要求，逐项目选择；"排除生成式结果造假"是通用要求，载体本身不是。
- 图像工具的实际模型身份、字体文件与分辨率：如实记载；低分辨率原图不能继承为"已验收"。
- 旧项目的验收状态、实验数值与存储位置：历史记录，不是新项目的先验。

## 项目 AGENTS 入口与规则分层（2026-11-12）

核对 [AGENTS.md 开放约定](https://agents.md/)与 [Codex 官方加载说明](https://learn.chatgpt.com/docs/agent-configuration/agents-md)：项目入口保留长期原则、路径与任务路由，详细流程按需读取；目录发现不等于任意跨目录聊天都会加载目标项目文件。参考 [HumanLayer 的指令文件经验](https://www.humanlayer.dev/blog/writing-a-good-claude-md)及 [steipete/agent-scripts 的 AGENTS.MD](https://github.com/steipete/agent-scripts/blob/main/AGENTS.MD)中的精简常驻内容、按需查阅项目资料与验证实际结果的做法，不移植其特定工具、提交习惯或授权范围。用户提供的 AGENTS 样例仅作结构参考，文档里的命令不视为当前执行指令。此次按用户确认范围统一两项目原则与路由，保留各自任务状态入口；约 80 行、8 KiB 是本次项目维护目标，不冒称官方限制。

## research-topic：选题与调研

**四步法**：源自一次真实合作中用户提出的调研顺序与随后认可的研究进展报告。适用：宽泛方向细化、阶段性调研与选题汇报；已有具体问题时可跳过无关步骤。反例：只列方法名称、用早期准备索引否定后来完成的实验、把行为标签当更强的目标真值、把全部候选想法写成同等成熟的课题。源报告的场景选择、想法数量、实验数值与设备不作为通用要求。

**按证据动态聚焦**：参考 [Neel Nanda 的 Explore–Understand–Distill](https://forum.effectivealtruism.org/posts/hmBPqApDXvhLzbiFt/how-i-think-about-my-research-process-explore-understand)，采纳探索中优先增加信息、发现值得问的问题，以及新发现可使研究返回探索；参考 [Uri Alon：How to Choose a Good Scientific Problem](https://www.weizmann.ac.il/mcb/alon/sites/mcb.UriAlon/files/uploads/nurturing/howtochoosegoodproblem.pdf)，采纳分别判断研究价值与可行性、允许研究目标随发现改变。两者的个人时间安排不作为固定探索周期。[FunSearch 候选数据库实现](https://github.com/google-deepmind/funsearch/blob/main/implementation/programs_database.py)以多岛和行为分组保留不同程序路径，借鉴其避免过早只保留单一路径的做法；不把程序评分、岛屿数量或重置策略套用于通用选题。结合下述 AI Scientist-v2 的分支探索，将这些经验改写为区分方向与下一项检查、比较实质替代问题、随证据展开或聚焦；目标与评价已明确时可集中优化，不要求持续发散。

**精读 P1—P9**：核查七项学者公开策略（Keshav 三遍阅读、Eisner 边读边写、Mitzenmacher 批判性阅读、Carey 等十条规则、Datasheets、Measuring what Matters、Peyton Jones）后按适用范围吸收——采纳按目的选深度、先提取后判断、同假设下重建而不必全量运行；不按名气或星数排序，个人文件组织方式不成标准。另参考 PaperQA2、Ai2 Scholar QA、K-Dense scientific-agent-skills 三个开源仓库（只读未运行）：采纳证据收集与作答分开、先提取可定位内容再综合、先中性理解再映射主张与证据。边界：相关性评分不是证据强度，元数据测试通过不等于语义支持。去重原则：**允许的重复是填写字段，不是第二套规则**。

**深度调研与文献综合 D1—D8（2026-11-12）**：源自 [academic-research-skills](https://github.com/Imbad0202/academic-research-skills) 的 deep-research 技能（本地只读逐文件核对，未运行其检索管线）——检索式五要素与两轮筛选（deep-research/agents/bibliography_agent.md）、去重与多版本关联（其 Step 4.5）、双轴来源分级与利益冲突警示（references/source_quality_hierarchy.md）、三层引用核验＋红旗清单＋拼盘引用反模式（agents/source_verification_agent.md 及其 SKILL.md 反模式表）、矛盾五步消解与张力清单（agents/synthesis_agent.md）、失败路径（references/failure_paths.md）。采纳：工艺流程化、灰色地带记"未核验"、可调和／不可调和二分、综合矩阵角色标注、覆盖声明。边界与反例：不捆绑联网检索脚本——检索用宿主已有工具执行，结果视为待核数据；不照搬其最少篇数（full 10／quick 5）、同行评审占比、偏斜阈值等数值门槛；API 去重改写为 DOI 或题名＋年份＋作者主键的规则型关联；13 代理管线、检查点轮次与 PASS/REVISE 裁定权不进入本库，终局判断保留给研究者。

**近邻命中的处置（2026-11-12）**：来源为用户指定目标——修正 AI 在调研讨论与头脑风暴中的过度防御性新颖性否定（"已在 XX 出现，应从候选撤下"一类终局判决）。方法参照 academic-research-skills 中 devils_advocate 反证针对具体主张而非笼统质疑（deep-research/agents/devils_advocate_agent.md）与 synthesis 不做无分析矛盾陈述的做法。边界与反例：终局判断与放弃决定保留给研究者；反例双方向——直接判死想法与讨好式放宽差异都须拒绝；不引入其检查点轮次与裁定权。

**全文获取、Markdown 精读与接续成本（2026-11-12；2026-11-18 补强）**：用户明确要求真实溯源、摘要初筛后获取全文、以本地 Markdown 深读，并在全文不可得时尽早提供手动获取信息；首轮在既有 D1—D8、P1—P9、模板及协作与接续中定向补充。2026-11-18 用户重申并升格：依赖全文的精读以全文本地落盘并转换为可用 Markdown 为硬前提，下载受阻时及时暂停该精读线、批次收尾汇总全量缺口清单交用户获取、用户补入并通知后才接续；已同步 D1 获取段、D8 失败路径、SKILL 场景流程与贯穿红线及多智能体基座项目 AGENTS（R5）。反例：静默用摘要顶替全文、逐条零散索要、未等用户通知即自行推进。项目 AGENTS 只保留原则与任务路由，不统一项目状态后端。

**前沿覆盖倾斜（2026-11-18）**：用户要求调研覆盖与阅读投入向最新、前沿的高质量文献倾斜，经典方法取建立原理与成熟基线所需即可，不以旧经典挤占前沿覆盖。与既有“不按新鲜度打分、近五年不能替代质量”护栏兼容：倾斜作用于覆盖与投入分配，质量判断仍以适配性与证据为准。已写入问题与创新论证“最近邻与反证”、SKILL 贯穿红线及多智能体基座项目 AGENTS（R5）。反例：整轮调研只罗列旧经典不触前沿，或以“够新”为由跳过必引的经典出处。

| 来源与核查范围 | 采纳内容 | 不适用边界 |
|---|---|---|
| [PaperQA README](https://github.com/Future-House/paper-qa/blob/main/README.md)，只读检索、证据收集、作答、索引复用与固定调用路径说明；所读 Git blob `af05b404aacd6aa3bc6792fcfb650902fc666c1f` | 复用已有材料与索引；证据收集和综合分开；减少重复处理与无效编排 | 作者对固定调用路径开销的说明不证明本项目能节省多少 token；不安装框架，不采用其评分作为科学质量认证 |
| [ScholarQA 实现](https://github.com/allenai/ai2-scholarqa-lib/blob/main/api/scholarqa/scholar_qa.py)，只读摘录、聚类、迭代综合与来源元数据相关实现；所读 Git blob `0f65304725c9e136055e271ecebb7927c30d2b5b` | 摘录—组织—综合，保留来源定位与条件 | 实现允许摘要进入证据提取，不能把其问答流程或摘录结果当作论文全文精读；不引入模型、代理或预算默认值 |
| [Docling 文档结构](https://docling-project.github.io/docling/concepts/docling_document/)及[项目说明](https://github.com/docling-project/docling/blob/main/README.md)，只读层级、文本、图表与来源信息说明 | Markdown 阅读保留原件对应、结构与来源；转换检查和理解检查分开，关键公式、表格与疑点回查原件 | 文档结构能力不保证每份转换正确，也不证明 Markdown 天然消除幻觉；不绑定转换器、不安装新工具 |

上述为文档与源码核查，未运行相关系统。规则场景走查只检查所查情形的适用性，不是成本或科研效果评测；对话轮次、文件读取量等代理指标不能冒充真实 token 或费用。题录、转换、阅读与接续字段复用既有记录，不建立第二套文献台账。

## research-execution：研究执行

执行域规则主要提炼自真实合作的执行教训：强基线先建立且公平（"方法是否照抄、LLM 有何必要"）、所有方法同分时从逐例预测/实际执行/证据传播/决策改变定位、方案转为绑定产物与复核版本的验收任务、复核输出独立保存防止维护操作污染已验收证据、当前证据可更新而获取与决策历史保留。

**探索与判断（含短循环五问、三层次、四类追问）**：由 [Vuk Rosić 的视频](https://www.youtube.com/watch?v=3ceJEbN2KAs)启发，吸收 [Karpathy 训练经验](https://karpathy.github.io/2019/04/25/recipe/)中的逐步理解与验证、[Neel Nanda 研究指南](https://www.alignmentforum.org/posts/jP9KDyMkchuv6tHwm/how-to-become-a-mechanistic-interpretability-researcher)中的探索/理解/提炼分工，以及 [autoresearch](https://github.com/karpathy/autoresearch/blob/068d93da75aa45f72ba482046f108241aaaf1b8e/program.md)在目标与评价已明确时的固定评价与尝试记录（不直接用其单指标取舍来形成开放研究问题）、[Agent Laboratory](https://github.com/SamuelSchmidgall/AgentLaboratory/blob/d9017d90e329112d2a80b7712f37ee9094d2cd27/README.md)的人机分工、[AI Scientist-v2 配置](https://github.com/SakanaAI/AI-Scientist-v2/blob/96bd51617cfdbb494a9fc283af00fe090edfae48/bfts_config.yaml)的分支探索与阶段预算（在给定研究想法内探索实现；不移植自动评分、并发数或阶段配置）、[PaperQA2](https://github.com/Future-House/paper-qa/blob/b9cb21ff05529567606ebab0714562cc3bbc4d79/README.md)的候选/证据/回答分离。[HKUDS AI-Researcher](https://github.com/HKUDS/AI-Researcher/blob/15d629504b91336616e124631f32a02cd952a68a/README.md)用于核对文献—实现—评价的衔接，保留本仓库原流程。[CRUX 跟进评测](https://cruxevals.com/research-notes/crux-2-follow-up/)中两项研究的实验设计改善后仍被专家拒绝，提示研究执行、贡献判断与论文质量应分别检查。视频中的"五秒实验""十五分钟重选题"不作为通用阈值；AI 自评与多模型相互同意不替代独立验证。

**长程计划拆分与 Markdown 状态载体（2026-11-05）**：用户明确将“断点”解释为可供人和其他模型检查的短期模块任务标签，并选择 Markdown 直接承载计划、任务、状态、验收与接续。撤销“JSON 必须是唯一任务状态源”的通用规定；保留“同一任务状态只维护一次”的约束。旧 JSON 项目兼容，不迁移实际运行项目。

| 来源与核对范围 | 采纳内容 | 边界与反例 |
|---|---|---|
| 用户提供的 RWB 本地文档：AGENTS.md、docs/TASKS.md、STATUS.md、NEXT_VERSION_PLAN.md、ROADMAP.md 与 F5 任务包；源码基准 `b57094675bb22416a3d1cd7dfa9320835df553f4`，NEXT_VERSION_PLAN.md SHA256 `da60ab7e4ef79dc2ae648062f03dbbf741d269a766e1205b7362db514af56719`；只读审阅 | 计划、任务包、当前状态及验收证据分工；Markdown 任务清单持有事项状态；实现、验证、未覆盖范围分开 | 不移植角色体系、目录数量、真实预算与旧验收状态；历史任务不自动重启 |
| 用户提供的 EvoMeta Infra 本地快照：README、CLAUDE.md、task.json、run-automation.sh；脚本 SHA256 `2351aa3f201ebfe37b15d27ccaec328b26a02219f840c4313d6ff66389588353`；未运行其调度器 | 稳定任务、依赖、逐项推进及接续记录 | passes 布尔值不足以表达待核验和受阻；其 count_remaining 将缺文件或读取失败回退为 0，作为“未知不等于完成”的反例；不采用强制开窗、终止进程或无人值守调度 |
| [Anthropic 长程代理实践](https://www.anthropic.com/research/effective-harnesses-for-long-running-agents)（2025-11-26） | 渐进推进、实际验证与跨会话留下清楚工件 | JSON 较少被不当改写是该开发实验观察，不是 Markdown 无法可靠使用的证明；不固定任务数量或强制逐任务提交 |
| [OpenAI ExecPlans](https://developers.openai.com/cookbook/articles/codex_exec_plans)（核对时已标归档）及 [Harness engineering](https://openai.com/index/harness-engineering/) | 可持续更新的 Markdown 计划、可验证里程碑、决策记录与简短导航 | 仅取方法，不沿用旧模型推荐；不把自包含误解为每个文件重复全部上下文 |
| [Superpowers writing-plans](https://github.com/obra/superpowers/blob/main/skills/writing-plans/SKILL.md) 与 [Beads](https://github.com/gastownhall/beads)（2026-11-05读取） | 能独立验收/退回的任务边界；明确依赖、稳定 ID 与可推进任务 | 不引入完整框架、数据库、自动派发、固定时间粒度或每步 TDD 仪式 |
| [AIDE journal](https://github.com/WecoAI/aideml/blob/main/aide/journal.py)（2026-11-05读取） | 计划、尝试谱系、执行结果与评价相互关联 | 指标优化和代码树搜索不替代开放研究的问题选择与科学判断 |
| [MAST](https://arxiv.org/abs/2503.13657v3)、[METR 长任务评测](https://arxiv.org/abs/2503.14499v4)及 [Birgitta Böckeler 的工程经验](https://martinfowler.com/articles/harness-engineering.html) | 验收和任务理解失败应单独检查；事前指引与事后反馈配合；机械检查与模型判断分工 | 这些资料未验证本技能，不能据此声称 Markdown 或本次改动提高科研正确率；不外推固定时限或独立同分布的错误率 |

适用：跨多步或多会话的研究相关任务，包括复现、实现、分析和证据整理。简单工作可在一份 Markdown 中完成；输入已结构化且主要供程序消费的旧项目可以保留 JSON。真正减少冗余的是减少重复状态与无用字段，不保证 Markdown 天然节省 token。规则和工具格式分别在 research-execution 对应 references 单一维护；模板只保留待填内容。验证依据为随附的兼容与 Markdown 正反例、实际命令检查及独立接续应用检查；覆盖结构、引用和证据绑定，不认证科研正确、真实评审独立性或长程效率提升。

**执行中计划调整与验收依据（2026-11-06）**：用户进一步要求计划调整能落实到任务，而非重新生成整套状态账。核对上述 ExecPlans 的动态更新与决策记录做法后，将本库既有“同步下游”细化为按影响更新、稳定ID、拆分承接和局部重验。计划修订标识文档同步，任务要求摘要绑定局部目标、声明的关键输入、依赖、复核方式和验收条件；不把整份计划哈希绑定到所有任务。反例：只改计划未改任务、产物未变但标准已改仍沿用旧回执、重编ID切断证据、把暂缓或替代计为完成。继承旧JSON/无版本Markdown的兼容边界，但显式提示未核验的修订或要求绑定，不自动迁移。机械摘要不认证语义适用性、隐含依赖或实际复核；来源未验证本方案效果。实施以计划错位、旧回执失配、进度无关变更、承接缺失/环与隔离接续演练验证，不外推科研收益。

## paper-writing：论文写作

**W3、W5—W9 表达与论证**：源自一套 SCI 写作经验材料（八组经验、32 项判断，逐项处理：9 项合并、4 项补充、15 项修正适用边界、4 项仅记来源）。修正为不成立为硬规则的：引言固定四段每段五行、摘要固定五句、结论固定三四句、阅读数量门槛、导师对白与个人经历。公开核对过 Nature 摘要示例、Springer Nature 结果与讨论说明、Manchester Academic Phrasebank（只作边界核对，不是合规保证）。

**A1—A7 附录分工**：区分政策（某刊会某阶段要求）、范文观察（某版本怎样安排）与本仓库建议（可迁移判断）三层——从"某论文这样写"推不出"都应这样写"。政策核对 ICML/NeurIPS/Nature 格式与 SI 说明：评审没有阅读补充材料的义务，正文自足原则（A1、A2）由此而来。七篇范文各取一点（评价原理与可执行细节分层、过程概括配实际标注指令、完整案例落实领域测试、关键负结果留正文、新评价体系分层解释、边界算例解释指标含义、多载体共同支撑论证）。教训：引用范文前先核验材料齐全。

**W9 量化参考带与 F7**：来自《SCI论文方法论手册》部分章节（按适用范围移植，板块化润色与五遍编辑法未采纳，避免与 W3—W8 分工重复）、de-ai-taste 中文信号库三类信号（结构节奏、标点排版、内容姿态）、Gopen & Swan 一句（旧信息在前、重点居尾），以及两篇交流报告重写的实测标定。**标定样本仅两篇，全部阈值为初版，随使用修正**；机械判定并入 writing_lint（rhythm/parity/layout）。2026-11-15 按 lieflat-less-ai-tone 配对复测证据重标：句长/段长均匀度实测人机无差异，段长CV与宽度带占比从失败门降为可读性警告（见下条登记），其余阈值不变。

**F8—F14 科研绘图生产（2026-11-12）**：源自 [nature-skills](https://github.com/Yuan1z0825/nature-skills) 的 nature-figure 技能 v2.8.0（Apache-2.0；本地只读摘编改写为中文规则条文，非逐字复制，未运行其脚本）——图形契约要素（references/figure-contract.md）、四原型（static/core/stance.md、references/chart-types.md）、语义色族与无障碍判据（references/design-theory.md）、刊印尺寸与渲染后检查项（references/qa-contract.md）、多面板证据架构（references/multipanel-evidence-architecture.md）、图注统计最小项。mplstyle 示例的键项另参考 [SciencePlots](https://github.com/garrettj403/SciencePlots)（仅样式条目类别，未采纳其具体取值）。边界与反例：Nature 单双栏毫米、字号 pt、面板标号规格与色板 hex 均为期刊语境值，不作通用规则，具体值由项目配置域（字体版式、图件载体）决定、未知填 null；不引入其 AI 生图联网路线（生成式图像诚信沿用本库 F2/F3）、后端排他约束与 Python QA 脚本分发；随附 figure_style.template.mplstyle 为全注释示例。图中文字字形缺失告警经验来自 2026-11-12 实测（默认字体无中文字形，登记含所需字形字体后消除）。

**审稿意见路线图与回复信（2026-11-12）**：源自 [academic-research-skills](https://github.com/Imbad0202/academic-research-skills) 的 revision-coach 思想（审稿意见解析为不可变 Roadmap＋作者逐条裁决）、revision_response_template（回应—行动—变化三段结构）、rebuttal-audit（只审覆盖度不代写、不代审对错）。采纳：条目不可改写、判断变化追加不抹除、每条裁决给依据、覆盖度逐条核对。阶段要求差异核对（初投／修回／录用分治）与发表阶段版本分存参考 nature-skills 的期刊阶段门做法（初投不以生产级排版拒收；录用后补齐），具体要求以目标刊当前指南为准、登记核验日期，Nature 语境值不照搬。意见解读与排序另参考 [Rebuttal-Skill](https://github.com/TobiasLee/Rebuttal-Skill)：采纳其“推断意见背后的核心关切并交作者确认、修回可行性评估、按最可能改变审稿结论排序行动、生成式辅助先核对 venue 政策”；其两段式（先分诊后成稿）与“Direct Answer→Evidence→Revision”结构和本库路线图＋回应—行动—变化同构，不另建第二套。边界与反例：三门盲序复审与检查点轮次机制不采纳（与本库“机械／实质分层、研究者终局裁决”的既定边界一致）；不代作者决定最终提交内容。边界与反例：不引入其多代理分工与裁定权；修订状态与版本账目仍由 research-execution 技能交接与修回模板唯一维护，不建第二套状态账；回复不虚构审稿人让步、不把部分回应写成完全解决。

**统计报告完整性清单（2026-11-12）**：源自 academic-research-skills 的 statistical_reporting_standards.md（academic-paper-reviewer/references）——通用报告清单与分方法最小报告项。改写：APA 具体格式（小数位、符号样式）通用化为"报告什么"判据，格式随目标刊；补机器学习语境（划分、种子或折、曝光登记），与数据准入及 paper-writing 技能 F14 图注最小项同源不同粒度。边界与反例：清单管报告完整性不管结论解读（解读仍归统计推断与外推节）；缺项要么补齐要么写明不适用，不逐项打勾代替核对。

**二期对标增量（2026-11-12，本地克隆逐文件只读核对）**：以下为第一批登记之外的增量吸收，各来源采纳与边界如下。

| 来源 | 采纳 | 边界与反例 |
|---|---|---|
| [deep-research（dzhng）](https://github.com/dzhng/deep-research)（src/deep-research.ts） | 检索式绑定研究目标并逐轮收窄（D1）、学习点蒸馏且必须带来源映射（D2） | 其 learnings 无来源映射、单查询失败静默吞掉、字符串弱去重作为反例登记（D5/D8 不重蹈）；广度减半等数值策略不照搬 |
| [gpt-researcher](https://github.com/assafelovic/gpt-researcher)（skills/writer.py、curator.py） | 无证据即弃权（D8）、snippet 不当全文引用（D5）、检索失败留痕（D8） | 其多代理编排与来源策展管线不进入本库 |
| [storm（stanford-oval）](https://github.com/stanford-oval/storm)（outline_generation.py 等） | 先验大纲用证据修订、章节绑定证据格（D7）、多视角提问分别记录（D1） | persona 代理化实现不采纳，视角以提问维度落地 |
| [paper-qa](https://github.com/future-house/paper-qa)（src/prompts.py） | 逐字引文锚点与位置记录、修订不沿用过期条目（D5） | 其引用键机器校验格式与 CANNOT_ANSWER 哨兵短语机制不随库分发，弃权要求以条文表达 |
| [paper-writing-skill（SNL-UCSB）](https://github.com/SNL-UCSB/paper-writing-skill) | 引言初稿作护栏、证据后重写（W1）；压缩操作记录前后字数、超半数回结构处理（W10）；整合遍历查术语漂移与首句职责（W10） | 其 M1—M18/S1—S31 双门、红队闭合门与 loop 账本不引入——本库以审查单＋交付闸门表达同类要求；闭合门以"关键问题修复复验后交付、不以轮次用尽放行"条文落地 |
| [sciwrite（labarba，Sainani 判据）](https://github.com/labarba/sciwrite) | 谓语埋没、被动三分条件、模糊指示词带名词、名词化还原（W9）；二手统计量回核一手（W7） | 香蕉规则、同义词纪律本库 W9 已有（同义词循环条目），不重复登记；摘要 move 审计以 W8 既有功能清单表达 |
| [Rebuttal-Skill](https://github.com/TobiasLee/Rebuttal-Skill)（补充） | 意见优先级四维（严重度×决策影响×共享度×解决置信）、有依据不执行实验的标注、共享意见合并回应（投稿与修回） | 会议机制（AC 私信、分数-文本不符流程、confidential note）不采纳；重投 R0—R3 积压表属会议语境，期刊转投以可行性评估覆盖 |

以上各仓库均未运行其代码；本库条文为独立改写，不含其原文。

**成稿去AI味对标增量（2026-11-15，本地克隆逐文件只读核对）**：源自 [lieflat-less-ai-tone](https://github.com/larashero3-dotcom/lieflat-less-ai-tone)（**CC BY-NC 4.0**，作者 shiujan；克隆存于本机 `_external` 对标库，未运行其研究复现脚本）。本仓为私有科研自用属非商业范围；两份适配脚本与条文改写在文件头与本条目署名来源并标明改动。**若未来公开分发本仓库，随件保留本署名与许可证声明，NC 条款对被分发部分继续生效。**

| 采纳 | 边界与反例 |
|---|---|
| W9 结构条目证据修正：rule of three 收窄为"高度同构三连"（宽口径排比无区分力）；同义词循环升级为段级同义重命名判据（≥2次/段为重灾段）；二元对比并页翻案腔表述；新增衔接零跳转（≥6连环）；冒号句收窄为"结论提示"子类 | 序数词小标题、"这意味着"复述、空转句引列表、概括替代、精确数字堆砌、漂亮词黑名单、名词化/明喻/设问/模糊量词/首先其次总之、句长段长参差——两轮实测人机无差异或反向，全部进W9"已否决特征"永不清理 |
| W9 句法新增翻译腔四种（过长前置定语约15字/的的连用、当…时从句、前置话题壳、句首连接词当路标）；句长条目改"不制造参差"；模糊指示词条目补"频率不作信号"注记 | 套语替换表保留但判据改为语义精确性（漂亮词频率不显著）；总分总八股保留为文体控制并注明非AI统计信号；显式序列词为文体要求不算AI味 |
| W10 新增成稿清理六条纪律（最小改动、信息守恒、不制造参差、结构不动、风格参考优先、改后自查） | 比喻贴切度/暗喻/拟人化喻体归人审区默认保留，模型不判贴切度；问句、设问、文学性表达、对话体不清理 |
| 新建 references/成稿去AI味检测与语义判据.md：三层分工（脚本/语义/人审）、A/B/C/X/F/H分级（按改动风险不按特征强度）、检测→报告→用户确认→改写→复测流程、语义层四项封闭判据与汇总口径、报告口径（研究显著≠本篇显著、不静默删项、保留需举证、F指纹不反推模型）、学术文体排除 | 通识判例不入库；判断纪律（封闭标签、逐条独立、兜底标签）保留但其43万次打标规模是来源研究事实，不是本库验收依据 |
| 适配脚本 scripts/ai_tone_detect.py（源自其 detect.py）与 scripts/ai_tone_report.py（源自其 report.py）：正则、阈值与人类参考值未改；新增学术文体排除（列表/表格/引用/参考文献/题注/独立公式行不计数，行内公式先剥离）；建议文案改指W9条目 | 商业授权提示段未采纳（源技能商业模式条款，非许可义务，私有科研用途不传导）；examples/ 通识案例未采纳（非学术文体且涉来源项目内容）；compare-human-ai.py、check-structure.py、check-translationese.py 研究复现脚本未采纳（检测能力已含于 detect.py，吸收即冗余） |
| writing_lint.py：段长CV与宽度带占比由失败降为警告（阈值常量同步），docstring 记录分工（lint 管交付闸门，detect 管分级候选报告） | rhythm 其余项（元话语、加粗冒号、顿号、连续同带句）阈值不变，仍为警告级；parity/layout 未动 |
| 新增 templates/成稿去AI味检测报告模板.md（空白待填）；SKILL.md 规则地图、写作流程"成稿去AI味清理"行与贯穿红线补条；report-writing 按名提及 ai_tone_detect.py（沿用 writing_lint 例外登记模式） | 检测报告是改前确认点不是交付闸门；单篇未做显著性检验不得宣称统计显著、不得断言作者是AI——此为来源结论亦为本库红线 |

验证依据：W9 变动条目与已否决清单的两轮实测数据（首轮629篇对照、复测270对同题同事实配对＋43万次语义判断）引自源仓 RESEARCH.md 与 SKILL.md，**本库未复现其研究**；适配脚本已以构造的中文学术正反例（阳性段/X级段/排除项）跑通检测、候选抽取与前后对比报告，并用旧版样张回归 writing_lint 三模块（均匀类指标降为警告后无失败误报）。参考值来自通识中文语料，学术论文语料未重标定，全部标[可调]/初版随使用修正。

## report-writing：非论文报告

R1—R5 与风格契约卡直接提炼自两篇交流报告的重写实战（诊断证据：段长变异系数 0.38→0.45 / 0.20→0.37，单一宽度带段落从 58/80、67/71 集中降为四档分布，行首禁则 4/5 处归零，元话语 26→9 / 42→14 次）。适用：非投稿文体；判断依据是"重写是否丢事实、是否用分析腔元话话替代直接陈述"，不是篇数或字数。

## 修改规则时

先在本文件找到该规则的来源与边界；适用条件变化时同步更新对应条目，不默默放宽。新增经验先给适用范围、反例和验证依据，再进入技能正文。

## 用户指定任务的跨 Harness 执行（2026-11-07）

用户明确选择：科学讨论与方案制定保持正常对话；仅由用户指定的具体任务使用当前Codex主持、Claude Code执行、模块返回后审核的方式。授权范围内连续推进，其他窗口、旧项目及普通任务不自动启用。Markdown仍是任务状态权威；进程事件、派发摘要和回执是尝试证据，不另建任务数据库。

| 来源 | 采纳 | 边界与反例 |
|---|---|---|
| [Claude Code程序化执行](https://code.claude.com/docs/en/headless)，2026-11-07核对文档与本机help | print模式、流式结果、明确会话ID、bare模式隔离自动发现 | CLI退出0不等于业务验收；结果字段与回执还需检查。bare模式所需API凭据与订阅登录不同，不能泛称所有账户可用 |
| [Agent Teams](https://code.claude.com/docs/en/agent-teams#limitations) | 按独立产出选择并行、先串行再验证并行 | 仍有实验性及恢复限制；首版桥接使用显式前台Agent，不默认启用Teams，不声称回复结束后全部子作业必然结束 |
| [Sub-agents](https://code.claude.com/docs/en/sub-agents)、[Settings reference](https://code.claude.com/docs/en/settings-reference)、[Memory](https://code.claude.com/docs/en/memory) | 会话级自定义代理、明确工具范围、独立配置目录与自动加载控制 | 本机bare模式下即使注册代理仍缺少Agent工具；并行改用专属配置且禁用普通自动加载。托管策略仍由CLI执行，不能据此声称绕过组织约束或构成沙箱 |
| [ACP/acpx](https://github.com/openclaw/acpx)、[CCG Workflow](https://github.com/fengshao1227/ccg-workflow) | 会话身份、结构化交接、职责分开 | 保留为扩展参考，不引入新任务系统；CCG默认主控角色与本次不同；acpx自述pre-1.0，不以项目热度认证本机GLM适配 |
| [Codex App Server](https://learn.chatgpt.com/docs/app-server) | 区分会话/轮次/事件/审批及外部运行生命周期 | 用户选择当前会话主持，首版不建立后台主控；不假定可随意唤醒原桌面聊天 |
| 用户提供RWB的HARNESS_INTERFACE_COMPARISON_2026-10-19.md（只读） | 请求接纳、运行结束与业务完成分开，旧版本结果拒绝、未知效果先查询 | 不移植角色体系、存储系统或其全部运行保证 |
| [MAST](https://arxiv.org/abs/2503.13657)、[Agent Laboratory](https://arxiv.org/abs/2501.04227) | 任务定义、协作理解与验证分别处理；保留研究者反馈 | 异构模型并不自动独立，模型一致不认证科学正确；论文没有验证本机组合，不外推固定效率提升 |
| [Windows Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects) | 本次进程树归属、关闭与残留检测 | 不是文件系统沙箱；WMI/远端服务等不属于普通子代保证，首版不支持 |

工具检查覆盖声明的范围、版本、返回结构、文件变动与普通进程树；无法认证用户授权真实性、模型实际身份、科学判断和未声明依赖。显式执行约定与owner字段是协作约束，不是抵御恶意代理的安全边界。实际验证以隔离正反例、真实小任务交接和独立应用检查为准；保留失败修订和未覆盖范围，不把准备成功或模拟通过写成真实模型执行成功。

本机验证发现并修正：输出管道关闭不能证明子进程已结束；项目内占用不足以阻止不同项目共写一个副本；Windows状态读写须处理短暂共享冲突。另拒绝非有限超时、大小写变体的保留目录、损坏交接及不匹配的恢复会话。真实示例完成三数统计的串行交接与两个前台子代理交接；bare代理能力不足的两次返回保留为失败依据。该示例只验证本机接口与产物复核，不证明复杂科研能力、并行加速或长期正确率提升。

### 审核回应、收敛与历史交叉核查（2026-11-07）

用户提出执行者可再检查主持审核中的冗余，随后明确强调增加轮次的效率与稳定性成本。采用一次主审、按影响回验、快速核实合并入已有修回调用；无实质意见直接推进。已完成模块的交叉核查仅覆盖用户指定范围，以独立报告承接，不把原已验收状态改回待做。

| 核对来源 | 采纳 | 不外推的部分 |
|---|---|---|
| [Superpowers receiving-code-review](https://github.com/obra/superpowers/blob/main/skills/receiving-code-review/SKILL.md) | 先核实意见与当前实现是否相符，允许以证据反驳；检查是否引入不需要的功能 | 不照搬所有反馈不清就停下整项工作的规定，也不移植其措辞禁令；独立且明确的工作可继续 |
| [Google code review standard](https://google.github.io/eng-practices/review/reviewer/standard.html) | 技术事实优先，区分必要修正与非强制建议，兼顾质量与推进 | 软件“足够好”不意味着可降低科研证据要求；关键未知仍需解决或限制结论 |
| [Claude Code团队的审核经验](https://claude.dev/blog/solving-code-review-at-anthropic/)（2026-10-15发布，2026-11-07读取） | 验证实际输出、以位置和证据提出问题、校验误报；后续审核聚焦变更，不重复旧发现，避免代理互相驱动无尽修回 | 这是团队自身经验，不证明本机GLM效果；不移植完整多层门禁、投票系统或默认多轮。其轮次限制不是本库统一任务配额 |
| [When and Why Does Multi-Agent Debate Fail and Does It Really Underperform? v2](https://arxiv.org/abs/2510.20963v2) | 竞争或过早共识均可能抑制有效分歧，协议应围绕可核对信息 | 属于特定评测与协议研究；不能推导跨Harness/异构模型必然降低幻觉，更不能拿模型一致替代原文、数据与测试 |

适用：已选择跨Harness的模块修回，或用户明确指定的历史产物复核。反例：每个通过模块再派一轮“确认”、每条建议都变成任务、未经核对就采纳误报、以“已有测试”回避不同边界、因达到轮次上限而放行、历史核查顺带改代码、将负面核查报告验收等同原模块通过。工具本轮未改；新规则以隔离应用演练及现有接口接入检查验证，不将减少轮次直接记成可靠性提升。

### GitHub模块记录与任务归组（2026-11-08）

用户选择以总览加模块PR改善实验过程可见性，明确PR复用既有Codex审核，通过后在指定范围内自动合并。该能力独立于跨Harness；方案认可不自动变成执行或发布授权。任务Markdown继续唯一维护状态，GitHub总览是带来源版本的派生视图。

| 来源与核对范围 | 采纳 | 边界与反例 |
|---|---|---|
| [GitHub Flow](https://docs.github.com/en/get-started/using-github/github-flow)和[Draft PR说明](https://docs.github.com/en/pull-requests/reference/pull-requests)（2026-11-07读取） | 模块开始即建立分支和草稿，持续提交有意义变化，合并后新工作另开分支；PR保存过程 | 不按每个task/随机种子建PR；PR不是任务状态源；不增加人工或模型审核层 |
| [Martin Fowler分支模式](https://martinfowler.com/articles/branching-patterns.html) | 频繁集成、维护可信主线，减少长期分叉 | 不把软件交付时长阈值套给昂贵科研实验；main可包含可信负结果，不等于科学假设获支持 |
| [Superpowers结束开发分支](https://github.com/obra/superpowers/blob/main/skills/finishing-a-development-branch/SKILL.md)及[worktree方法](https://github.com/obra/superpowers/blob/main/skills/using-git-worktrees/SKILL.md)（2026-11-07只读） | 隔离工作、核对实际集成结果 | 不移植整套审批菜单、每轮全量测试或默认嵌套worktree；本库桥接副本必须在权威目录外 |
| [GitHub CLI合并](https://cli.github.com/manual/gh_pr_merge)、[创建PR](https://cli.github.com/manual/gh_pr_create)与本机gh 2.92.0帮助 | 明确仓库/头提交、stdin多行正文、原生合并、查询恢复 | --match-head-commit不原子锁定目标基线；合并后核对父提交和内容。gh pr create --dry-run可能仍推送，不能拿它充当纯只读模拟 |
| [GitHub Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects)、[DVC实验管理](https://doc.dvc.org/user-guide/experiment-management)及[Vibe Kanban停运说明](https://www.vibekanban.com/blog/shutdown)（前轮调研） | 区分展示、实验实例和代码集成；借鉴清楚的工作入口 | 首版不引入看板同步框架、每次实验的普通分支或依赖停运项目的远程服务 |

本库分组判断以共同产出、变更关联、可共享且充分的验收、一起集成/回退是否自然为依据。机械工具仅核对ID、唯一归属及收缩后的依赖图，不能认证任务粒度、科研意义或隐含依赖。反例：把同一阶段全部任务合组、将评分正确性与性能比较混为一次通过、因一个成员完成即标整组通过、最终删除范围外文件却忽略它仍在Git中间历史、将PR关闭或合并响应超时当成完成。

实施验证使用本地bare Git远端、模拟GitHub、原任务/桥接兼容测试和独立应用检查。真实仓库尚未指定，未进行真实GitHub创建、推送或合并；模拟通过不证明所有账户权限、分支保护/合并队列或长期使用效果。检查密钥模式和文件范围只是有限预检，不声称构成操作系统沙箱或完整泄漏检测。

独立应用检查暴露并推动修正两项具体缺陷：CLI执行入口先于渲染函数定义导致部分发布后失败；新main已合入模块后仍按启动基线计算范围，误拒绝已发布的上游文件。分别加入实际脚本入口与真实上游文件集成的回归；当前发布基线与历史启动快照分开，仍检查未进入基线的中间越界提交。另外比较Git blob原字节与本地证据，拒绝换行/clean过滤造成“链接内容与哈希不一致”。这些是软件行为验证，不外推科研正确率提升。

### 交付验证摘要与过程材料清理（2026-11-08）

用户要求测试稳定后清理C盘过程文件。清理前重新逐文件核对：当前69个产品文件与最终测试清单及独立回验候选一致，无产品漂移；未重新调用模型或干预另一窗口正在运行的实验。正式代码、模板、随附回归测试和本摘要保留在技能库，候选副本、合成夹具、备份、临时日志与已完成派发材料不作为另一套产品继续保留。

| 验证范围 | 已观察结果 |
|---|---|
| 最终自动化回归 | 离线任务/Markdown/JSON检查84项、GitHub记录24项、Claude桥接40项，共148项通过；三个进程exit 0，运行期间产品未变 |
| 最终文档 | 技能元数据校验通过；198个本地引用及技能目录边界通过 |
| GitHub独立应用 | 首轮11个场景中9个通过、2个缺陷；修复后的6个针对性测试方法对应场景通过，含真实CLI入口、上游集成、隐藏越界历史、字节绑定及封存复用 |
| 早期Markdown与计划变更 | Markdown作者52项及修订后独立35＋15项通过；计划变更作者78项及修订后独立46＋28＋4项通过。这些是当时版本的历史结果，不能与最终148项简单相加 |
| 早期跨Harness及审核规则 | 桥接最终作者40项及独立20项通过；开发候选曾完成真实串行与两个前台子代理的小型示例。后续审核规则的独立应用通过；没有把候选真实调用外推为最终版本再次付费实测 |

清理时确认的实现SHA256（之后如改动须按影响重验）：

| 实现 | SHA256 |
|---|---|
| research-execution/scripts/research_infra.py | `4a61aeede9de90d0773a0fe9a43451ae91a343da394a94218810e90a3b133398` |
| research-execution/scripts/markdown_tasks.py | `447ccffddd8d583d832bd7e6d403d11e926461df18e0b621e6ed803b6a5a4ef9` |
| research-execution/scripts/module_groups.py | `22a3977e9ba104b0fe13f55ff3a5ecd4b4fc53a99a790584270af8be378965d8` |
| integrations/github/record.py | `2cebb684b55ca17f8fcc339d2001b6ac6c99d3a3c601ffc6a3aef3c98508a087` |
| integrations/claude-code/bridge.py | `0d8a17733b1b47614d2d7d23cf349928b454a2e0a7600ac65d3ea2b72846c231` |
| integrations/claude-code/process_scope.py | `d92913c0430cf874eb2797bb0208e7dfa7ad9c7c6aded08ce02932a0ad0e3cb5` |

历史独立报告与运行细节在清理后不再保留原始文件；本节是经核对的精简结果记录，不冒充完整原始证据。现有软件回归可由随附测试重新运行。真实GitHub仓库仍未指定，尚未做真实创建/推送/合并演练；科学正确性与长期效率不由这些检查认证。

清理执行状态：本次对已核对的C盘过程目录与已完成派发文件发起删除，但自动审批在命令启动前拒绝，仅返回`blocked by policy`，未提供更具体原因。因此本次并未删除这些文件，也未改用其他执行方式绕过拒绝；已准备限定目标、默认只检查的本地清理脚本供用户手动运行。本节保留此未完成状态，不将清理计划写成已经完成。

## turn-report：逐轮汇报

**知识限度免责与结论先行（2026-11-20）**：来源为 [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)（CC BY-SA，WikiProject AI Cleanup 维护；只取模式分类与其对"统计上最可能的表达"这一成因的解释，不逐字复制其文本）、[blader/humanizer](https://github.com/blader/humanizer)（MIT，26 模式；重点采纳 #22 聊天残留、#23 知识限度免责与猜测、#26 重讲读者已知并主张"先给决定"；采纳其"单一弱信号不单独触发、需与另一信号共现"的门控做法）与 Humanizer-zh（MIT，中文词表参考，实施时复核许可证）。适用：逐轮汇报、任务完成说明与变更说明。边界与反例：不采纳其"加人味"目标（其 README 亦自称不试图骗过检测器），本技能只管决策是否清楚；不做作者归属判断；不删限定条件、单位与未做声明；不搬英文专属特征（破折号、弯引号、格式徽章）。

**校准而非去防御（2026-11-20）**：来源为 [Conformal Linguistic Calibration](https://arxiv.org/abs/2502.19110)（事实性与具体性之间存在可调的权衡，说明"说得更具体"与"说得更可能对"不是同一件事）、El Attar 等 2026（[arXiv 2606.04177](https://arxiv.org/abs/2606.04177)，写作特征随模型与文体变化，不宜作身份判据）与 humanizer-pro 自报的误报 0.2%、命中 3.1%（统计型检测不可靠）。采纳：五档强度映射，以及"过防御与过自信是同一错的两端"。适用：一切对外汇报的措辞强度。边界与反例：不以统计特征判定"AI 味"；不要求用户交代生成模型；未知来源文本照常按结构判；有依据的单次"可能"是准确而非防御。

**缩写首现（2026-11-20）**：来源为 [Microsoft Style Guide · Acronyms](https://learn.microsoft.com/en-us/style-guide/acronyms)（全称后接括号缩写、后续直接用、只用在读者熟悉的缩写上、不为产品名造缩写）、[IEEE 802 编辑规则](https://mentor.ieee.org/802.15/dcn/10/15-10-0324-09-0000-wg-editors-instructions.pdf)（全称小写，专名除外）与国家标准 GB/T 7713.1—2006《学位论文编写规则》及高校实施细则（中文缩略词首现注明全称，外文缩略词在译名后用圆括号注明原词全称）。采纳：首现格式、一篇一次、集中登记、单位与代码例外、全称未知标"待核"。适用：汇报、文档与图注中的术语首现。边界与反例：不复制上述文本原文；不把"展开"当义务——能用中文全称就不用缩写；不臆造英文全称；不为凑格式把单位、文件格式或代码标识符展开。

**结论先行的既有实践（2026-11-20）**：Plain Writing Act 2010 与 BLUF（Bottom Line Up Front，结论前置）作为公开先例；ASD-STE100 简化技术英语（ASD 标准，版权归 ASD，仅取"一句一义、主动语态、避免名词堆叠"的思想，不复制规则与受控词表）。内部复用 report-writing 的 R4 直接陈述、paper-writing 的 W9/W10 与成稿去 AI 味检测与语义判据（A/B/C 分级；该文件的 X 级在本技能改称 P 级，避免同名异义）、论文组织与语言规范的"缩写首次给全称、不编造缩写展开词"。边界：文档成稿仍归 W9；本技能不复制其判据，只做逐轮汇报的结构与措辞。

**完成声明需可验（2026-11-20）**：参考 [obra/superpowers](https://github.com/obra/superpowers) 的 verification-before-completion 技能（只读，未运行），采纳"没有运行验证不得声称完成"。边界：不引入其审批菜单、每轮全量测试与嵌套流程；T2 只要求在汇报里标注证据状态，不改变项目既定的验收流程。
