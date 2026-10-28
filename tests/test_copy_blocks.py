import importlib.util
import unittest
from pathlib import Path
path = Path(__file__).resolve().parents[1] / "50_Skill/bounded-development/scripts/check_copy_blocks.py"
if not path.exists(): path = Path(__file__).resolve().parents[1] / "skills/bounded-development/scripts/check_copy_blocks.py"
spec = importlib.util.spec_from_file_location("copy_checks", path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
FENCE = chr(96) * 3
def wrap(text):
    return FENCE + "text\n" + text + "\n" + FENCE
class CopyTests(unittest.TestCase):
    def test_bare_three_paragraphs_fail(self):
        self.assertEqual(m.check("A文\n\nB文\n\nC文", {"copy_block_count":3})["status"], "failed")
    def test_three_independent_blocks_pass(self):
        self.assertEqual(m.check("\n\n".join(wrap(x) for x in ["A文","B文","C文"]),
                                 {"copy_block_count":3})["status"], "passed")
    def test_writing_blocks_supported(self):
        text=':::writing{variant="social_post" id="54321"}\n文章\n:::'
        self.assertEqual(m.check(text, {"copy_block_count":1})["status"], "passed")
    def test_split_chain_rejected(self):
        text=wrap("商品介紹")+ "\n\n" + wrap("接龍\n1.\n2.\n3.")
        c={"required_same_block":[["商品介紹","接龍\n1.\n2.\n3."]],
           "first_block_suffix":"接龍\n1.\n2.\n3."}
        self.assertEqual(m.check(text,c)["status"],"failed")
    def test_line_main_and_chain_pass(self):
        text=wrap("商品介紹\n價格490元\n\n接龍\n1.\n2.\n3.")
        c={"copy_block_count":1,"required_same_block":[["商品介紹","價格490元","接龍"]],
           "first_block_suffix":"接龍\n1.\n2.\n3."}
        self.assertEqual(m.check(text,c)["status"],"passed")
    def test_wrong_url_rejected(self):
        self.assertEqual(m.check(wrap("訂購 https://example.com/wrong"),
            {"required_same_block":[["訂購","https://example.com/right"]]})["status"],"failed")
    def test_empty_contract_rejected(self):
        with self.assertRaises(ValueError):
            m.check(wrap("文章"), {})
    def test_unknown_rule_fails_closed(self):
        with self.assertRaises(ValueError):
            m.check(wrap("文章"), {"made_up_rule":True})
if __name__=="__main__":
    unittest.main(verbosity=2)
