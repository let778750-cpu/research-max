# research-max 维护约定

- 本仓库是科研全流程技能集合，共七个技能：research-topic（选题与调研）、research-execution（研究执行）、paper-writing（论文写作）、figure-craft（科研图件）、report-writing（非论文报告）、turn-report（逐轮汇报）、effort-guard（投入与止损）；另有 project-agents 模板与 integrations 可选组件。以整仓分发，自包含，不依赖外部方法库。
- 每条规则在所属技能的 references/ 内单一维护；技能间共享的模板与脚本只随一个技能分发，消费方按名提及（技能名 + 文件名纯文本）。
- 技能内的相对链接（含 `../`）不得越出该技能目录；禁止跨技能 markdown 链接；不得出现私有绝对路径。顶层 README、SOURCES、CHANGELOG 与 examples/ 是跨技能链接和仓库级说明的唯一例外；integrations 文档按名提及 research-execution 的文件。
- 来源、采纳理由、适用边界与反例只记在 [SOURCES.md](SOURCES.md)；迁移、实施验证、测试计数、哈希与提交史只记在 [CHANGELOG.md](CHANGELOG.md)，不写进 SOURCES 或技能正文。修改规则前先核对其边界，适用条件变化时同步更新，不默默放宽。新增经验先给适用范围、反例和验证依据，再进入技能正文。
- 技能正文保持领域中性；有教学价值的领域例子（航空航天、观测调度等）只放 [examples/领域示例.md](examples/领域示例.md)，按技能分节并标“示例”。figure-craft 的领域图型配方属于技能本身，不受此限。
- 模板保持空白（待填/null）；示例必须标注“示例”；不携带任何来源项目的模型、题名、预算、样本量与验收状态（通用反例清单见 SOURCES.md）。
- 规则编号前缀在仓库内唯一（各技能 SKILL.md 规则地图为准）；新增前缀先做撞号扫描。
- 各技能内工具脚本只用本地文件，不联网、不调用模型、不付费；机械通过不代表实质审查通过。
- 按改动影响验证：文字、入口与引用调整检查对应内容和链接；影响技能选择或执行判断时做针对性应用检查；工具改动运行相关正反例。复杂行为变更再安排独立代理评测，不把整套评测作为每次文字小修的固定步骤。
- 确认交付可用后，清理临时备份、一次性修订脚本、渲染预览和浏览器日志，包括库外工作目录与系统临时目录；保留正式产物和必要科研证据，清理后同步引用，不另搬目录继续堆积。

## 显式例外登记

- report-writing 无自有脚本：写作机械自检按名使用 paper-writing 的 `scripts/writing_lint.py`，去 AI 味检测按名使用 paper-writing 的 `scripts/ai_tone_detect.py`（规则与阈值归写作域，单副本防漂移）。
- integrations/claude-code：仅在用户指定具体任务采用跨 Harness 执行后，调用已配置的 Claude Code 及其模型；不自动安装、不改全局配置、不启动其他任务、不改写任务验收。它从 research-execution 读取共用任务接口；运行能力不改变普通技能的发现与使用方式。
- integrations/github：仅在用户指定具体项目或任务采用 GitHub 记录并开始执行后，使用已配置 Git 与 GitHub CLI 向明确私有仓库发布总览、模块 PR 和合并；不调用模型、不改写任务状态、不增加 PR 审核轮次、不改全局配置、不绕过仓库保护。离线分组检查归 research-execution/scripts；测试用本地 Git 与模拟 GitHub，真实远端演练须有用户指定仓库。
