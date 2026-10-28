import importlib.util, json, tempfile, unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
MODULE=HERE.parent/"50_Skill"/"bounded-development"/"scripts"/"run_bounded.py"
if not MODULE.exists(): MODULE=HERE.parent/"skills"/"bounded-development"/"scripts"/"run_bounded.py"
spec=importlib.util.spec_from_file_location("bounded",MODULE)
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name)
        self.plan=self.root/"plan.json"; self.state=self.root/"state.json"; self.report=self.root/"report.json"
    def tearDown(self): self.temp.cleanup()
    def make(self,code="print('ok')",timeout=3,budget=None):
        self.plan.write_text(json.dumps({"commands":[{"id":"case-a","argv":["{python}","-c",code],"timeout":timeout}],"budget":budget or {"max_rounds":3,"total_seconds":10}}),encoding="utf-8")
    def run_plan(self): return m.execute(self.plan,self.state,self.report)
    def test_pass_keeps_human_release_gate(self):
        self.make(); r,code=self.run_plan(); self.assertEqual(code,0); self.assertEqual(r["release"],"human_review_required")
    def test_repeated_failure_stops(self):
        self.make("raise SystemExit(1)")
        self.assertEqual(self.run_plan()[0]["status"],"failed")
        self.assertEqual(self.run_plan()[0]["reason"],"repeated_failure")
        r,code=self.run_plan(); self.assertEqual(r["status"],"stopped"); self.assertEqual(r["state"]["rounds"],2)
    def test_round_cap(self):
        self.make(budget={"max_rounds":20,"total_seconds":10})
        for _ in range(3): self.assertEqual(self.run_plan()[1],0)
        self.assertEqual(self.run_plan()[0]["reason"],"round_budget_exhausted")
    def test_timeout(self):
        self.make("import time; time.sleep(3)",timeout=.15)
        self.assertEqual(self.run_plan()[0]["results"][0]["exit_code"],124)
    def test_changed_plan_cannot_reset_budget(self):
        self.make(); self.run_plan(); self.make("print('changed')")
        with self.assertRaises(ValueError): self.run_plan()
    def test_time_budget_stops(self):
        self.make()
        r,code=self.run_plan(); s=json.loads(self.state.read_text()); s["seconds"]=10; self.state.write_text(json.dumps(s))
        self.assertEqual(self.run_plan()[0]["reason"],"time_budget_exhausted")
if __name__=="__main__": unittest.main(verbosity=2)
