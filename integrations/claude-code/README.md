# 可选 Claude Code 单模块桥接

需要完整 research-max、Python 3.10+、已安装的 Claude Code，以及用户已配置的可用模型。程序不安装 CLI、不改全局设置、不建调度服务。

本文件只写接口、记录格式与机械保证。何时启用、授权核对、交接责任、审核与修回、交叉核查、暂停与接续，统一按 research-execution 的 `references/跨Harness任务执行.md`；交接模板为 research-execution 的 `templates/跨Harness交接.md`。

## 机械约束

- 桥接只保存尝试与进程事实：不更新任务状态，不做最终验收，不自动派发下一模块；已开始的尝试不自动重放。
- 同一项目同时最多一个运行；工作副本旁的原子占用目录阻止不同权威项目同时写同一副本。
- 首版只接收 Markdown 执行约定；旧 JSON 检查与快照保持兼容。同时发现 `TASKS.md` 与 `tasks.json` 时报歧义，用 `--tasks` 明确选择。
- Markdown 执行约定只是已有授权的记录，不是防恶意调用的权限系统。

## 准备

1. 用 research-execution 的 `scripts/research_infra.py` 检查项目；任务需有实际负责人、V 版本和验收条件。
2. 在任务文件独立二级标题“执行约定”下填写五项（只保留一份可解析约定，历史调整写普通段落）：

| 字段 | 写法 |
|---|---|
| 执行方式 | 跨 Harness |
| 指定任务 | 明确 ID，以顿号或逗号分隔，不支持通配符 |
| 授权来源 | 实际用户指令摘要或可核对引用 |
| 当前接手者 | 本次主持者的明确标识 |
| 派发 | 允许／暂停／结束 |

3. 执行目录是权威项目之外的独立工作副本，且不能包含权威项目。Git 项目可用独立 worktree 再带入必要的未提交修改；工具不自动 stash、reset 或整目录覆盖。关键输入在两个目录中保持相同相对路径与字节，用 `--input` 逐一绑定；大数据按实际必要范围配置。
4. 在项目内写 Markdown 实施说明：必读材料、方法约束、资源范围与停止条件。说明变更需新尝试。提示词与工作副本中不放密钥。

## 命令接口

尖括号内容必须替换；以下是命令形状，不是已执行示例。

```text
python bridge.py prepare --root <权威项目> --task <任务ID> --run <唯一尝试ID> --owner <当前接手者> --workspace <独立工作副本> --instructions <项目内说明.md> --input <关键输入相对路径> --write <允许修改相对路径> --model <执行模型ID> --timeout <秒数> [--tasks <任务文件>] [--resume-run <旧尝试ID>] [--parallel]
python bridge.py run --root <权威项目> --run <尝试ID> --owner <当前接手者>
python bridge.py status --root <权威项目> --run <尝试ID>
python bridge.py cancel --root <权威项目> --run <尝试ID>
python bridge.py release --root <权威项目> --run <尝试ID>
```

| 参数／命令 | 机械含义 |
|---|---|
| prepare、status、cancel、release | 只操作本地文件；只有 run 调用模型。prepare 与 run 分开，主持者可先读 BRIEF.md |
| `--input`、`--write` | 可重复。无 write 时只允许返回检查结果；目录 write 允许其子路径；禁止整个工作副本、路径穿越与链接目标 |
| `--timeout` | 有限正数，为本次调用上限；不代表计费上限；模型品牌与角色不认证服务端身份 |
| `--resume-run` | 修回用新 `--run` 并指定旧尝试；只恢复相同任务、相同工作副本且已结束的尝试，用明确会话 ID；无会话 ID 时开新尝试。不用 `--continue` 猜最近会话；新模块默认新会话 |
| 只读复核 | CLI 只派发待做／进行中任务：用复核卡 ID 准备新会话，不加 `--write`，最终回复保存为 REPORT.md；确需输出时只给新的结果路径，原输入与代码不纳入写域 |
| `--parallel` | 仅本次会话注册 module-worker 并开放前台 Agent 工具；用项目专属 `CLAUDE_CONFIG_DIR`、空 setting-sources、禁用 hooks 与自动记忆，显式 `--agents`（实测 bare 模式传 `--agents` 仍只给基础工具）。不写用户全局目录；串行与并行不能互相恢复会话；关闭实验性 Agent Teams；子代理须在本次结束前收尾 |

run 是前台控制进程，可交给主持端的长时命令工具并查询同一次调用；无需可见终端。退出码：0 命令成功（run 只表示可提交审核），1 未满足机械交付条件，2 参数／输入／前置条件错误。

## 运行与返回记录

权威项目 `.research-harness/runs/<尝试ID>/`：

| 文件 | 内容 |
|---|---|
| BRIEF.md、dispatch.json、binding.json | 生成的派发与版本清单 |
| started.json | 启动占用证据 |
| runtime.json、events.jsonl | 运行事实；筛选后的事件元数据（事件类型、会话、报告的模型名、工具调用名、结束信息；不存思考、工具参数、环境转储） |
| REPORT.md、stderr.txt | 实际最终回复；必要的错误输出 |

- 生成记录不手工编辑；失败尝试保留，不用同 ID 覆盖。`active/` 只存项目运行占用；工作副本相邻的 `.research-harness-<路径摘要>.lock/` 记录共享副本占用，正常结束时删除。
- 串行调用用 `--bare`；提示词经 stdin 传入，argv 不拼 shell 命令；只传当前模块必要工具，禁用自动记忆与 hooks，只连显式空 MCP 配置，排除自动发现的指令文件。适用项目约定须由主持者写入实施说明或列为材料。组织托管策略仍由 CLI 执行，不承诺覆盖。
- 从用户设置只读取 Anthropic 端点／鉴权与模型映射等小范围环境项到进程内存，不复制整个配置；环境变量优先。鉴权依赖 API key/token，不承诺 bare 模式支持订阅登录。
- 已知凭据值从回执与错误输出脱敏，不保证识别未知敏感数据。完整会话转录由 CLI 自管；并行模式转录在 `.research-harness/claude-profile`，未核对不得发布。
- `ready_for_review=true` 的条件：唯一成功结果事件、退出码 0、回执身份与要求匹配、报告完成且子作业结束、输入与要求仍有效、工作副本无范围外改动。部分完成、受阻、缺结果、非零退出、重复结束事件、旧依据、残留子进程均不满足。status 会再次检查证据是否改变。它不评价科学结论、不证明自检真的执行，也不替代主持者独立检查。

## 停止与恢复

- cancel 只写取消请求；控制进程观察后终止自己拥有的进程树，再用 status 核对。Windows 用 Job Object（目标 CLI 归入 Job 前不启动，控制进程崩溃时系统关闭 Job）；POSIX 用进程组，控制进程被强杀后的残留需核查。WMI、远端服务、脱离进程组的作业不受保证，首版不允许启动。
- 主调用结束后仍有普通子进程时，桥接清理并拒绝报告机械完成。提示词与 Job Object 不是文件系统或网络沙箱，只核查声明输入与工作副本；不对不可信代码宣称隔离安全。
- 控制进程退出而 active 占用残留：先核对回执与产物，再 release。release 要求记录的控制与直接运行进程均不存活，无法核清时不抢占；它只解除占用，不续跑、不验收。取消、超时或结果未知后先判断实际效果再新建尝试；准备后工作副本改变也要新建尝试。

## 本地验证

```text
python -B -m unittest -v test_bridge
```

测试用隔离临时目录和模拟 CLI，不调用模型，不改用户配置。真实模型验证另用标注为示例的任务、小预算和独立工作副本；串行闭环通过后再测前台子代理。
