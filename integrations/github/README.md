# 可选 GitHub 模块记录

使用本机 Git、GitHub CLI及已配置身份，在用户指定的私有仓库记录实验推进。方法规则由 research-execution 的 GitHub模块记录.md 维护。组件随整仓分发，不自动安装工具、修改全局配置、调用模型、更新任务状态或增加一次PR审核。

## 接入前提

- 主持者已核实当前对话中的用户授权，在权威任务Markdown填写GitHub记录约定与模块分组；读取文件本身不构成授权。首次启动需要准确owner/repo，不猜默认仓库。当前版本GitHub模式使用Markdown；旧JSON离线功能不变。
- 项目根就是Git工作区根；初始接入位于约定基线分支，已有仓库先同步该基线。绑定origin可为同仓库的标准HTTPS或SSH地址；不覆盖其他远端，不自动发布未登记的本地历史。
- 目标为可写私有仓库并允许merge commit。connect默认接入已有仓库；仅显式--create-private才尝试创建，网络错误不当成仓库不存在。首次接入提交初始计划/任务和首页导航；已有分支保护拒绝直接发布时，主持者按原规则把这些明确文件通过初始化PR集成，再重试接入，不绕过保护。
- 首版单个活动模块串行集成。Codex持有权威目录，Claude执行副本在其外部；先start再准备桥接。桥接active占用存在时不进行发布写操作。status可只读查询，不接管、不发布。

## CLI

以下为占位命令，不是本仓库实际发布授权。所有路径以项目根为基准；--file逐个列出文件，不接受目录、通配符、绝对路径或越界链接。

```text
python integrations/github/record.py connect --root <项目> --owner <当前接手者> --file <项目必要文件> [--create-private] [--tasks <自定义任务Markdown>]
python integrations/github/record.py start --root <项目> --owner <当前接手者> --module <M-ID> --iteration 1 --file <本轮明确文件>
python integrations/github/record.py publish --root <项目> --owner <当前接手者> --module <M-ID> --iteration 1 --file <新增文件> --message <实际变化>
python integrations/github/record.py attest --root <项目> --owner <当前接手者> --module <M-ID> --iteration 1 --evidence <已有检查记录>
python integrations/github/record.py merge --root <项目> --owner <当前接手者> --module <M-ID> --iteration 1
python integrations/github/record.py status --root <项目> [--module <M-ID> --iteration 1]
```

每次命令都重新读取权威文件。自定义--tasks须在后续命令继续传入；约定仓库、基线或任务源改变时不静默重绑。

connect创建/复用一个带生成标记的总览Issue并置顶，给README追加导航，不覆盖人工正文。start创建codex/<模块小写>-r<轮次>分支，以及research-records/modules/<模块>/r<轮次>.md历史启动记录，产生实际提交后建Draft PR。状态由主持者按事实更新；工具不把创建分支当成实验已开始或任务已验收。

publish只提交本轮登记文件，新增文件须显式--file；自动包含所选任务文件、所关联计划和project.json。实际产物/回执必须同时发布；若其文件尚未纳入已提交快照，会拒绝发布带失效证据链接的PR。已登记文件删除可以提交；无关暂存和未跟踪文件保持原样。私钥、常见令牌、配置/原始桥接日志和超过10MiB文件拒绝发布；这是有限预检，不是秘密信息认证或Git数据沙箱。中间提交也会推送，因此检查整个待发布分支历史，不能用“最后删除了”掩盖范围外文件。

attest只封存已有审核：所有必要成员已验收，要求绑定有效，本地/已发布/PR头提交相同，基线已集成，已有检查文件确实在该提交中。--evidence可重复，用现有报告、任务自检记录或复核文件，不要求新建PR审核报告。主持者必须实际检查集成条件；文件存在和哈希不能证明该条件成立。封存不调用模型、不运行第二套测试、不修改验收记录。

任务、计划和验收证据按原始字节绑定。发布前逐文件比较Git blob与本地SHA256；若CRLF/clean过滤改变字节，先按项目规则为这些明确路径设置保持字节的.gitattributes或统一格式并重新核实受影响记录，不自动改用户Git配置或重签旧验收。不能让总览所列哈希与链接文件实际内容不同。

merge匹配封存的头提交，复核当前基线、证据和模块要求，转正式PR后使用gh pr merge --merge --match-head-commit。它不请求reviewer、--admin或--auto；仓库自身规则仍可能要求检查或排队，未确认实际合并时不得推进下游。核实远端merge commit的父提交、内容及基线可达性后才记作已核实。GitHub服务端不能通过该参数锁定目标分支；并发基线竞态若改变实际合并，工具明确失败并保留远端事实，主持者核对实际差异，不能假称已核实或自动回滚。

## 恢复与边界

`.research-github/`只存仓库/Issue/PR标识、提交、封存哈希和同步事实，通过本仓库Git exclude排除；不存第二份可编辑任务状态。模块要求及任务当前状态始终从Markdown读取。首次操作建立本地operation.lock，写入进程及主持者；正常结束移除。崩溃遗留时先核对该PID和操作结果，确认原进程结束后仅移除这个明确的锁，不自动按超时抢占。

网络异常后用status及明确轮次恢复；start会查已有PR，merge会先核对已合并结果，避免响应丢失导致重复操作。成功合并后不复用旧分支，也不自动删除分支/工作副本；新轮次从最新基线建立。任务要求变更后旧封存失效，保留历史证据，只重验受影响部分。

工具不提供后台调度；由当前Codex在用户授权范围内调用。暂停发布仍可status；不得以发布故障重启模型或重跑实验。总览是最后成功发布的快照，只有更新时查询GitHub，不能保证离线期间显示实时远端变化。

## 验证

```text
python -X utf8 -B -m unittest discover -s research-execution/scripts -p test_*.py
python -X utf8 -B -m unittest discover -s integrations/github -p test_record.py
python -X utf8 -B -m unittest discover -s integrations/claude-code -p test_bridge.py
```

GitHub测试使用临时中文路径、本地bare远端和模拟GitHub；不访问真实GitHub、不调用模型。覆盖创建/合并响应丢失、私有及范围限制、部分完成、证据漂移、基线变化、未提交工作保护等。真实私有仓库的权限、保护策略和端到端接口仍须在用户指定仓库中演练，不能把模拟通过写成已完成真实发布。
