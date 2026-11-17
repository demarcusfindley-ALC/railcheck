"""Optional live probes of public, unauthenticated board APIs. Never signs in."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Optional

UA = "Railcheck/0.1 (+https://speedbot.dev/swarm-hackathon; public read-only probes)"


@dataclass
class LiveFetch:
    url: str
    ok: bool
    status: Optional[int]
    error: Optional[str]
    body: Any


def fetch_json(url: str, timeout: float = 20.0) -> LiveFetch:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json, text/json, */*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            status = getattr(resp, "status", 200)
            try:
                body = json.loads(raw.decode("utf-8", "replace"))
            except json.JSONDecodeError as e:
                return LiveFetch(url, False, status, f"non-json: {e}", raw[:300].decode("utf-8", "replace"))
            return LiveFetch(url, True, status, None, body)
    except urllib.error.HTTPError as e:
        return LiveFetch(url, False, e.code, str(e.reason), None)
    except Exception as e:  # noqa: BLE001 — surface network failures in the report
        return LiveFetch(url, False, None, f"{type(e).__name__}: {e}", None)


LIVE_ENDPOINTS = {
    "bountycaster": "https://www.bountycaster.xyz/api/v1/bounties/open",
    "basebounty": "https://www.basebounty.app/api/v1/bounties?status=open",
    "githubbounties": "https://githubbounties.xyz/api/v1/bounties?limit=100",
    "frantic": "https://gofrantic.com/feed.json",
    "opire": "https://api.opire.dev/rewards",
    "musedin": "https://musedin.com/api/roles",
    "poidh": "https://indexer.poidh.xyz/api/v1/bounties?chainId=8453&offset=1550&limit=20",
}


def probe_all(timeout: float = 20.0) -> dict[str, LiveFetch]:
    return {name: fetch_json(url, timeout=timeout) for name, url in LIVE_ENDPOINTS.items()}
