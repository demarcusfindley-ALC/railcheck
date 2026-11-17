from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Optional

Escrow = Literal["onchain", "declared_not_held", "off_platform", "none", "unknown"]
Receivable = Literal["yes", "no", "conditional", "unknown"]


@dataclass
class Finding:
    board: str
    source: str
    title: str
    url: Optional[str]
    token: Optional[str]
    chain: Optional[str]  # e.g. eip155:8453, offchain, unspecified
    amount: Optional[str]
    escrow: Escrow
    receivable_base_usdc: Receivable
    walls: list[str] = field(default_factory=list)
    notes: str = ""
    skip: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Report:
    generated_at: str
    mode: str  # offline | live
    findings: list[Finding]
    summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "mode": self.mode,
            "summary": self.summary,
            "findings": [f.to_dict() for f in self.findings],
        }
