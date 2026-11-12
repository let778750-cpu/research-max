# SOURCES：各技能规则的来源、适用边界与反例

## Zotero 中文对照集成（2026-11-09，独立可选组件）

用户明确要求在现有 Zotero 中实现原文/中文并排阅读，图片可保留原文，公式、上下标和正文变量优先保护。组件入口为 [中文对照工具](integrations/zotero-bilingual/README.md)。它的模型调用例外仅限用户选择的 PDF，不扩展四个技能的离线工具边界。

| 直接来源 | 采纳 | 适用边界与反例 |
|---|---|---|
| Z-Transplit v1.20.0，固定提交见组件 upstream-lock.json | Zotero 双窗格和滚动/缩放同步代码 | 不复用图像重建公式的翻译路径，不接受上游插件自动覆盖 |
| Zotero PDF2zh v4.1.8 | TaskManager 和任务接口约定 | 本机服务另补回环鉴权、取消和交付报告，不声称原插件原样安装 |
| PDFMathTranslate Next 2.10.2 / BabelDOC 0.7.1 | 0.2.x 历史引擎，保留来源与迁移代码；0.3 默认运行包移除 | 旧存档不能跳过新识别清单；保留旧版本用于回退 |
| [飞桨 AI Studio 异步 API](https://ai.baidu.com/ai-doc/AISTUDIO/fml7mozw5)、PaddleOCR 官方 API 模型定义 | 0.3 采用云端布局、图中文字及表格结构识别，本机使用原字形排版 | 仅上传用户所选 PDF；使用单独 DPAPI 令牌；取消保存任务编号，不伪称已取消远端任务；正式接口结构与质量在用户填写密钥后验收 |
| Zotero 本机 10.0.8 源码与官方插件开发文档 | 附件 API、当前阅读器接口、插件清单与配置目录 | 不修改数据库、不把源码塞入应用程序目录；清单 update_url 必需且须 HTTPS，手动发布使用保留域名并关闭自动更新 |
| Windows DPAPI 和 Job Objects | 当前账户凭据加密与任务进程树清理 | 不承诺抵御同账户恶意程序；不读取或改写 Claude Code 的日常配置 |

验证中的具体发现：用户级 Python 包会污染独立环境，运行时使用 `-I`；普通斜体英文不能一概视为公式；复杂数学拆分后仍必须保留不可侵占的原公式区域；表格单元格划分必须完整保留原字符，部分单元格识别不能替代整张表的文本清单。自动检查不等于数学或语义正确。完整验收以组件内记录为准，未完成的安装、真实接口或视觉检查不得写成已通过。

规则正文以各技能 `references/` 为唯一权威；本文件只记"每类规则从哪里来、适用到哪里、反例是什么"，供修改规则前核对边界。本仓库自包含，不依赖任何外部方法库；完整历史裁定与逐版字节史保存于迁移源仓库的 git 标签（v1.5.0 / v1.8.0），仅作档案，不构成本仓库的使用前提。

## 通用反例清单（任何来源项目的取值都不自动继承）

- 研究场景数量、任务数量、文献/阅读卡/知识块数量：不是通用验收门槛。
- 指定模型、执行团队与并发数、费用授权与重复次数：逐项目配置，不成为通用要求。
- 字数区间、字体、单双栏、图尺寸、页眉页脚、引文位置等版式项：以真实投稿模板为准。
- 图件载体、图中文字风格：用户偏好与任务要求，逐项目选择；"排除生成式结果造假"是通用要求，载体本身不是。
- 图像工具的实际模型身份、字体文件与分辨率：如实记载；低分辨率原图不能继承为"已验收"。
- 旧项目的验收状态、实验数值与存储位置：历史记录，不是新项目的先验。

## research-topic：选题与调研

**四步法**：源自一次真实合作中用户提出的调研顺序与随后认可的研究进展报告。适用：宽泛方向细化、阶段性调研与选题汇报；已有具体问题时可跳过无关步骤。反例：只列方法名称、用早期准备索引否定后来完成的实验、把行为标签当更强的目标真值、把全部候选想法写成同等成熟的课题。源报告的场景选择、想法数量、实验数值与设备不作为通用要求。

**按证据动态聚焦**：参考 [Neel Nanda 的 Explore–Understand–Distill](https://forum.effectivealtruism.org/posts/hmBPqApDXvhLzbiFt/how-i-think-about-my-research-process-explore-understand)，采纳探索中优先增加信息、发现值得问的问题，以及新发现可使研究返回探索；参考 [Uri Alon：How to Choose a Good Scientific Problem](https://www.weizmann.ac.il/mcb/alon/sites/mcb.UriAlon/files/uploads/nurturing/howtochoosegoodproblem.pdf)，采纳分别判断研究价值与可行性、允许研究目标随发现改变。两者的个人时间安排不作为固定探索周期。[FunSearch 候选数据库实现](https://github.com/google-deepmind/funsearch/blob/main/implementation/programs_database.py)以多岛和行为分组保留不同程序路径，借鉴其避免过早只保留单一路径的做法；不把程序评分、岛屿数量或重置策略套用于通用选题。结合下述 AI Scientist-v2 的分支探索，将这些经验改写为区分方向与下一项检查、比较实质替代问题、随证据展开或聚焦；目标与评价已明确时可集中优化，不要求持续发散。

**精读 P1—P9**：核查七项学者公开策略（Keshav 三遍阅读、Eisner 边读边写、Mitzenmacher 批判性阅读、Carey 等十条规则、Datasheets、Measuring what Matters、Peyton Jones）后按适用范围吸收——采纳按目的选深度、先提取后判断、同假设下重建而不必全量运行；不按名气或星数排序，个人文件组织方式不成标准。另参考 PaperQA2、Ai2 Scholar QA、K-Dense scientific-agent-skills 三个开源仓库（只读未运行）：采纳证据收集与作答分开、先提取可定位内容再综合、先中性理解再映射主张与证据。边界：相关性评分不是证据强度，元数据测试通过不等于语义支持。去重原则：**允许的重复是填写字段，不是第二套规则**。

**深度调研与文献综合 D1—D8（2026-11-12）**：源自 [academic-research-skills](https://github.com/Imbad0202/academic-research-skills) 的 deep-research 技能（本地只读逐文件核对，未运行其检索管线）——检索式五要素与两轮筛选（deep-research/agents/bibliography_agent.md）、去重与多版本关联（其 Step 4.5）、双轴来源分级与利益冲突警示（references/source_quality_hierarchy.md）、三层引用核验＋红旗清单＋拼盘引用反模式（agents/source_verification_agent.md 及其 SKILL.md 反模式表）、矛盾五步消解与张力清单（agents/synthesis_agent.md）、失败路径（references/failure_paths.md）。采纳：工艺流程化、灰色地带记"未核验"、可调和／不可调和二分、综合矩阵角色标注、覆盖声明。边界与反例：不捆绑联网检索脚本——检索用宿主已有工具执行，结果视为待核数据；不照搬其最少篇数（full 10／quick 5）、同行评审占比、偏斜阈值等数值门槛；API 去重改写为 DOI 或题名＋年份＋作者主键的规则型关联；13 代理管线、检查点轮次与 PASS/REVISE 裁定权不进入本库，终局判断保留给研究者。

**近邻命中的处置（2026-11-12）**：来源为用户指定目标——修正 AI 在调研讨论与头脑风暴中的过度防御性新颖性否定（"已在 XX 出现，应从候选撤下"一类终局判决）。方法参照 academic-research-skills 中 devils_advocate 反证针对具体主张而非笼统质疑（deep-research/agents/devils_advocate_agent.md）与 synthesis 不做无分析矛盾陈述的做法。边界与反例：终局判断与放弃决定保留给研究者；反例双方向——直接判死想法与讨好式放宽差异都须拒绝；不引入其检查点轮次与裁定权。

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

**W9 量化参考带与 F7**：来自《SCI论文方法论手册》部分章节（按适用范围移植，板块化润色与五遍编辑法未采纳，避免与 W3—W8 分工重复）、de-ai-taste 中文信号库三类信号（结构节奏、标点排版、内容姿态）、Gopen & Swan 一句（旧信息在前、重点居尾），以及两篇交流报告重写的实测标定。**标定样本仅两篇，全部阈值为初版，随使用修正**；机械判定并入 writing_lint（rhythm/parity/layout）。

**F8—F14 科研绘图生产（2026-11-12）**：源自 [nature-skills](https://github.com/Yuan1z0825/nature-skills) 的 nature-figure 技能 v2.8.0（Apache-2.0；本地只读摘编改写为中文规则条文，非逐字复制，未运行其脚本）——图形契约要素（references/figure-contract.md）、四原型（static/core/stance.md、references/chart-types.md）、语义色族与无障碍判据（references/design-theory.md）、刊印尺寸与渲染后检查项（references/qa-contract.md）、多面板证据架构（references/multipanel-evidence-architecture.md）、图注统计最小项。mplstyle 示例的键项另参考 [SciencePlots](https://github.com/garrettj403/SciencePlots)（仅样式条目类别，未采纳其具体取值）。边界与反例：Nature 单双栏毫米、字号 pt、面板标号规格与色板 hex 均为期刊语境值，不作通用规则，具体值由项目配置域（字体版式、图件载体）决定、未知填 null；不引入其 AI 生图联网路线（生成式图像诚信沿用本库 F2/F3）、后端排他约束与 Python QA 脚本分发；随附 figure_style.template.mplstyle 为全注释示例。图中文字字形缺失告警经验来自 2026-11-12 实测（默认字体无中文字形，登记含所需字形字体后消除）。

**审稿意见路线图与回复信（2026-11-12）**：源自 [academic-research-skills](https://github.com/Imbad0202/academic-research-skills) 的 revision-coach 思想（审稿意见解析为不可变 Roadmap＋作者逐条裁决）、revision_response_template（回应—行动—变化三段结构）、rebuttal-audit（只审覆盖度不代写、不代审对错）。采纳：条目不可改写、判断变化追加不抹除、每条裁决给依据、覆盖度逐条核对。边界与反例：不引入其多代理分工与裁定权；修订状态与版本账目仍由 research-execution 技能交接与修回模板唯一维护，不建第二套状态账；回复不虚构审稿人让步、不把部分回应写成完全解决。

**统计报告完整性清单（2026-11-12）**：源自 academic-research-skills 的 statistical_reporting_standards.md（academic-paper-reviewer/references）——通用报告清单与分方法最小报告项。改写：APA 具体格式（小数位、符号样式）通用化为"报告什么"判据，格式随目标刊；补机器学习语境（划分、种子或折、曝光登记），与数据准入及 paper-writing 技能 F14 图注最小项同源不同粒度。边界与反例：清单管报告完整性不管结论解读（解读仍归统计推断与外推节）；缺项要么补齐要么写明不适用，不逐项打勾代替核对。

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
