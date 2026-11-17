from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .analyze import analyze_fixture_dir, summarize
from .models import Finding, Report
from .render import to_html, to_markdown

ET = ZoneInfo("America/New_York")
HERE = Path(__file__).resolve().parents[2]
DEFAULT_FIXTURES = HERE / "fixtures"


def now_et() -> str:
    return datetime.now(ET).isoformat()


def build_report(findings: list[Finding], mode: str) -> Report:
    return Report(generated_at=now_et(), mode=mode, findings=findings, summary=summarize(findings))


def canonical_bytes(report: Report) -> bytes:
    """SHA-256 input: mode, summary, and findings only. generated_at is excluded so independent re-runs match."""
    payload = {
        "mode": report.mode,
        "summary": report.summary,
        "findings": [f.to_dict() for f in report.findings],
    }
    return json.dumps(payload, indent=2, sort_keys=True).encode() + b"\n"


def write_outputs(report: Report, out_dir: Path) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    full = json.dumps(report.to_dict(), indent=2, sort_keys=False) + "\n"
    digest = hashlib.sha256(canonical_bytes(report)).hexdigest()
    (out_dir / "report.json").write_text(full)
    (out_dir / "canonical.json").write_text(canonical_bytes(report).decode())
    (out_dir / "report.md").write_text(to_markdown(report))
    (out_dir / "report.html").write_text(to_html(report))
    (out_dir / "report.sha256").write_text(digest + "  canonical.json\n")
    return {"dir": str(out_dir), "sha256": digest}


def cmd_check(args: argparse.Namespace) -> int:
    fixtures = Path(args.fixtures)
    if not fixtures.is_dir():
        print(f"fixtures directory not found: {fixtures}", file=sys.stderr)
        return 2
    findings = analyze_fixture_dir(fixtures)
    report = build_report(findings, "offline")
    dest = Path(args.out) if args.out else HERE / "examples"
    info = write_outputs(report, dest)
    print(to_markdown(report))
    print(f"sha256(canonical.json)={info['sha256']}")
    print(f"wrote {info['dir']}/report.{{json,md,html,sha256}}")
    return 0


def cmd_boards(args: argparse.Namespace) -> int:
    if not args.live:
        print("Pass --live to probe public APIs, or use `check --offline` for fixtures.", file=sys.stderr)
        return 2
    from .live import probe_all

    results = probe_all(timeout=args.timeout)
    rows = []
    for name, fr in results.items():
        rows.append({
            "board": name,
            "url": fr.url,
            "ok": fr.ok,
            "status": fr.status,
            "error": fr.error,
            "hint": (
                f"keys={list(fr.body)[:8]}" if isinstance(fr.body, dict)
                else f"list[{len(fr.body)}]" if isinstance(fr.body, list)
                else None
            ),
        })
    print(json.dumps({"generated_at": now_et(), "probes": rows}, indent=2))
    # Live classification of full payloads is intentionally fixture-first so
    # an independent verifier can reproduce exact verdicts without network drift.
    failed = [r for r in rows if not r["ok"]]
    return 0 if not failed else 1


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="railcheck", description="Audit whether public bounty listings are receivable as USDC on Base.")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("check", help="Classify the frozen fixture corpus (offline, reproducible).")
    c.add_argument("--offline", action="store_true", default=True, help="Use fixtures only (default).")
    c.add_argument("--fixtures", default=str(DEFAULT_FIXTURES), help="Fixture directory")
    c.add_argument("--out", default="", help="Output directory for report files")
    c.set_defaults(func=cmd_check)

    b = sub.add_parser("boards", help="Probe live public board APIs (read-only, no login).")
    b.add_argument("--live", action="store_true", help="Actually fetch public endpoints.")
    b.add_argument("--timeout", type=float, default=20.0)
    b.set_defaults(func=cmd_boards)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
