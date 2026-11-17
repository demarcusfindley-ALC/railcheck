from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .models import Finding


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def analyze_fixture(path: Path) -> list[Finding]:
    name = path.name
    data = load_json(path)
    source = data.get("source") or str(path)
    body = data.get("body")
    if name.startswith("bountycaster"):
        items = (body or {}).get("bounties") or []
        if not items:
            return [Finding(
                board="bountycaster",
                source=source,
                title="Open bounties list is empty",
                url="https://www.bountycaster.xyz/",
                token=None,
                chain=None,
                amount="0 open",
                escrow="unknown",
                receivable_base_usdc="no",
                walls=[],
                notes="GET /api/v1/bounties/open returned {\"bounties\":[]}.",
            )]
        out = []
        for b in items:
            out.append(Finding(
                board="bountycaster",
                source=source,
                title=str(b.get("title") or b),
                url=b.get("url"),
                token=str(b.get("token") or b.get("currency") or "unknown"),
                chain=str(b.get("chain") or "unknown"),
                amount=str(b.get("amount") or b.get("reward") or ""),
                escrow="unknown",
                receivable_base_usdc="unknown",
                walls=[],
            ))
        return out
    if name.startswith("basebounty"):
        count = (body or {}).get("count", len((body or {}).get("bounties") or []))
        return [Finding(
            board="basebounty",
            source=source,
            title=f"Open BaseBounty listings: {count}",
            url="https://www.basebounty.app",
            token="USDC" if count else None,
            chain="eip155:8453",
            amount=str(count),
            escrow="onchain" if count else "none",
            receivable_base_usdc="yes" if count else "no",
            walls=[],
            notes="Adapter 0x32c215908a46Eb5D34e4E5146c99891eD3014Fee on Base. Zero open at capture.",
        )]
    if name.startswith("githubbounties"):
        out = []
        for item in (body or {}).get("items") or []:
            status = item.get("status")
            funded = status == "funded"
            out.append(Finding(
                board="githubbounties",
                source=source,
                title=f"{item.get('repo')}#{item.get('issue')} {item.get('title') or ''} ({status})",
                url=f"https://github.com/{item.get('repo')}/issues/{item.get('issue')}",
                token="USDC",
                chain="unknown",  # board pays USDC; chain not stated in this compact fixture
                amount=str(item.get("totalFundedUsdc")),
                escrow="onchain" if funded else "none",
                receivable_base_usdc="conditional" if funded else "no",
                walls=["github_account"] if funded else [],
                notes="Only funded rows are claimable after a merged PR. Chain of payout is the board's, not verified from this compact fixture.",
            ))
        return out
    if name.startswith("frantic"):
        out = []
        for item in (body or {}).get("items") or []:
            meta = item.get("_frantic") or {}
            title = item.get("title") or ""
            pay_to_play = "on the house" in title.lower() or "back when it clears" in title.lower()
            out.append(Finding(
                board="frantic",
                source=source,
                title=title,
                url=item.get("url"),
                token="USDC",
                chain="eip155:8453",
                amount=f"{meta.get('price_usd')} USD; slots {meta.get('claim_slots')}",
                escrow="onchain",
                receivable_base_usdc="conditional",
                walls=["speedbot_or_frantic_agent_account", "email_or_github_verification"]
                + (["fund_a_bounty_to_earn_rebate"] if pay_to_play else []),
                notes="Frantic pays USDC on Base after judgment. This open listing is a rebate for funding work, not ordinary task pay.",
            ))
        return out
    if name.startswith("opire"):
        out = []
        for item in body or []:
            skip = bool(item.get("skip_reason"))
            closed = item.get("issue_state_later") == "CLOSED"
            out.append(Finding(
                board="opire",
                source=source,
                title=item.get("title") or "",
                url=item.get("url"),
                token="USD_CENT",
                chain="offchain",
                amount=str((item.get("pendingPrice") or {}).get("value", "")) + " USD cents",
                escrow="off_platform",
                receivable_base_usdc="no",
                walls=["opire_account", "off_platform_payment_arranged_by_parties"],
                notes=item.get("skip_reason") or (
                    "Opire docs: payments are arranged directly, not automatic on-chain USDC."
                    + (" Issue later observed CLOSED." if closed else "")
                ),
                skip=skip or closed,
            ))
        return out
    if name.startswith("musedin"):
        b = body or {}
        budget = b.get("budget") or {}
        on_base = (budget.get("network") or b.get("rail") or "").lower() in {"base", "usdc-base"}
        escrow = "declared_not_held"
        walls = ["musedin_account"]
        if b.get("verified_only"):
            walls.append("paid_agent_verification_via_card")
        return [Finding(
            board="musedin",
            source=source,
            title=b.get("title") or "",
            url=b.get("url"),
            token=budget.get("token") or "USDC",
            chain="eip155:8453" if on_base else str(budget.get("network")),
            amount=f"{budget.get('amount')} total, {budget.get('share')} per seat, {b.get('seats')} seats",
            escrow=escrow,
            receivable_base_usdc="conditional",
            walls=walls,
            notes=f"Not escrowed ({b.get('worker_budget')}). Poster paid-hire count={b.get('poster_paid')}. Applicants={b.get('applicants')}.",
        )]
    if name.startswith("poidh"):
        b = body or {}
        return [Finding(
            board="poidh",
            source=source,
            title=f"Base poidh in-progress: {b.get('in_progress_count')} (newest #{b.get('newest_frontend_id')})",
            url="https://poidh.xyz/base",
            token=b.get("payout_token") or "ETH",
            chain=b.get("payout_network") or "eip155:8453",
            amount="varies; ETH not USDC",
            escrow="onchain",
            receivable_base_usdc="no",
            walls=["onchain_claim_gas_in_base_eth"],
            notes=b.get("note") or "Pays ETH on Base, not USDC. Receivable to the same EOA, but token is ETH.",
        )]
    raise ValueError(f"No analyzer for fixture {path}")


def analyze_fixture_dir(directory: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in sorted(directory.glob("*.json")):
        findings.extend(analyze_fixture(path))
    return findings


def summarize(findings: Iterable[Finding]) -> dict:
    findings = list(findings)
    def count(pred):
        return sum(1 for f in findings if pred(f))
    return {
        "total": len(findings),
        "skipped": count(lambda f: f.skip),
        "receivable_base_usdc_yes": count(lambda f: f.receivable_base_usdc == "yes"),
        "receivable_base_usdc_conditional": count(lambda f: f.receivable_base_usdc == "conditional"),
        "receivable_base_usdc_no": count(lambda f: f.receivable_base_usdc == "no"),
        "onchain_escrow": count(lambda f: f.escrow == "onchain"),
        "boards": sorted({f.board for f in findings}),
    }
