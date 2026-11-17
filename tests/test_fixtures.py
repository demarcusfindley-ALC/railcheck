import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from railcheck.analyze import analyze_fixture_dir, summarize  # noqa: E402
from railcheck.models import Report  # noqa: E402
from railcheck.render import to_html, to_markdown  # noqa: E402
from railcheck.cli import canonical_bytes  # noqa: E402
import hashlib  # noqa: E402


class FixtureCorpusTests(unittest.TestCase):
    def setUp(self):
        self.findings = analyze_fixture_dir(ROOT / "fixtures")

    def test_all_fixtures_produce_findings(self):
        boards = {f.board for f in self.findings}
        self.assertEqual(
            boards,
            {"bountycaster", "basebounty", "githubbounties", "frantic", "opire", "musedin", "poidh"},
        )
        self.assertGreaterEqual(len(self.findings), 7)

    def test_empty_boards_are_not_receivable_yes(self):
        empty = [f for f in self.findings if f.board in {"bountycaster", "basebounty"}]
        self.assertTrue(empty)
        for f in empty:
            self.assertEqual(f.receivable_base_usdc, "no")

    def test_opire_is_off_platform_not_base_usdc(self):
        opire = [f for f in self.findings if f.board == "opire"]
        self.assertGreaterEqual(len(opire), 3)
        for f in opire:
            self.assertEqual(f.receivable_base_usdc, "no")
            self.assertEqual(f.escrow, "off_platform")
        self.assertTrue(any(f.skip and "captcha" in (f.notes or "").lower() or "hcapcha" in f.title.lower() for f in opire))

    def test_poidh_pays_eth_not_usdc(self):
        poidh = [f for f in self.findings if f.board == "poidh"]
        self.assertEqual(len(poidh), 1)
        self.assertEqual(poidh[0].token, "ETH")
        self.assertEqual(poidh[0].receivable_base_usdc, "no")
        self.assertEqual(poidh[0].escrow, "onchain")

    def test_musedin_is_declared_not_escrowed(self):
        m = [f for f in self.findings if f.board == "musedin"][0]
        self.assertEqual(m.escrow, "declared_not_held")
        self.assertEqual(m.receivable_base_usdc, "conditional")
        self.assertIn("paid_agent_verification_via_card", m.walls)

    def test_frantic_rebate_is_pay_to_play(self):
        f = [x for x in self.findings if x.board == "frantic"][0]
        self.assertIn("fund_a_bounty_to_earn_rebate", f.walls)
        self.assertEqual(f.chain, "eip155:8453")

    def test_only_funded_githubbounties_are_conditional(self):
        rows = [f for f in self.findings if f.board == "githubbounties"]
        funded = [f for f in rows if "funded" in f.title and "settled" not in f.title]
        settled = [f for f in rows if "settled" in f.title]
        self.assertEqual(len(funded), 1)
        self.assertEqual(funded[0].receivable_base_usdc, "conditional")
        self.assertTrue(all(f.receivable_base_usdc == "no" for f in settled))

    def test_summary_and_render(self):
        summary = summarize(self.findings)
        self.assertEqual(summary["total"], len(self.findings))
        report = Report(generated_at="2026-11-17T18:24:00-05:00", mode="offline", findings=self.findings, summary=summary)
        md = to_markdown(report)
        html = to_html(report)
        self.assertIn("Railcheck report", md)
        self.assertIn("<table>", html)
        json.dumps(report.to_dict())  # must be serializable

    def test_canonical_digest_is_stable(self):
        a = Report(generated_at="2026-11-17T18:00:00-05:00", mode="offline", findings=self.findings, summary=summarize(self.findings))
        b = Report(generated_at="2026-11-17T19:00:00-05:00", mode="offline", findings=self.findings, summary=summarize(self.findings))
        da = hashlib.sha256(canonical_bytes(a)).hexdigest()
        db = hashlib.sha256(canonical_bytes(b)).hexdigest()
        self.assertEqual(da, db)
        self.assertEqual(len(da), 64)


if __name__ == "__main__":
    unittest.main()
