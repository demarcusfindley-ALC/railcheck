from __future__ import annotations

import html
import json
from .models import Report


def to_markdown(report: Report) -> str:
    s = report.summary
    lines = [
        f"# Railcheck report ({report.mode})",
        "",
        f"Generated: {report.generated_at}",
        "",
        f"- Findings: {s.get('total')} (skipped {s.get('skipped')})",
        f"- Receivable as Base USDC: yes {s.get('receivable_base_usdc_yes')}, conditional {s.get('receivable_base_usdc_conditional')}, no {s.get('receivable_base_usdc_no')}",
        f"- On-chain escrow: {s.get('onchain_escrow')}",
        f"- Boards: {', '.join(s.get('boards') or [])}",
        "",
        "| Board | Title | Token | Chain | Escrow | Base USDC? | Walls |",
        "|---|---|---|---|---|---|---|",
    ]
    for f in report.findings:
        title = (f.title or "").replace("|", "\\|")
        walls = ", ".join(f.walls) if f.walls else "—"
        lines.append(
            f"| {f.board} | {title} | {f.token or '—'} | {f.chain or '—'} | {f.escrow} | {f.receivable_base_usdc} | {walls} |"
        )
    lines.append("")
    return "\n".join(lines)


def to_html(report: Report) -> str:
    md_table = to_markdown(report)
    # simple standalone page, no external assets
    rows = []
    for f in report.findings:
        rows.append(
            "<tr>"
            + "".join(
                f"<td>{html.escape(str(v) if v is not None else '—')}</td>"
                for v in (
                    f.board,
                    f.title,
                    f.token,
                    f.chain,
                    f.amount,
                    f.escrow,
                    f.receivable_base_usdc,
                    ", ".join(f.walls) or "—",
                    f.notes,
                )
            )
            + "</tr>"
        )
    s = report.summary
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<title>Railcheck report ({html.escape(report.mode)})</title>
<style>
body {{ font-family: ui-sans-serif, system-ui, sans-serif; margin: 2rem; color: #111; }}
table {{ border-collapse: collapse; width: 100%; font-size: 0.9rem; }}
th, td {{ border: 1px solid #ddd; padding: 0.4rem 0.5rem; vertical-align: top; }}
th {{ text-align: left; background: #f4f4f4; }}
code {{ background: #f4f4f4; padding: 0.1rem 0.3rem; }}
.meta {{ color: #444; }}
</style>
</head><body>
<h1>Railcheck report</h1>
<p class="meta">Mode: {html.escape(report.mode)} · Generated: {html.escape(report.generated_at)}</p>
<p>Findings {s.get('total')} · Base USDC yes/conditional/no: {s.get('receivable_base_usdc_yes')}/{s.get('receivable_base_usdc_conditional')}/{s.get('receivable_base_usdc_no')} · On-chain escrow {s.get('onchain_escrow')}</p>
<table>
<thead><tr><th>Board</th><th>Title</th><th>Token</th><th>Chain</th><th>Amount</th><th>Escrow</th><th>Base USDC?</th><th>Walls</th><th>Notes</th></tr></thead>
<tbody>
{''.join(rows)}
</tbody>
</table>
<p>Verdicts are from public, unauthenticated pages and fixtures. They are not payment promises. Source JSON is the canonical record.</p>
<pre>{html.escape(json.dumps(report.summary, indent=2))}</pre>
</body></html>
"""
