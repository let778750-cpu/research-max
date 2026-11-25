# SOURCES：各技能规则的来源、适用边界与反例

规则正文以各技能 `references/` 为唯一权威；本文件只记“每类规则从哪里来、采纳了什么、适用到哪里、反例是什么”，修改规则前先核对。过程史（迁移、实施验证、测试计数、哈希快照）不在本文件，见 [CHANGELOG.md](CHANGELOG.md)。

## 修改规则时

先在本文件找到该规则的来源与边界；适用条件变化时同步更新对应条目，不默默放宽。新增经验先给适用范围、反例和验证依据，再进入技能正文。

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

**全文获取、Markdown 精读与接续成本（2026-11-12；2026-11-18 补强）**：用户明确要求真实溯源、摘要初筛后获取全文、以本地 Markdown 深读，并在全文不可得时尽早提供手动获取信息；首轮在既有 D1—D8、P1—P9、模板及协作与接续中定向补充。2026-11-18 用户重申并升格：依赖全文的精读以全文本地落盘并转换为可用 Markdown 为硬前提，下载受阻时及时暂停该精读线、批次收尾汇总全量缺口清单交用户获取、用户补入并通知后才接续；已同步 D1 获取段、D8 失败路径、SKILL 场景流程与贯穿红线及多智能体基座项目 AGENTS（R5）。反例：静默用摘要顶替全文、逐条零散索要、未等用户通知即自行推进。项目 AGENTS 只保留原则与任务路由，不统一项目状态后端。

