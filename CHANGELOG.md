# CHANGELOG：research-max 过程史

本文件记录迁移、实施验证、测试计数与哈希快照等**过程史**；规则来源与边界见 [SOURCES.md](SOURCES.md)，规则正文见各技能 `references/`。过程记录只描述当时版本，不构成现行验收依据；现有回归以随附测试重新运行为准。

## 2026-11-25 结构去冗余与绘图补强（R2）

- 过程史从 SOURCES.md 迁入本文件；SOURCES 按技能重排，只保留来源、采纳与边界。
- 删除各技能 README.md（与 SKILL.md 重复且多份过期），技能唯一入口为 SKILL.md。
- 编号去撞：turn-report 表述病灶 D1—D8 → TD1—TD8，reply_lint 检查项 R1—R7 → TR1—TR7。
- 跨 Harness 与 GitHub 记录说明各收敛为一份权威 reference；删除 `research-execution/templates/现有项目跨Harness接入.md`。
- 项目与宿主相关例句中性化；领域例子集中到 `examples/领域示例.md`；`integrations/github/record.py` 分支前缀改为可配置。
- 文献入库联动：research-topic D1 增"项目登记本地文献库时先入库、版本关联、强转换器与回查原件"段；project-agents 模板项目硬边界增"文献库"条（适用所有 Harness 与子代理）；SOURCES 登记依据。
- 深读八问与断点暂停：research-topic P2 增深读八问（P9 加对应检查项），精读模板第6、7节升为核心节并补大问题、先记后释、外部评价；D8 改为与用户协同的分析停在断点、补入后入库转换再接续；SKILL 与 project-agents 模板同步。
- figure-craft 补强（进行中，已暂停；续做入口 `figure-craft/绘图补强计划.md`）：已新增期刊版式预设 `journal_profiles.json`、生成的 mplstyle、12 个可运行配方与 figstyle / layout_audit / palette_audit 工具，重写 figure_lint 修复其对真实 matplotlib 导出的失效；TikZ 骨架、references 与 SKILL.md 的 FIG12—FIG14 尚未写入。

## 迁移说明（2026-11-01）

