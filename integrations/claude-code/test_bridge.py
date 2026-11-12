"""Isolated behavioral tests; no model invocation or user configuration mutation."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

import bridge as b


TASKS = """# 示例任务
- 计划文件：[计划](PLAN.md)
- 已同步计划修订：R1

## 执行约定
- 执行方式：跨 Harness
- 指定任务：T-001
- 授权来源：用户明确指定本隔离示例任务使用跨Harness执行
- 当前接手者：示例主持者
- 派发：允许

## T-001 示例评分核验
- 状态：待做
- 要求版本：V1
- 对应计划：[计划](PLAN.md)
- 依赖：无
- 负责人：示例执行者
- 复核方式：独立复核

### 目标与边界
检查三个数的均值，保留负结果的解释；仅为工具示例。
### 输入与版本
输入在input.txt，版本由派发绑定。
### 验收条件
- 使用独立加总与除法核对结果，报告实际检查范围。
### 当前进展与下一步
尚未执行。

## T-002 示例未指定任务
- 状态：待做
- 要求版本：V1
- 依赖：无
- 负责人：示例执行者
- 复核方式：自检
### 目标与边界
未指定跨Harness的独立工作。
### 验收条件
- 保留原执行方式。
"""

FAKE = r'''
import json,os,pathlib,re,subprocess,sys,time
text=sys.stdin.read()
mode=os.environ.get('FAKE_MODE','ok')
task=re.search(r'^- 任务：(.*)$',text,re.M)[1]
run=re.search(r'^- 尝试：(.*)$',text,re.M)[1]
basis=re.search(r'^- 要求依据：(.*)$',text,re.M)[1]
if mode=='slow':time.sleep(30)
if mode in ('child','quiet_child'):
 opts={'stdout':subprocess.DEVNULL,'stderr':subprocess.DEVNULL,'stdin':subprocess.DEVNULL} if mode=='quiet_child' else {}
 p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)'],**opts)
 pathlib.Path('child.pid').write_text(str(p.pid))
if mode=='outside':pathlib.Path('outside.txt').write_text('bad')
if mode=='alter_input':pathlib.Path('input.txt').write_text('changed')
if mode=='mutate_source':pathlib.Path(os.environ['SOURCE_INPUT']).write_text('changed')
if mode=='no_result':sys.exit(0)
pathlib.Path('result.txt').write_text('mean = 2\nnegative result accepted as evidence',encoding='utf-8')
outcome='部分完成' if mode=='partial' else '完成'
report=f'# 模块执行回执\n- 任务：{task}\n- 尝试：{run}\n- 要求依据：{basis}\n- 结果：{outcome}\n- 子作业：已结束\n## 实际产物\nresult.txt\n## 检查结果\n独立加总1+2+3=6，除以3得2；未支持性能提升。\n## 缺口与偏差\n仅检查此示例。'
if mode=='wrong':report=report.replace(run,'wrong-run')
if mode=='secret':report+='\n'+os.environ['TEST_SECRET_TOKEN']
event={'type':'result','subtype':'success','is_error':False,'session_id':os.environ['FAKE_SESSION'],'result':report}
if mode=='error':event.update(is_error=True,subtype='error_during_execution')
print(json.dumps(event,ensure_ascii=False),flush=True)
if mode=='duplicate':print(json.dumps(event),flush=True)
'''


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="research-bridge-示例-")
        self.base = Path(self.temp.name)
        self.root, self.work = self.base / "权威项目", self.base / "执行 副本"
        self.root.mkdir(); self.work.mkdir()
        (self.root / "PLAN.md").write_text("# 示例计划\n- 当前修订：R1\n", encoding="utf-8")
        (self.root / "TASKS.md").write_text(TASKS, encoding="utf-8")
        (self.root / "project.json").write_text('{"schema_version":1,"name":"隔离示例"}', encoding="utf-8")
        for folder in (self.root, self.work):
            (folder / "input.txt").write_text("1 2 3", encoding="utf-8")
        (self.root / "instructions.md").write_text('只检查示例均值。\n保留中文、引号"及换行。', encoding="utf-8")
        self.fake = self.base / "fake.py"
        self.fake.write_text(FAKE, encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def edit(self, old, new):
        p = self.root / "TASKS.md"
        p.write_text(p.read_text(encoding="utf-8").replace(old,new),encoding="utf-8")

    def prepare(self, **kwargs):
        args = dict(task_id="T-001", run_id="T-001-a01", owner="示例主持者", workspace=self.work,
                    inputs=["input.txt"], writes=["result.txt"], instructions="instructions.md",
                    model="test-only", timeout=10)
        args.update(kwargs)
        return b.prepare(self.root, **args)

    def run_fake(self, mode="ok", run_id="T-001-a01"):
        data = b.read_dispatch(self.root, run_id)[1]
        return b.execute(self.root, run_id, "示例主持者", command=[sys.executable,str(self.fake)],
                         env_override={"FAKE_MODE":mode,"FAKE_SESSION":data["session_id"],
                                       "SOURCE_INPUT":str(self.root/'input.txt'),
                                       "TEST_SECRET_TOKEN":"SENSITIVE_EXAMPLE_123456"})

    def test_success_keeps_tasks_authoritative(self):
        before = (self.root/'TASKS.md').read_bytes()
        self.prepare()
        result = self.run_fake()
        self.assertTrue(result['ready_for_review'], result)
        self.assertEqual(before,(self.root/'TASKS.md').read_bytes())
        self.assertEqual(result['changes'],{'result.txt':b.infra.digest(self.work/'result.txt')})

    def test_unselected_task(self):
        with self.assertRaisesRegex(ValueError,'指定范围'):self.prepare(task_id='T-002')

    def test_no_agreement_no_activation(self):
        self.edit('## 执行约定','## 历史讨论')
        with self.assertRaisesRegex(ValueError,'执行约定'):self.prepare()

    def test_paused_prevents_launch(self):
        self.prepare(); self.edit('- 派发：允许','- 派发：暂停')
        with self.assertRaisesRegex(ValueError,'暂停'):self.run_fake()
        self.assertFalse((self.work/'result.txt').exists())

    def test_owner_mismatch(self):
        with self.assertRaisesRegex(ValueError,'接手者'):self.prepare(owner='另一个窗口')

    def test_unknown_scope(self):
        self.edit('指定任务：T-001','指定任务：T-999')
        with self.assertRaisesRegex(ValueError,'不存在'):self.prepare()

    def test_duplicate_agreement(self):
        self.edit('- 派发：允许','- 派发：允许\n- 派发：允许')
        with self.assertRaisesRegex(ValueError,'重复'):self.prepare()

    def test_quoted_and_fenced_agreements_are_not_authority(self):
        self.edit('## 执行约定','> ## 执行约定')
        with self.assertRaises(ValueError):self.prepare()

    def test_dependency_is_not_automatically_launched(self):
        self.edit('- 依赖：无','- 依赖：T-002', )
        with self.assertRaises(ValueError):self.prepare()

    def test_mismatched_input(self):
        (self.work/'input.txt').write_text('different')
        with self.assertRaisesRegex(ValueError,'输入版本'):self.prepare()

    def test_workspace_must_be_isolated(self):
        with self.assertRaisesRegex(ValueError,'副本'):self.prepare(workspace=self.root)

    def test_path_escape(self):
        for path in ('../escape','C:/escape','.', '.claude/settings.json'):
            with self.subTest(path=path),self.assertRaises(ValueError):self.prepare(writes=[path])

    def test_immutable_attempt(self):
        self.prepare()
        with self.assertRaises(FileExistsError):self.prepare()

    def test_replay_does_not_change_previous_success(self):
        self.prepare(); self.run_fake()
        before=(b.run_folder(self.root,'T-001-a01')/'runtime.json').read_bytes()
        with self.assertRaisesRegex(ValueError,'重复'):self.run_fake()
        self.assertEqual(before,(b.run_folder(self.root,'T-001-a01')/'runtime.json').read_bytes())

    def test_stale_requirements(self):
        self.prepare(); self.edit('使用独立加总与除法','检查分母后使用独立加总与除法')
        with self.assertRaisesRegex(ValueError,'要求已改变'):self.run_fake()

    def test_progress_does_not_invalidate(self):
        self.prepare(); self.edit('尚未执行。','已安排执行，先核对输入。')
        self.assertTrue(self.run_fake()['ready_for_review'])

    def test_unrelated_plan_revision_can_be_synced(self):
        self.prepare(); self.edit('已同步计划修订：R1','已同步计划修订：R2')
        (self.root/'PLAN.md').write_text('# 示例计划\n- 当前修订：R2\n仅修改未指定任务安排。',encoding='utf-8')
        self.assertTrue(self.run_fake()['ready_for_review'])

    def test_late_source_mutation(self):
        self.prepare()
        result=self.run_fake('mutate_source')
        self.assertFalse(result['ready_for_review'])
        self.assertTrue(any('关键输入' in s for s in result['errors']))

    def test_source_change_after_return(self):
        self.prepare();self.run_fake();(self.root/'input.txt').write_text('4 5 6')
        self.assertFalse(b.status(self.root,'T-001-a01')['ready_for_review'])

    def test_artifact_change_after_return(self):
        self.prepare();self.run_fake();(self.work/'result.txt').write_text('changed')
        self.assertFalse(b.status(self.root,'T-001-a01')['ready_for_review'])

    def test_report_change_after_return(self):
        self.prepare();self.run_fake();(b.run_folder(self.root,'T-001-a01')/'REPORT.md').write_text('changed')
        self.assertFalse(b.status(self.root,'T-001-a01')['ready_for_review'])

    def test_error_partial_missing_or_duplicate_not_ready(self):
        for mode in ('error','partial','no_result','duplicate','wrong','outside','alter_input'):
            with self.subTest(mode=mode):
                run='case-'+mode
                self.prepare(run_id=run)
                self.assertFalse(self.run_fake(mode,run)['ready_for_review'])

    def test_secret_not_saved(self):
        self.prepare();self.run_fake('secret')
        for p in b.run_folder(self.root,'T-001-a01').iterdir():
            if p.is_file():self.assertNotIn('SENSITIVE_EXAMPLE_123456',p.read_text(encoding='utf-8'))

    def test_timeout(self):
        self.prepare(timeout=.3)
        self.assertEqual(self.run_fake('slow')['phase'],'timed_out')

    def test_cancel_is_request_then_observed_end(self):
        self.prepare()
        results=[]
        worker=threading.Thread(target=lambda:results.append(self.run_fake('slow')))
        worker.start()
        for _ in range(100):
            if b.status(self.root,'T-001-a01')['phase']=='running':break
            time.sleep(.02)
        self.assertTrue(b.cancel(self.root,'T-001-a01')['cancel_requested'])
        worker.join(12)
        self.assertFalse(worker.is_alive())
        self.assertEqual(results[0]['phase'],'cancelled')

    def test_lingering_child_rejects_completion(self):
        self.prepare(writes=['result.txt','child.pid'])
        result=self.run_fake('child')
        self.assertFalse(result['ready_for_review'])
        self.assertTrue(any('子作业' in s for s in result['errors']),result)
        pid=int((self.work/'child.pid').read_text())
        for _ in range(50):
            if not b.alive(pid):break
            time.sleep(.02)
        self.assertFalse(b.alive(pid))

    def test_project_busy(self):
        self.prepare()
        active=self.root/b.META_DIR/'active';active.mkdir()
        with self.assertRaisesRegex(ValueError,'在途'):self.run_fake()

    def test_resume_is_explicit_and_same_task(self):
        self.prepare();self.run_fake()
        self.prepare(run_id='repair',resume_run='T-001-a01')
        new=b.read_dispatch(self.root,'repair')[1]
        old=b.read_dispatch(self.root,'T-001-a01')[1]
        self.assertEqual(new['session_id'],old['session_id'])

    def test_brief_tampering(self):
        self.prepare();(b.run_folder(self.root,'T-001-a01')/'BRIEF.md').write_text('changed')
        with self.assertRaisesRegex(ValueError,'交接包'):self.run_fake()

    def test_status_never_spawns(self):
        self.prepare()
        for _ in range(3):self.assertEqual(b.status(self.root,'T-001-a01')['phase'],'prepared')
        self.assertFalse((self.work/'result.txt').exists())

    def test_npm_native_and_js_entrypoints_without_shell(self):
        self.prepare()
        data=b.read_dispatch(self.root,'T-001-a01')[1]
        npm=self.base/'npm'; package=npm/'node_modules/@anthropic-ai/claude-code'
        (package/'bin').mkdir(parents=True)
        shim=npm/'claude.cmd';shim.write_text('must not execute shim')
        for entry in ('bin/claude.exe','cli.js'):
            (package/entry).write_text('test entry')
            (package/'package.json').write_text(json.dumps({'bin':{'claude':entry}}))
            mapping={'claude.cmd':str(shim),'node':'node.exe'}
            with patch.object(b.shutil,'which',side_effect=lambda name:mapping.get(name)):
                argv=b.claude_command(data)
            self.assertIn(str(package/entry),argv)
            self.assertNotIn(str(shim),argv)
            self.assertIn('--bare',argv)

    def test_nonfinite_timeout_rejected(self):
        for value in (float('nan'),float('inf'),float('-inf'),0,-1):
            with self.subTest(value=value),self.assertRaises(ValueError):self.prepare(timeout=value)

    def test_windows_reserved_names_and_case(self):
        for name in ('.GIT/config','.CLAUDE/settings.json','.RESEARCH-HARNESS/x','NUL.txt','folder./a'):
            with self.subTest(name=name),self.assertRaises(ValueError):self.prepare(writes=[name])

    def test_resume_checks_old_binding(self):
        self.prepare();self.run_fake()
        old=b.run_folder(self.root,'T-001-a01')/'dispatch.json'
        value=json.loads(old.read_text(encoding='utf-8'));value['model']='tampered'
        old.write_text(json.dumps(value),encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'派发记录'):
            self.prepare(run_id='repair',resume_run='T-001-a01')

    def test_quiet_child_cannot_escape_gate(self):
        self.prepare(writes=['result.txt','child.pid'])
        result=self.run_fake('quiet_child')
        self.assertFalse(result['ready_for_review'])
        pid=int((self.work/'child.pid').read_text())
        for _ in range(50):
            if not b.alive(pid):break
            time.sleep(.02)
        self.assertFalse(b.alive(pid))

    def test_workspace_lock_shared_across_projects(self):
        self.prepare()
        second=self.base/'second';second.mkdir()
        for name in ('project.json','PLAN.md','TASKS.md','instructions.md','input.txt'):
            (second/name).write_bytes((self.root/name).read_bytes())
        b.prepare(second,task_id='T-001',run_id='second',owner='示例主持者',workspace=self.work,
                  inputs=['input.txt'],writes=['result.txt'],instructions='instructions.md',model='test-only',timeout=10)
        results=[]
        worker=threading.Thread(target=lambda:results.append(self.run_fake('slow')))
        worker.start()
        for _ in range(100):
            if b.status(self.root,'T-001-a01')['phase']=='running':break
            time.sleep(.02)
        try:
            with self.assertRaisesRegex(ValueError,'工作副本已被'):
                b.execute(second,'second','示例主持者',command=[sys.executable,str(self.fake)])
        finally:
            b.cancel(self.root,'T-001-a01');worker.join(12)
        self.assertFalse(worker.is_alive())

    def test_parallel_profile_is_explicit_and_session_scoped(self):
        self.prepare(parallel=True)
        data=b.read_dispatch(self.root,'T-001-a01')[1]
        with patch.object(b.shutil,'which',return_value='claude.exe'):
            argv=b.claude_command(data)
        self.assertNotIn('--bare',argv)
        self.assertEqual(argv[argv.index('--setting-sources')+1],'')
        settings=json.loads(argv[argv.index('--settings')+1])
        self.assertTrue(settings['disableAllHooks'])
        self.assertFalse(settings['autoMemoryEnabled'])
        workers=json.loads(argv[argv.index('--agents')+1])
        self.assertFalse(workers['module-worker']['background'])
        self.assertNotIn('Agent',workers['module-worker']['tools'])

    def test_adapter_profile_change_requires_new_session(self):
        self.prepare();self.run_fake()
        with self.assertRaisesRegex(ValueError,'不同CLI配置'):
            self.prepare(run_id='repair',resume_run='T-001-a01',parallel=True)

    def test_resume_rejects_wrong_returned_session(self):
        self.prepare();self.run_fake()
        path=b.run_folder(self.root,'T-001-a01')/'runtime.json'
        state=b.infra.read_json(path);state['session_id']='different-session'
        b.atomic_json(path,state)
        with self.assertRaisesRegex(ValueError,'会话ID与派发'):
            self.prepare(run_id='repair',resume_run='T-001-a01')

    @unittest.skipUnless(os.name=='nt','Windows sharing violation')
    def test_atomic_record_retries_transient_reader(self):
        path=self.base/'atomic.json';real=b.os.replace;calls=[]
        def rename(source,target):
            calls.append(1)
            if len(calls)==1:raise PermissionError('reader handle')
            return real(source,target)
        with patch.object(b.os,'replace',side_effect=rename):
            b.atomic_json(path,{'phase':'prepared'})
        self.assertEqual(b.infra.read_json(path),{'phase':'prepared'})
        self.assertEqual(len(calls),2)


if __name__=='__main__':unittest.main()