**本地文献库入库与转换核对（2026-11-25）**：用户要求所有 Harness 在文献分析前把检索到的文献全文下载进项目文献库、合理命名分类并转 Markdown 后再深读，取不到的及时汇总交用户手动下载。核查依据：[Pitkin 等，JAMA 1999;281:1110](https://pubmed.ncbi.nlm.nih.gov/10188662/)（摘要与正文数据不一致或正文缺失 18%—68%）；Walters 与 Wilder，Sci Rep 2023;13:14045（GPT-3.5／GPT-4 生成引文虚构 55%／18%）；[Cochrane Handbook v6.3 §4.6.3 与 MECIR](https://www.cochrane.org/authors/handbooks-and-manuals/handbook/archive/v6.3)（题名摘要初筛、可能相关者取全文、同一研究多报告关联、取不到者标待分类，纳入以全文为准）；PRISMA 2020（Page 等，BMJ 2021;372:n71，流程图分列"寻求获取"与"未获取"报告）；转换器对比 [olmOCR-bench 运行记录](https://github.com/yolow92/pagesift/blob/6aebf81523233b6ccc402546f0669ca1719d11d9/benchmarks/pdf/results-2026-10-22.md)与 [DEV 五工具对比](https://dev.to/jeromebuilds/i-benchmarked-5-open-source-pdf-to-markdown-tools-for-rag-on-real-documents-2026-4heh)（轻量转换器公式与阅读顺序弱，强转换器表格公式好但会丢脚注）。采纳：摘要只作初筛、进入分析或引用者先入库、版本关联不重复、转换器按文献类型选择并回查原件、缺口按批汇总。边界：只走合法来源；不绑定具体转换器；两份对比为第三方单次评测，只作"轻量转换器不可单独信任公式"的依据，不作排名。已写入 D1 获取段与 project-agents 模板项目硬边界。

**深读八问与断点暂停（2026-11-25）**：用户要求深入分析一律读本地 Markdown，重点理解科学问题、理论、实验方法、创新点、结果、结论、不足与讨论；取不到的文献统计后告知用户，协同分析停在断点，补入后再转换深读。核查并吸收：[Raff 的阅读步骤](https://psy311.wichita.edu/wp-content/uploads/2020/07/Raff_LSE_2016.pdf)（大问题与具体问题分开、先记结果再解释、先形成自己的解释再读讨论、最后对照摘要、查看同行评价）；[DARPA Heilmeier 问题集](https://www.darpa.mil/about/heilmeier-catechism)（现有做法的局限、新在哪里、为何能成）；NeurIPS 论文核对单（如 [2024 年论文所附核对单](https://papers.nips.cc/paper_files/paper/2024/file/b444ad72520a5f5c467343be88e352ed-Paper-Conference.pdf)：主张与贡献相符、局限、理论假设与证明、误差来源、算力）与 [2026 评审准则](https://nips.cc/Conferences/2026/ReviewerGuidelines)（原创性不限于新方法，含新认识与组合）；[Lipton 与 Steinhardt，arXiv:1807.03341](https://arxiv.org/abs/1807.03341)（区分解释与推测、指明经验增益来源、警惕装饰性数学）；李沐三遍读法（[mli/paper-reading](https://github.com/mli/paper-reading) 视频系列，本次经二手整理核对要点，未逐段核原视频：第三遍设想自己怎样做、能否做得更好）。采纳：用户八项作为交付骨架，按上述来源细化为 P2 深读八问；模板第6、7节升为核心节；D8 改为协同分析停在断点并写明断点。边界：八问是交付结构不是阅读顺序；理论、综述、定性论文按 P5 改问法，不虚构实验；这些来源是收敛的经验做法，未证明能提升理解，不作评分量表；NeurIPS 条目面向机器学习投稿，借其问法不借其合规要求。第三方 mli-paper-reading 技能（无可核许可证）只参考其主张—证据—强度账本与隐含假设、缺失对照两项批判问题，不采用其写入用户主目录与加载 CDN 的 HTML 笔记流程。

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
| 用户提供的 RWB 本地文档：AGENTS.md、docs/TASKS.md、STATUS.md、NEXT_VERSION_PLAN.md、ROADMAP.md 与 F5 任务包；只读审阅 | 计划、任务包、当前状态及验收证据分工；Markdown 任务清单持有事项状态；实现、验证、未覆盖范围分开 | 不移植角色体系、目录数量、真实预算与旧验收状态；历史任务不自动重启 |
| 用户提供的 EvoMeta Infra 本地快照：README、CLAUDE.md、task.json、run-automation.sh；未运行其调度器 | 稳定任务、依赖、逐项推进及接续记录 | passes 布尔值不足以表达待核验和受阻；其 count_remaining 将缺文件或读取失败回退为 0，作为“未知不等于完成”的反例；不采用强制开窗、终止进程或无人值守调度 |
| [Anthropic 长程代理实践](https://www.anthropic.com/research/effective-harnesses-for-long-running-agents)（2025-11-26） | 渐进推进、实际验证与跨会话留下清楚工件 | JSON 较少被不当改写是该开发实验观察，不是 Markdown 无法可靠使用的证明；不固定任务数量或强制逐任务提交 |
| [OpenAI ExecPlans](https://developers.openai.com/cookbook/articles/codex_exec_plans)（核对时已标归档）及 [Harness engineering](https://openai.com/index/harness-engineering/) | 可持续更新的 Markdown 计划、可验证里程碑、决策记录与简短导航 | 仅取方法，不沿用旧模型推荐；不把自包含误解为每个文件重复全部上下文 |
| [Superpowers writing-plans](https://github.com/obra/superpowers/blob/main/skills/writing-plans/SKILL.md) 与 [Beads](https://github.com/gastownhall/beads)（2026-11-05读取） | 能独立验收/退回的任务边界；明确依赖、稳定 ID 与可推进任务 | 不引入完整框架、数据库、自动派发、固定时间粒度或每步 TDD 仪式 |
| [AIDE journal](https://github.com/WecoAI/aideml/blob/main/aide/journal.py)（2026-11-05读取） | 计划、尝试谱系、执行结果与评价相互关联 | 指标优化和代码树搜索不替代开放研究的问题选择与科学判断 |
| [MAST](https://arxiv.org/abs/2503.13657v3)、[METR 长任务评测](https://arxiv.org/abs/2503.14499v4)及 [Birgitta Böckeler 的工程经验](https://martinfowler.com/articles/harness-engineering.html) | 验收和任务理解失败应单独检查；事前指引与事后反馈配合；机械检查与模型判断分工 | 这些资料未验证本技能，不能据此声称 Markdown 或本次改动提高科研正确率；不外推固定时限或独立同分布的错误率 |

适用：跨多步或多会话的研究相关任务，包括复现、实现、分析和证据整理。简单工作可在一份 Markdown 中完成；输入已结构化且主要供程序消费的旧项目可以保留 JSON。真正减少冗余的是减少重复状态与无用字段，不保证 Markdown 天然节省 token。规则和工具格式分别在 research-execution 对应 references 单一维护；模板只保留待填内容。验证依据为随附的兼容与 Markdown 正反例、实际命令检查及独立接续应用检查；覆盖结构、引用和证据绑定，不认证科研正确、真实评审独立性或长程效率提升。

**执行中计划调整与验收依据（2026-11-06）**：用户进一步要求计划调整能落实到任务，而非重新生成整套状态账。核对上述 ExecPlans 的动态更新与决策记录做法后，将本库既有“同步下游”细化为按影响更新、稳定ID、拆分承接和局部重验。计划修订标识文档同步，任务要求摘要绑定局部目标、声明的关键输入、依赖、复核方式和验收条件；不把整份计划哈希绑定到所有任务。反例：只改计划未改任务、产物未变但标准已改仍沿用旧回执、重编ID切断证据、把暂缓或替代计为完成。继承旧JSON/无版本Markdown的兼容边界，但显式提示未核验的修订或要求绑定，不自动迁移。机械摘要不认证语义适用性、隐含依赖或实际复核；来源未验证本方案效果。实施以计划错位、旧回执失配、进度无关变更、承接缺失/环与隔离接续演练验证，不外推科研收益。

**设计源与任务源二分（2026-11-25）**：用户质疑项目约定的“方案、PLAN、TASKS”三件是否冗余、方案拆成任务后是否还需保留，参照对象为 EvoMeta Infra 的 task.json。核查：EvoMeta 本地快照在任务表之外另有题目、界面参考材料与长篇 README 作需求说明；[Anthropic 长程代理实践](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) 的特性清单由输入规格展开，规格本身不被替代；[GitHub spec-kit](https://github.com/github/spec-kit/blob/main/spec-driven.md) 分 spec、plan、tasks 三层，任务由计划派生、规格是持续维护的真相源；[Kiro 规格](https://kiro.dev/docs/specs/) 为 requirements、design、tasks 三件，tasks.md 即实施计划并按依赖分波执行，任务回链需求编号；[Nygard 架构决策记录（2011）](https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions) 指出决策动机最难追踪，缺少理由只能盲从或盲改；SPIRIT 2013 要求方案修订注明日期，方案作为原始意图记录可与最终报告对照以发现选择性报告（[Chan 等，Ann Intern Med 2013](https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC5114123&blobtype=pdf)）。反面：[Böckeler 对 Kiro、spec-kit、Tessl 的评测](https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html) 指出多份 Markdown 相互重复、审阅负担重、小问题套大流程。采纳：总体计划（方案）为唯一设计源，TASKS 为唯一状态源并以依赖表达先后，不另建只列步骤的第三份计划，README 只导航。边界：两份是默认不是下限，小任务可合为一份；不采用 passes 布尔值（理由见 2026-11-05 条）；上述来源多为软件开发经验，未证明能提高科研正确率。

### 用户指定任务的跨 Harness 执行（2026-11-07）

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

## paper-writing：论文写作

**W3、W5—W9 表达与论证**：源自一套 SCI 写作经验材料（八组经验、32 项判断，逐项处理：9 项合并、4 项补充、15 项修正适用边界、4 项仅记来源）。修正为不成立为硬规则的：引言固定四段每段五行、摘要固定五句、结论固定三四句、阅读数量门槛、导师对白与个人经历。公开核对过 Nature 摘要示例、Springer Nature 结果与讨论说明、Manchester Academic Phrasebank（只作边界核对，不是合规保证）。

**A1—A7 附录分工**：区分政策（某刊会某阶段要求）、范文观察（某版本怎样安排）与本仓库建议（可迁移判断）三层——从"某论文这样写"推不出"都应这样写"。政策核对 ICML/NeurIPS/Nature 格式与 SI 说明：评审没有阅读补充材料的义务，正文自足原则（A1、A2）由此而来。七篇范文各取一点（评价原理与可执行细节分层、过程概括配实际标注指令、完整案例落实领域测试、关键负结果留正文、新评价体系分层解释、边界算例解释指标含义、多载体共同支撑论证）。教训：引用范文前先核验材料齐全。

**W9 量化参考带与 F7**：来自《SCI论文方法论手册》部分章节（按适用范围移植，板块化润色与五遍编辑法未采纳，避免与 W3—W8 分工重复）、de-ai-taste 中文信号库三类信号（结构节奏、标点排版、内容姿态）、Gopen & Swan 一句（旧信息在前、重点居尾），以及两篇交流报告重写的实测标定。**标定样本仅两篇，全部阈值为初版，随使用修正**；机械判定并入 writing_lint（rhythm/parity/layout）。2026-11-15 按 lieflat-less-ai-tone 配对复测证据重标：句长/段长均匀度实测人机无差异，段长CV与宽度带占比从失败门降为可读性警告（见下条登记），其余阈值不变。

**审稿意见路线图与回复信（2026-11-12）**：源自 [academic-research-skills](https://github.com/Imbad0202/academic-research-skills) 的 revision-coach 思想（审稿意见解析为不可变 Roadmap＋作者逐条裁决）、revision_response_template（回应—行动—变化三段结构）、rebuttal-audit（只审覆盖度不代写、不代审对错）。采纳：条目不可改写、判断变化追加不抹除、每条裁决给依据、覆盖度逐条核对。阶段要求差异核对（初投／修回／录用分治）与发表阶段版本分存参考 nature-skills 的期刊阶段门做法（初投不以生产级排版拒收；录用后补齐），具体要求以目标刊当前指南为准、登记核验日期，Nature 语境值不照搬。意见解读与排序另参考 [Rebuttal-Skill](https://github.com/TobiasLee/Rebuttal-Skill)：采纳其“推断意见背后的核心关切并交作者确认、修回可行性评估、按最可能改变审稿结论排序行动、生成式辅助先核对 venue 政策”；其两段式（先分诊后成稿）与“Direct Answer→Evidence→Revision”结构和本库路线图＋回应—行动—变化同构，不另建第二套。边界与反例：三门盲序复审与检查点轮次机制不采纳（与本库“机械／实质分层、研究者终局裁决”的既定边界一致）；不代作者决定最终提交内容。边界与反例：不引入其多代理分工与裁定权；修订状态与版本账目仍由 research-execution 技能交接与修回模板唯一维护，不建第二套状态账；回复不虚构审稿人让步、不把部分回应写成完全解决。

**统计报告完整性清单（2026-11-12）**：源自 academic-research-skills 的 statistical_reporting_standards.md（academic-paper-reviewer/references）——通用报告清单与分方法最小报告项。改写：APA 具体格式（小数位、符号样式）通用化为"报告什么"判据，格式随目标刊；补机器学习语境（划分、种子或折、曝光登记），与数据准入及 figure-craft 技能 FIG11 图注最小项同源不同粒度。边界与反例：清单管报告完整性不管结论解读（解读仍归统计推断与外推节）；缺项要么补齐要么写明不适用，不逐项打勾代替核对。

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

**成稿去AI味对标增量（2026-11-15，本地克隆逐文件只读核对）**：源自 [lieflat-less-ai-tone](https://github.com/larashero3-dotcom/lieflat-less-ai-tone)（**CC BY-NC 4.0**，作者 shiujan；未运行其研究复现脚本）。本仓为私有科研自用属非商业范围；两份适配脚本与条文改写在文件头与本条目署名来源并标明改动。**若未来公开分发本仓库，随件保留本署名与许可证声明，NC 条款对被分发部分继续生效。**

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

## figure-craft：科研图件

**nature-figure 摘编**：契约、语义色族、刊印与渲染检查、多面板架构、图注最小项来自 nature-figure v2.8.0（Apache-2.0，本地只读摘编，未运行其脚本）；原"四原型"只保留排布骨架（定量网格、图像加定量、非对称混合），示意图与架构图不在本技能范围。迁移保留原边界：期刊毫米、字号与色板 hex 不作通用规则，未知填 null；AI 生图路线、后端排他约束与脚本分发不引入。

**多面板与导出要点（nature-figure，2026-11-21 复核）**：[Yuan1z0825/nature-skills](https://github.com/Yuan1z0825/nature-skills) 的技能索引与 README（只读，未读其内部全部文件）。采纳：三级面板层级（总览→偏离→关系）、最终尺寸出图、SVG 保留文本节点的 rcParams 思路、渲染后文字与图形碰撞审计的存在性。改写为 FIG7、FIG10。边界与反例：不把其模板当默认，不引入其 AI 生图与脚本分发。

**先剖面后选图（scipilot，MIT）**：[Haojae/scipilot-figure-skill](https://github.com/Haojae/scipilot-figure-skill)（只读仓库 README，未运行其脚本）。采纳：数据剖析先于绘图、按数据形态与论证目标选图、主动拦截常见错误（n<10 均值柱、双 Y 轴、饼图与 3D、彩虹色、一图多论点、缺字、标号错位）、出图后"程序＋读图"自检闭环、按最终尺寸出图。改写为 FIG2、FIG3、FIG5、FIG7—FIG11 与反模式清单。边界与反例：不把其九类配方当规则，不采用 plotly 交互路线与依赖栈；其"读图"只能补充视觉审读，不能替代文本提取与尺寸实测。

**期刊图件规格（Nature 作者指南，2026-11-21 读取）**：[Final submission](https://www.nature.com/nature/for-authors/final-submission)。采纳：单栏 89 mm、一栏半 120—136 mm、双栏 183 mm、页深 247 mm；正文最大 7 pt、最小 5 pt、面板标号 8 pt 粗体；线宽 0.25—1 pt；照片 300—600 dpi；不转曲、不栅格化文字；RGB。用于 FIG9、FIG10 的典型值表。边界与反例：这是 Nature 单刊的现行要求，不是通用规则；投稿前必须核对目标刊当期指南与项目 submission_profile.json。

**误差条规则（Cumming、Fidler、Vaux，J Cell Biol 2007）**：[Error bars in experimental biology](https://rupress.org/jcb/article-abstract/177/1/7/34602/Error-bars-in-experimental-biology)。采纳其方向：误差条必须说明表示什么、给出 n、只用于独立重复、区分 SD 与 SEM／CI、图上比较不能只看重叠。改写为 FIG4 的四问与常见误用。边界与反例：原文面向实验生物学，未复制其数值判据；本库按统计协议与目标领域调整，不把"区间重叠"简化成显著性判据。

**小样本展示个体（Weissgerber 等，PLoS Biol 2015）**：[Beyond Bar and Line Graphs](https://journals.plos.org/plosbiology/article?id=10.1371%2Fjournal.pbio.1002128)。系统综述显示顶刊生理学论文多用均值柱与折线，掩盖分布与个体。采纳为 FIG5 的"小样本显示个体点、均值柱不作唯一表达"。边界与反例：不设"所有图必须点图"的硬规则；大样本且分布已知时汇总图仍可用，但须同时给区间。

**十条绘图规则（Rougier、Droettboom、Bourne，PLoS Comput Biol 2014）**：[Ten Simple Rules for Better Figures](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1003833)。采纳：先明确读者与主张、不用默认设置、不堆装饰、坐标轴标注、颜色有意义、字号可读、避免不必要的三维。改写为 FIG1、FIG8、FIG9 与反模式。边界与反例：其"不要用默认设置"不等于堆样式；规则不提供具体阈值。

**顺序可靠性与 HOPs（Hullman 等，PLoS ONE 2015）**：[Hypothetical Outcome Plots Outperform Error Bars and Violin Plots](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0142444)。采纳为 FIG4 的可选增强：判断顺序可靠性时可用分帧或动态表达，静态图仍须给区间。边界与反例：该结论来自特定读者实验，不构成一切场景都该用动画；投稿静态版式仍以静态图为准。

**色图误用（Crameri 等，Nat Commun 2020）**：[Scientific colour maps](https://www.fabiocrameri.ch/colourmaps/) 与 The misuse of colour in science communication（DOI 10.1038/s41467-020-19160-7）。采纳：感知均匀、色盲友好、灰度可读、避免彩虹与 jet。改写为 FIG8 与反模式第 5 条。边界与反例：具体色值由项目登记，不把某一套色图设成唯一正确；定性配色的语义色族优先于色图选择。

## report-writing：非论文报告

R1—R5 与风格契约卡直接提炼自两篇交流报告的重写实战（诊断证据：段长变异系数 0.38→0.45 / 0.20→0.37，单一宽度带段落从 58/80、67/71 集中降为四档分布，行首禁则 4/5 处归零，元话语 26→9 / 42→14 次）。适用：非投稿文体；判断依据是"重写是否丢事实、是否用分析腔元话话替代直接陈述"，不是篇数或字数。

## turn-report：逐轮汇报

**知识限度免责与结论先行（2026-11-20）**：来源为 [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)（CC BY-SA，WikiProject AI Cleanup 维护；只取模式分类与其对"统计上最可能的表达"这一成因的解释，不逐字复制其文本）、[blader/humanizer](https://github.com/blader/humanizer)（MIT，26 模式；重点采纳 #22 聊天残留、#23 知识限度免责与猜测、#26 重讲读者已知并主张"先给决定"；采纳其"单一弱信号不单独触发、需与另一信号共现"的门控做法）与 Humanizer-zh（MIT，中文词表参考，实施时复核许可证）。适用：逐轮汇报、任务完成说明与变更说明。边界与反例：不采纳其"加人味"目标（其 README 亦自称不试图骗过检测器），本技能只管决策是否清楚；不做作者归属判断；不删限定条件、单位与未做声明；不搬英文专属特征（破折号、弯引号、格式徽章）。

**校准而非去防御（2026-11-20）**：来源为 [Conformal Linguistic Calibration](https://arxiv.org/abs/2502.19110)（事实性与具体性之间存在可调的权衡，说明"说得更具体"与"说得更可能对"不是同一件事）、El Attar 等 2026（[arXiv 2606.04177](https://arxiv.org/abs/2606.04177)，写作特征随模型与文体变化，不宜作身份判据）与 humanizer-pro 自报的误报 0.2%、命中 3.1%（统计型检测不可靠）。采纳：五档强度映射，以及"过防御与过自信是同一错的两端"。适用：一切对外汇报的措辞强度。边界与反例：不以统计特征判定"AI 味"；不要求用户交代生成模型；未知来源文本照常按结构判；有依据的单次"可能"是准确而非防御。

**缩写首现（2026-11-20）**：来源为 [Microsoft Style Guide · Acronyms](https://learn.microsoft.com/en-us/style-guide/acronyms)（全称后接括号缩写、后续直接用、只用在读者熟悉的缩写上、不为产品名造缩写）、[IEEE 802 编辑规则](https://mentor.ieee.org/802.15/dcn/10/15-10-0324-09-0000-wg-editors-instructions.pdf)（全称小写，专名除外）与国家标准 GB/T 7713.1—2006《学位论文编写规则》及高校实施细则（中文缩略词首现注明全称，外文缩略词在译名后用圆括号注明原词全称）。采纳：首现格式、一篇一次、集中登记、单位与代码例外、全称未知标"待核"。适用：汇报、文档与图注中的术语首现。边界与反例：不复制上述文本原文；不把"展开"当义务——能用中文全称就不用缩写；不臆造英文全称；不为凑格式把单位、文件格式或代码标识符展开。

**结论先行的既有实践（2026-11-20）**：Plain Writing Act 2010 与 BLUF（Bottom Line Up Front，结论前置）作为公开先例；ASD-STE100 简化技术英语（ASD 标准，版权归 ASD，仅取"一句一义、主动语态、避免名词堆叠"的思想，不复制规则与受控词表）。内部复用 report-writing 的 R4 直接陈述、paper-writing 的 W9/W10 与成稿去 AI 味检测与语义判据（A/B/C 分级；该文件的 X 级在本技能改称 P 级，避免同名异义）、论文组织与语言规范的"缩写首次给全称、不编造缩写展开词"。边界：文档成稿仍归 W9；本技能不复制其判据，只做逐轮汇报的结构与措辞。

**完成声明需可验（2026-11-20）**：参考 [obra/superpowers](https://github.com/obra/superpowers) 的 verification-before-completion 技能（只读，未运行），采纳"没有运行验证不得声称完成"。边界：不引入其审批菜单、每轮全量测试与嵌套流程；T2 只要求在汇报里标注证据状态，不改变项目既定的验收流程。

## effort-guard：投入与止损

**用户观察（2026-11-20）**：来源为本轮真实对话——用户指出执行模型（Codex 与 GPT 组合）在实验与项目中不估算时间、token、精力与迭代维护成本，随便开工，出错后大量测试与打补丁。用户同时提出反证条件：这样的规则会不会压制模型的发散能力。本技能即按这两条约束设计：既设止损，也不把成本闸前置到探索阶段。适用：多步、多轮或产生费用工作的过程决策。反例：以"用户已说过"为由照抄某次阈值或某项目预算。

**LLM 编码失败模式（Karpathy，2026-01）**：原帖在 X，本仓库未直接抓取；据 [DEV 社区整理](https://dev.to/evan-dong/why-your-ai-coding-assistant-keeps-overengineering-4-rules-that-actually-fix-it-d8a)、[malskill 的 code-guidelines](https://github.com/aeondave/malskill/blob/main/coding/code-guidelines/SKILL.md) 与 npm 包说明三处转述互相一致：模型替你假设且不核对、把代码与 API 复杂化、为简单需求写上千行、顺手改动与任务无关的代码。采纳其行为条目，改写为 E3 最小起点、E4 一次一处。边界与反例：二手转述，未见原文逐字；不把"少写代码"当省事借口，也不把作者的个人风格当标准。

**最简方案优先（Anthropic，2024-12）**：[Building effective agents](https://www.anthropic.com/research/building-effective-agents) 的核心句是 find the simplest solution possible, and only increase complexity when needed。原页在本机抓取失败，经一份课程转引核对（措辞一致）。采纳为 E3。边界与反例：该文面向 agent 系统设计，不构成科研投入阈值；"简单"不指代码行数少，而指组件与自主度够用即可。

**YAGNI 的时机论（Kent Beck，2026-06-24）**：[The Cost YAGNI Was Never About](https://newsletter.kentbeck.com/p/the-cost-yagni-was-never-about)（已读全文）。核心：YAGNI 不是省钱，而是期权与时间价值两笔账；提前建结构等于在信息到达前行使选择权，模型"不懂 YAGNI"，生成变便宜只让违反更便宜、理解更少。采纳为 E3、E8 与探索保护。边界与反例：YAGNI 不等于不设计，作者明言"需要就建"；本文的净现值论证借自软件设计语境，不直接换算科研投入。

**thrash 阈值与治理（Zenodo 预印本，2026-02-13）**：[Governed Agentic Coding](https://zenodo.org/records/18629666)（已读摘要与描述）。现象：循环拉长后声明失去约束力、范围溶解、执行者自授权；经济后果是反复调试、回归震荡与调用消耗。采纳其现象命名与"把停机与拒绝当一等成功"的结构建议（E5、E6）。边界与反例：单作者预印本，非同行评审；不采用其 Governor/Coder 双会话架构，也不把其阈值数字当通用标准。

**自估预算不可靠（NeurIPS 2026）**：[Budget Guard](https://neurips.cc/virtual/2026/loc/sydney/168981)（已读摘要）。长周期 agent 自报的剩余预算区间覆盖率仅 2%—52%，外置校准区间在 19 组中 18 组超过 85%；多资源环境可行性闸把每次成功成本从 $1.61M 降到 $0.87M，但单资源 token 任务只省 3%—7%。采纳：外置判据、按区间不用点估计、收益集中在时间与人工同时受限的场景（E1、E6）。边界与反例：回放而非在线部署；单一环境案例，不外推节省比例。

**预算感知（ICML 2026）**：[Towards Budget-Aware Agents](https://icml.cc/virtual/2026/67798)（页面抓取失败，仅据检索摘要）。把预算感知形式化为"中间过程能否给出剩余资源区间以及任务是否仍可完成"。采纳其问题定义，用于 E1 要求写区间。边界：未读全文，不引用其指标数值。

**有界循环原语（2025—2026 社区对照）**：[agentsop 的跨框架对照](https://github.com/agentsope/skillalchemy/blob/955562e4416c483da946e9c95a1c3974ac52df3c/skills/agentsop-bounded-loop/references/R2-cross-framework.md)列出 LangGraph `recursion_limit=25`、OpenAI Agents SDK `max_turns`，并指出"把上限调高来修循环"是已知陷阱。采纳为 E5 的"不静默放宽"。边界：第三方技能库整理，未经独立验证；不同框架语义不可直接换算。

**两次停手的工程经验（社区 CLAUDE.md）**：[claude-code-guide](https://github.com/ytrofr/claude-code-guide/blob/refs/heads/main/best-practices/BEST-PRACTICES.md) 记录"同一 bug 两次失败必须停、先追踪数据流再改"。采纳为默认阈值 2（E5）。边界与反例：个人工程经验，非对照评测；阈值可被任务覆盖，改则写明。

**时间压力与创造力（Amabile 等，HBR 2002）**：[Creativity Under the Gun](https://store.hbr.org/product/creativity-under-the-gun/R0208C)（摘要与 [APA 报道](https://www.apa.org/monitor/nov02/tickingclock.html)）。九千余份工作日记显示时间压力通常降低创造性探索，而当事人常自以为更努力。采纳为探索保护：预算压力不施加在"要不要想"（第二节）。边界：人类组织研究，迁移到 agent 属类比，不作因果外推。

**约束与创造力的倒 U 形（Acar、Tarakci、van Knippenberg，2019）**：Journal of Management 45(1):96—121，DOI 10.1177/0149206318805832（读过摘要与引用）。约束过少与过多都抑制创造性产出，中等约束配合自主性最优。采纳为"只在决策点施加、强度中等"。边界：组织行为学证据，不提供可套用的数值阈值。

**重复采样的收益与瓶颈（2024）**：[Large Language Monkeys](https://arxiv.org/abs/2407.21787)（已读摘要）。覆盖率随采样数对数线性增长；SWE-bench Lite 从单次 15.9% 到 250 次 56%；无自动验证器时多数投票与奖励模型在几百样本后饱和。采纳为 E7 选择器条件与探索保护。边界与反例：编码与形式证明可自动验证，科研判断多数不可；覆盖率不等于可用性。

**可控的测试时计算（2025）**：[s1](https://ar5iv.labs.arxiv.org/html/2501.19393)。预算强制既能强制终止、也能追加"Wait"延长，可控性本身带来正向 scaling。采纳为"闸要能松开"，支撑按难度分级。边界：推理模型实验，不直接外推到工程修复循环。

**过度思考（ICML 2025）**：[Do NOT Think That Much for 2+3=?](https://icml.cc/virtual/2025/poster/45540)。长推理模型在简单问题上产生冗余推理，存在可压缩空间。采纳为按难度分级的收紧依据。边界：仅据摘要，未复现其压缩方法。

**过早收敛与多样性（类比来源）**：[Premature convergence in morphology and control co-evolution](https://produccion.siia.unam.mx/Publicaciones/ProdCientif/PublicacionFrw.aspx?id=649478)。目标驱动的搜索会丢多样性，质量-多样性类方法为对抗此点而设计。采纳为"单一判据越早介入，替代路线越少"。边界与反例：演化计算结论，迁移到研究工作流属类比，不作为 LLM 行为的直接证据。

## project-agents：项目侧 AGENTS 模板

**项目侧 AGENTS 模板（2026-11-20）**：来源为 [AGENTS.md 开放约定](https://agents.md/)与 [Codex 官方加载说明](https://learn.chatgpt.com/docs/agent-configuration/agents-md)（本文件"项目 AGENTS 入口与规则分层"条目已核）及 [HumanLayer 的指令文件经验](https://www.humanlayer.dev/blog/writing-a-good-claude-md)：项目入口保留长期原则、路径与按需读取路由，详细流程放技能内按需加载；目录发现不等于任意跨目录聊天都会加载目标项目文件。模板由一份真实项目的常驻约定抽象而来，删除全部项目名、目录、状态后端、领域参数与验收状态，只保留通用结构与占位符。适用：新建或改造研究项目的根 AGENTS.md。边界与反例：不携带来源项目的模型、预算、题名与验收状态；不复制技能正文，避免两处维护；占位符与 null 保留给使用方填写；模板随仓库分发，但不参与 research-max 自身的维护判断。

**项目 AGENTS 入口与规则分层（2026-11-12）**：核对 [AGENTS.md 开放约定](https://agents.md/)与 [Codex 官方加载说明](https://learn.chatgpt.com/docs/agent-configuration/agents-md)：项目入口保留长期原则、路径与任务路由，详细流程按需读取；目录发现不等于任意跨目录聊天都会加载目标项目文件。参考 [HumanLayer 的指令文件经验](https://www.humanlayer.dev/blog/writing-a-good-claude-md)及 [steipete/agent-scripts 的 AGENTS.MD](https://github.com/steipete/agent-scripts/blob/main/AGENTS.MD)中的精简常驻内容、按需查阅项目资料与验证实际结果的做法，不移植其特定工具、提交习惯或授权范围。用户提供的 AGENTS 样例仅作结构参考，文档里的命令不视为当前执行指令。此次按用户确认范围统一两项目原则与路由，保留各自任务状态入口；约 80 行、8 KiB 是本次项目维护目标，不冒称官方限制。
