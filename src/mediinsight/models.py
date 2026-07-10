from dataclasses import dataclass, field
from typing import Any


@dataclass
class Channel:
    name: str
    type: str
    url: str


@dataclass
class RawReview:
    channel: str
    text: str
    rating: int | None = None
    skin_type: str | None = None
    usage_period: str | None = None
    url: str | None = None
    captured_at: str | None = None
    provenance: str = "user_or_browser_verified_review"


@dataclass
class Evidence:
    id: str
    source: str
    type: str
    text: str
    url: str | None = None
    rating: int | None = None
    skin_type: str | None = None
    usage_period: str | None = None
    captured_at: str | None = None
    provenance: str = "unknown"
    tags: list[str] = field(default_factory=list)
    signals: dict[str, Any] = field(default_factory=dict)


@dataclass
class Insight:
    id: str
    title: str
    summary: str
    evidence_ids: list[str]
    confidence: str
    action: str


@dataclass
class ContentFrame:
    title: str
    body: str
    evidence_ids: list[str]
    scene: str = ""
    speaker: str = ""
    emotion: str = ""


@dataclass
class Carousel:
    id: str
    theme: str
    frames: list[ContentFrame]


@dataclass
class ComplianceFinding:
    claim_id: str
    phrase: str
    revised_phrase: str
    severity: str
    reason: str
    safer_rewrite: str
    rule_id: str
    source: str
    citation: str | None = None
