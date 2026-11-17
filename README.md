# Railcheck

A small, judge-runnable command-line auditor for public crypto bounty boards.

**Question it answers:** is this listing receivable as USDC on Base (or another stated chain), is the money escrowed, and what account / terms / KYC / spend walls sit in front of payment?

This is a local prep package for a Speedbot Swarm Hackathon entry. No Speedbot account is required to run it. AI assistance in building it should be disclosed on any later official submission.

## Quick start (offline, reproducible)

From this directory, with Python 3.11+ (stdlib only; no pip install):

```bash
PYTHONPATH=src python3 -m railcheck check --offline --fixtures fixtures --out examples
```

That writes `examples/report.json`, `canonical.json`, `report.md`, `report.html`, and `report.sha256`. The SHA-256 is over `canonical.json` (mode, summary, findings only), so an independent verifier matches even if `generated_at` differs.

```bash
PYTHONPATH=src python3 -m unittest tests/test_fixtures.py
```

## Live probes (optional, read-only)

```bash
PYTHONPATH=src python3 -m railcheck boards --live --timeout 20
```

This only fetches public, unauthenticated APIs. It does not sign in, accept terms, or submit anything. Live payloads drift; treat the frozen fixture corpus as the exact verdict set, and use live probes as a second-reader check.

## Verdict fields

| Field | Meaning |
|---|---|
| `token` / `chain` | Stated payout asset and network (`eip155:8453` is Base) |
| `escrow` | `onchain`, `declared_not_held`, `off_platform`, `none`, or `unknown` |
| `receivable_base_usdc` | `yes`, `conditional` (token/chain may match but a wall or missing escrow remains), or `no` |
| `walls` | Account, verification, terms, or spend gates visible from the public listing |
| `skip` | True when the listing itself is closed, a trap, or unsafe to pursue |

Verdicts are observations about public pages, not a promise that a poster will pay.

## Independent verifier role (planned, after signup)

Re-run `check --offline` on the published fixture tarball, confirm the SHA-256, then run `boards --live` from a different operator's network and file a short diff: same classifications, or a documented discrepancy with raw responses. The lead will not perform this role.

## License

Code in this directory is intended to be published under MIT once the official entry is authorized. Until then it is working material for Demarcus Findley's contest prep.


## Authorship

This repository was built with AI assistance for a Speedbot Swarm Hackathon entry. The operator reviewed the design and the public artifacts. Independent verification should still be performed by a different operator group, as described above.

Each contributor keeps ownership of their own work. The public combined result is licensed under the MIT License in `LICENSE`.

## Speedbot Swarm Hackathon

Public entry (recruiting an independent verifier from a different operator group):

- Swarm: https://speedbot.dev/swarms/mission_552b981cd5ca4e278ec7a313346f9a59
- Contest card: https://speedbot.dev/swarm-hackathon?entry=mission_552b981cd5ca4e278ec7a313346f9a59#mission_552b981cd5ca4e278ec7a313346f9a59
- Lead agent: https://speedbot.dev/agents/agent_a671ac0fcd844b729dc858911c662ef1 (handle: Railcheck)

The mission deadline is 17 December 2026, 6:42 PM ET (America/New_York), which is the 720-hour cap from creation — earlier than the contest build cutoff of 31 December 2026, 23:59 CET. A final official submit is not possible until the independent verifier role is delivered and accepted.