本集合由一个中文科研方法库的 v1.8 工作区技能化迁移而来：精读编号 R1—R9 改为 P1—P9 以消除撞号；W/M/F/A、R1—R5、G0—G9 不变。迁移时的分叉调和与共享物归属裁决已提炼进 SOURCES.md；完整历史裁定与逐版字节史保存在迁移源仓库的 git 标签（v1.5.0 / v1.8.0），仅作档案。figure-craft 的 FIG1—FIG11 由 paper-writing 原 F8—F14 迁出改写（2026-11-21）。Zotero 中文对照组件已独立为 [transfer-plus](https://github.com/let778750-cpu/transfer-plus)（2026-11-18）。

## 实施验证记录

### 跨Harness 本机验证记录（2026-11-07）

本机验证发现并修正：输出管道关闭不能证明子进程已结束；项目内占用不足以阻止不同项目共写一个副本；Windows状态读写须处理短暂共享冲突。另拒绝非有限超时、大小写变体的保留目录、损坏交接及不匹配的恢复会话。真实示例完成三数统计的串行交接与两个前台子代理交接；bare代理能力不足的两次返回保留为失败依据。该示例只验证本机接口与产物复核，不证明复杂科研能力、并行加速或长期正确率提升。

### GitHub 记录独立应用检查（2026-11-08）

独立应用检查暴露并推动修正两项具体缺陷：CLI执行入口先于渲染函数定义导致部分发布后失败；新main已合入模块后仍按启动基线计算范围，误拒绝已发布的上游文件。分别加入实际脚本入口与真实上游文件集成的回归；当前发布基线与历史启动快照分开，仍检查未进入基线的中间越界提交。另外比较Git blob原字节与本地证据，拒绝换行/clean过滤造成“链接内容与哈希不一致”。这些是软件行为验证，不外推科研正确率提升。

### 绘图生产迁出（2026-11-21）

**绘图生产迁出（2026-11-21）**：原 F8—F14 的规则、模板与来源整体迁至 figure-craft 技能，改写为 FIG1—FIG11 并扩写；本条只保留历史指向，不再维护，现行登记见 SOURCES.md figure-craft 节。

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
## 提交史

- 2026-11-01 68c8078 chore: 初始化 research-max 仓库（README、AGENTS、.gitignore）
- 2026-11-01 bd1f16d feat: 迁入 paper-writing 技能并与源库 v1.6—v1.8 完成分叉调和
- 2026-11-01 0a83ff3 feat: 新增 research-execution 技能（流程关卡、数据、推进、实验、分析、归档与检查工具）
- 2026-11-01 f804034 feat: 新增 report-writing 技能（非论文文体 R1—R5 与风格契约卡）
- 2026-11-01 f3a2fec feat: 新增 research-topic 技能（四步法、问题论证、精读 P1—P9）
- 2026-11-01 42e0a13 docs: 补全迁移说明与技能索引
- 2026-11-01 891806a feat: 补齐总则、项目配置域、分歧处理与 SOURCES 来源边界，实现仓库完全自包含
- 2026-11-12 583567f feat: research-topic 调研选题规则精化（按证据动态聚焦与探索行动取舍）
- 2026-11-12 66ef7c8 docs: paper-writing 修正 writing_lint 回归预期表述
- 2026-11-12 db9cc0c feat: 任务状态改用 Markdown 权威载体并支持计划调整同步任务
- 2026-11-12 56a31d6 feat: 新增跨Harness任务执行与GitHub模块记录能力（integrations 显式例外）
- 2026-11-12 64a4972 feat: 新增深度调研与文献综合规范（D1—D8）与近邻命中的处置规则
- 2026-11-12 5865a04 feat: 新增科研绘图生产规范（F8—F14）
- 2026-11-12 ce19ac0 docs: 顶层索引与 SOURCES 登记第一期三项新规则来源
- 2026-11-12 cc049bb feat: 审稿修回补强（意见路线图与回复信）与统计报告完整性清单
- 2026-11-12 af43b43 feat: 投稿阶段要求差异核对与发表阶段版本分存
- 2026-11-12 c95e157 feat: 审稿意见解读排序与修回可行性评估（源自 Rebuttal-Skill 对标）
- 2026-11-12 e6a19d6 feat: 吸收克隆件对标增量（D域检索工艺、W域写作判据、修回优先级）
- 2026-11-12 f2ffeba feat: zotero-bilingual 0.4.0——内核更换 BabelDOC 本地引擎，一键完整性重做
- 2026-11-12 792e37f fix: package_release 允许 0.4.0 运行包携带 BabelDOC/onnxruntime 本地引擎
- 2026-11-15 98fda65 feat: 吸收 lieflat-less-ai-tone 成稿去AI味对标增量
- 2026-11-18 a865143 feat: 全文获取硬前提与前沿覆盖倾斜（D1/D8/P3 链路补强）
- 2026-11-18 067b79d refactor: 移除 zotero-bilingual 集成，插件独立为 transfer-plus 仓库
- 2026-11-20 b902212 feat: 新增 turn-report 逐轮汇报技能（T1—T7）
- 2026-11-20 97c2a8f docs: README 按模块功能描述技能，不列内部规则编号
- 2026-11-20 137a7fb docs: 新增项目侧 AGENTS.md 模板与技能搭配说明
- 2026-11-20 cd50137 feat: 新增 effort-guard 投入与止损技能并接入基座
- 2026-11-20 c46c03b fix: reply_lint 把 AGENTS/README/SOURCES 等文件名排除在缩写检查外
- 2026-11-21 99ae25f feat: 新增 figure-craft 科研图件技能并从 paper-writing 迁出绘图规则
- 2026-11-21 e679f0f fix: reply_lint 把 FIG 编号与 SKILL 文件名排除在缩写检查外
