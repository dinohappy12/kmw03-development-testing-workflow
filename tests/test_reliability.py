import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
MODULE=HERE.parent/'50_Skill/bounded-development/scripts/run_bounded.py'
if not MODULE.exists(): MODULE=HERE.parent/'skills/bounded-development/scripts/run_bounded.py'
spec=importlib.util.spec_from_file_location('reliability',MODULE)
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
class ReliabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name)
        self.plan=self.root/'plan.json'; self.state=self.root/'state.json'; self.report=self.root/'report.json'
    def tearDown(self): self.temp.cleanup()
    def make(self,code="print('ok')",timeout=3,reason=None,budget=None):
        item=dict(id='case-a',argv=['{python}','-c',code],timeout=timeout)
        if reason is not None: item['timeout_reason']=reason
        self.plan.write_text(json.dumps(dict(commands=[item],budget=budget or dict(max_rounds=3,total_seconds=180))),encoding='utf8')
    def run_plan(self,**kw): return m.execute(self.plan,self.state,self.report,**kw)
    def state_data(self): return json.loads(self.state.read_text(encoding='utf8'))
    def fake(self,argv,cwd,timeout,env): return dict(exit_code=0,seconds=.01,output='mock; timeout selection only')
    def test_timeout_without_reason_capped_at_30(self):
        self.make(timeout=90)
        with patch.object(m,'run_command',side_effect=self.fake) as call: self.run_plan()
        self.assertEqual(call.call_args.args[2],30)
    def test_reason_allows_longer_timeout_within_remaining_budget(self):
        self.make(timeout=90,reason='Integration sample needs up to 90 seconds',budget=dict(max_rounds=3,total_seconds=60))
        with patch.object(m,'run_command',side_effect=self.fake) as call: self.run_plan()
        self.assertEqual(call.call_args.args[2],60)
        self.assertEqual(self.state_data()['history'][0]['results'][0]['timeout_reason'],'Integration sample needs up to 90 seconds')
    def test_blank_reason_does_not_extend_timeout(self):
        self.make(timeout=90,reason='  ')
        with patch.object(m,'run_command',side_effect=self.fake) as call: self.run_plan()
        self.assertEqual(call.call_args.args[2],30)
    def test_launch_error_saved_and_counts_as_failure(self):
        self.make(); data=json.loads(self.plan.read_text()); data['commands'][0]['argv']=['KMW03_missing_executable_70263']; self.plan.write_text(json.dumps(data))
        result,code=self.run_plan()
        self.assertEqual(result['status'],'failed'); self.assertEqual(code,1)
        self.assertEqual(result['results'][0]['error_type'],'launch_error')
        self.assertEqual(self.state_data()['rounds'],1); self.assertEqual(self.state_data()['failures']['case-a'],1)
        self.assertTrue(self.report.exists())
        self.assertEqual(self.run_plan()[0]['reason'],'repeated_failure')
    def test_state_saved_before_starting_command(self):
        self.make()
        def inspect(*args):
            data=self.state_data(); self.assertEqual(data['rounds'],1); self.assertEqual(data['in_progress']['command_id'],'case-a')
            self.assertEqual(json.loads(self.report.read_text())['status'],'running')
            return self.fake(*args)
        with patch.object(m,'run_command',side_effect=inspect): self.run_plan()
        self.assertIsNone(self.state_data()['in_progress'])
    def test_revision_preserves_time_rounds_failures(self):
        self.make('raise SystemExit(1)'); self.run_plan(); before=self.state_data()
        self.make()
        self.run_plan(revision_reason='Correct reproducible failure; same acceptance case')
        after=self.state_data(); self.assertEqual(after['rounds'],2); self.assertGreaterEqual(after['seconds'],before['seconds'])
        self.assertEqual(after['original_budget'],before['original_budget']); self.assertEqual(len(after['plan_revisions']),1)
        self.assertEqual(after['history'][0]['results'][0]['exit_code'],1)
    def test_revision_cannot_bypass_repeated_failure(self):
        self.make('raise SystemExit(1)'); self.run_plan(); self.run_plan(); self.make()
        result,code=self.run_plan(revision_reason='Try corrected command')
        self.assertEqual(result['reason'],'repeated_failure'); self.assertEqual(self.state_data()['rounds'],2)
    def test_revision_cannot_increase_original_total_budget(self):
        self.make(budget=dict(max_rounds=3,total_seconds=10)); self.run_plan(); self.make(budget=dict(max_rounds=3,total_seconds=180))
        with self.assertRaises(ValueError): self.run_plan(revision_reason='Changed command')
        self.assertEqual(self.state_data()['original_budget']['total_seconds'],10)
    def test_revision_cannot_rename_acceptance_case(self):
        self.make(); self.run_plan(); data=json.loads(self.plan.read_text()); data['commands'][0]['id']='renamed'; self.plan.write_text(json.dumps(data))
        with self.assertRaises(ValueError): self.run_plan(revision_reason='Rename case')
    def test_invalid_timeout_rejected_before_launch(self):
        for value in [0,-1,float('nan'),float('inf')]:
            self.make(timeout=value)
            with self.assertRaises(ValueError): self.run_plan()
        self.assertFalse(self.state.exists())
    def test_interrupted_run_is_not_silently_retried(self):
        self.make(); self.run_plan(); data=self.state_data(); data['in_progress']=dict(command_id='case-a'); self.state.write_text(json.dumps(data))
        result,code=self.run_plan(); self.assertEqual(result['reason'],'interrupted_run'); self.assertEqual(code,2)
if __name__=='__main__': unittest.main(verbosity=2)
