# 可选 GitHub 模块记录

使用本机 Git、GitHub CLI 及已配置身份，在用户指定的私有仓库记录实验推进。组件随整仓分发，不自动安装工具、不改全局配置、不调用模型、不更新任务状态，也不增加一次 PR 审核。

本文件只写前提、命令、记录格式与恢复步骤。何时启用、分工与唯一状态、每轮实施、审核与合并判断、调整与接续，统一按 research-execution 的 `references/GitHub模块记录.md`；模块分组离线检查用 research-execution 的 `scripts/module_groups.py`。

## 接入前提

- 主持者已核实当前对话中的用户授权，并在权威任务 Markdown 填写 GitHub 记录约定与模块分组；读取文件本身不构成授权。首次启动需要准确 owner/repo，不猜默认仓库。GitHub 模式只用 Markdown；旧 JSON 离线功能不变。
- 项目根就是 Git 工作区根；初次接入位于约定基线分支，已有仓库先同步该基线。origin 可为同仓库的标准 HTTPS 或 SSH 地址；不覆盖其他远端，不自动发布未登记的本地历史。
- 目标为可写私有仓库并允许 merge commit。connect 默认接入已有仓库；仅显式 `--create-private` 才尝试创建，网络错误不当成仓库不存在。分支保护拒绝直接发布初始文件时，主持者把这些明确文件经初始化 PR 集成后重试，不绕过保护。
- 首版单个活动模块串行集成。主持会话持有权威目录，执行端副本在其外部；先 start 再准备桥接。桥接 active 占用存在时，发布类写操作被拒绝；status 可只读查询。

## CLI

以下为占位命令，不是本仓库实际发布授权。路径以项目根为基准；`--file` 逐个列出文件，不接受目录、通配符、绝对路径或越界链接。

```text
python integrations/github/record.py connect --root <项目> --owner <当前接手者> --file <项目必要文件> [--create-private] [--tasks <自定义任务Markdown>]
python integrations/github/record.py start --root <项目> --owner <当前接手者> --module <M-ID> --iteration 1 --file <本轮明确文件> [--branch-prefix <前缀>]
python integrations/github/record.py publish --root <项目> --owner <当前接手者> --module <M-ID> --iteration 1 --file <新增文件> --message <实际变化>
python integrations/github/record.py attest --root <项目> --owner <当前接手者> --module <M-ID> --iteration 1 --evidence <已有检查记录>
python integrations/github/record.py merge --root <项目> --owner <当前接手者> --module <M-ID> --iteration 1
python integrations/github/record.py status --root <项目> [--module <M-ID> --iteration 1]
```

每次命令都重新读取权威文件。自定义 `--tasks` 须在后续命令继续传入；约定仓库、基线或任务源改变时不静默重绑。

| 命令 | 做什么 | 拒绝或不做什么 |
|---|---|---|
| connect | 创建或复用带生成标记的总览 Issue 并置顶；给 README 追加导航；提交初始计划／任务 | 不覆盖人工正文、已有远端或未登记历史 |
| start | 建 `<前缀>/<模块小写>-r<轮次>` 分支（默认前缀 `codex`，兼容既有记录；新项目可用 `--branch-prefix` 改，须通过 `git check-ref-format`）与 `research-records/modules/<模块>/r<轮次>.md` 启动记录，有实际提交后建 Draft PR | 不把建分支当成实验已开始或任务已验收；轮次须递增；目标分支已存在而无本地登记时拒绝 |
| publish | 只提交本轮登记文件（新增文件须显式 `--file`），自动带上任务文件、关联计划与 project.json；可提交已登记文件的删除 | 产物或回执未进入已提交快照、私钥与常见令牌、配置或原始桥接日志、超过 10 MiB 的文件均拒绝；检查整段待发布历史，不能用“最后删除了”掩盖。此为有限预检，不是秘密认证或 Git 沙箱 |
| attest | 封存已有审核：成员已验收、要求绑定有效、本地／已发布／PR 头提交相同、基线已集成、检查文件确在该提交中；`--evidence` 可重复 | 不调用模型、不跑第二套测试、不改验收记录；文件与哈希存在不能证明集成条件成立，主持者须实际检查 |
| merge | 匹配封存头提交，复核基线、证据与模块要求，转正式 PR 后 `gh pr merge --merge --match-head-commit`；核实远端 merge commit 的父提交、内容与基线可达性后记为已核实 | 不请求 reviewer，不用 `--admin`／`--auto`；未确认实际合并不推进下游；并发基线竞态改变结果时明确失败并保留远端事实，不自动回滚 |
| status | 只读查询仓库、总览、模块 PR 与任务状态 | 不接管、不发布、不派发 |

任务、计划和验收证据按原始字节绑定：发布前逐文件比较 Git blob 与本地 SHA256。若 CRLF 或 clean 过滤改变字节，先按项目规则为这些明确路径设置保持字节的 `.gitattributes` 或统一格式，并重新核实受影响记录；工具不改用户 Git 配置，也不重签旧验收。

## 恢复与边界

- `.research-github/` 只存仓库／Issue／PR 标识、提交、封存哈希和同步事实，经本仓库 Git exclude 排除；不存第二份可编辑任务状态，模块要求与任务状态始终从 Markdown 读取。
- 操作期间持有本地 `operation.lock`（记录进程与主持者），正常结束移除。崩溃遗留时先核对该 PID 与操作结果，确认原进程结束后只移除这个锁；不按超时抢占。
- 网络异常后用 status 与明确轮次恢复：start 会查已有 PR，merge 会先核对已合并结果，避免响应丢失导致重复操作。合并后不复用旧分支，也不自动删除分支或工作副本；新轮次从最新基线建立。任务要求变更后旧封存失效，只重验受影响部分。
- 工具不提供后台调度，由主持端在授权范围内调用。暂停发布时仍可 status；不得以发布故障重启模型或重跑实验。总览是最后成功发布的快照，不代表离线期间的实时远端状态。

## 验证

```text
python -X utf8 -B -m unittest discover -s research-execution/scripts -p test_*.py
python -X utf8 -B -m unittest discover -s integrations/github -p test_record.py
python -X utf8 -B -m unittest discover -s integrations/claude-code -p test_bridge.py
```

GitHub 测试使用临时中文路径、本地 bare 远端和模拟 GitHub，不访问真实 GitHub、不调用模型；覆盖创建／合并响应丢失、私有与范围限制、部分完成、证据漂移、基线变化、未提交工作保护与分支前缀校验。真实私有仓库的权限、保护策略和端到端接口须在用户指定仓库中演练，模拟通过不等于已完成真实发布。
