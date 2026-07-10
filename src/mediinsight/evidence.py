from __future__ import annotations

import re
import hashlib
from collections import Counter

from .models import Evidence, Insight


SKIN_TYPES = ["민감성", "지성", "건성", "복합성", "수부지"]
FRICTION_WORDS = ["끈적", "밀려", "답답", "건조", "자극", "따갑"]
POSITIVE_WORDS = ["매끈", "보습", "좋", "만족", "재구매", "오래", "편"]
ROUTINE_WORDS = ["아침", "저녁", "밤", "메이크업", "얇게", "루틴"]


def enrich_evidence(evidence: list[Evidence]) -> list[Evidence]:
    for item in evidence:
        text = item.text
        item.signals.update(
            {
                "skin_types": [skin for skin in SKIN_TYPES if skin in text or item.skin_type == skin],
                "usage_periods": extract_periods(text, item.usage_period),
                "frictions": [word for word in FRICTION_WORDS if word in text],
                "positives": [word for word in POSITIVE_WORDS if word in text],
                "routine_context": [word for word in ROUTINE_WORDS if word in text],
                "mentions_repurchase": any(
                    word in text for word in ["재구매", "또 샀", "두 번째", "한 통", "다 쓰"]
                ),
            }
        )
    return evidence


def deduplicate_reviews(evidence: list[Evidence]) -> tuple[list[Evidence], list[dict]]:
    unique: list[Evidence] = []
    seen: dict[str, str] = {}
    duplicates: list[dict] = []
    for item in evidence:
        if item.type != "customer_review":
            unique.append(item)
            continue
        normalized = re.sub(r"[^0-9A-Za-z가-힣]", "", item.text).lower()
        fingerprint = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        if fingerprint in seen:
            duplicates.append({"removed_id": item.id, "kept_id": seen[fingerprint]})
            continue
        seen[fingerprint] = item.id
        unique.append(item)
    return unique, duplicates


def extract_periods(text: str, explicit: str | None = None) -> list[str]:
    periods = []
    if explicit:
        periods.append(explicit)
    periods.extend(re.findall(r"\d+\s*(?:일|주|개월|달)", text))
    if "한 달" in text:
        periods.append("한 달")
    return sorted(set(periods))


def build_insights(evidence: list[Evidence], product_name: str) -> list[Insight]:
    reviews = [item for item in evidence if item.type == "customer_review"]
    repurchase = [item for item in reviews if item.signals.get("mentions_repurchase")]
    friction = [item for item in reviews if item.signals.get("frictions")]
    journey = [item for item in reviews if item.signals.get("usage_periods")]
    routine = [item for item in reviews if item.signals.get("routine_context")]

    confidence = confidence_for(len(reviews))
    insights: list[Insight] = []
    if journey:
        period_counts = Counter(period for item in journey for period in item.signals["usage_periods"])
        period_text = ", ".join(f"{period} {count}건" for period, count in period_counts.most_common(5))
        insights.append(
            Insight(
                id="insight-time-journey",
                title="효과 단정이 아니라 사용 기간별 경험을 콘텐츠화해야 합니다",
                summary=(
                    f"{product_name} 리뷰 {len(reviews)}건 중 사용 기간이 확인된 리뷰는 {len(journey)}건이며, "
                    f"주요 기간은 {period_text}입니다. 즉각 효과를 주장하지 않고 실제 사용 시점을 보여주는 근거로 활용할 수 있습니다."
                ),
                evidence_ids=[item.id for item in journey[:5]],
                confidence=confidence,
                action="4컷 캐러셀에서 '처음-적응-루틴-재구매' 흐름으로 구성합니다.",
            )
        )
    if friction:
        friction_counts = Counter(word for item in friction for word in item.signals["frictions"])
        friction_text = ", ".join(f"{word} {count}건" for word, count in friction_counts.most_common(5))
        insights.append(
            Insight(
                id="insight-usage-friction",
                title="사용량과 시간대 안내가 불만을 줄이는 핵심 메시지입니다",
                summary=(
                    f"사용 마찰이 확인된 리뷰는 {len(friction)}건이고 주요 표현은 {friction_text}입니다. "
                    "제품 결함으로 단정하지 말고 원문 사용 상황과 함께 안내 콘텐츠로 다뤄야 합니다."
                ),
                evidence_ids=[item.id for item in friction[:5]],
                confidence=confidence,
                action="콘텐츠 한 세트를 '낮/밤 사용법' 교육형으로 만듭니다.",
            )
        )
    if repurchase:
        insights.append(
            Insight(
                id="insight-repurchase",
                title="재구매 후기는 강한 판매 카피보다 신뢰형 증거로 써야 합니다",
                summary=(
                    f"재구매 신호가 확인된 리뷰는 전체 {len(reviews)}건 중 {len(repurchase)}건입니다. "
                    "효과 보장 대신 해당 리뷰의 피부 타입과 사용 기간을 함께 제시해야 합니다."
                ),
                evidence_ids=[item.id for item in repurchase[:5]],
                confidence=confidence,
                action="제품 홍보 이미지는 재구매 경험과 개인차 고지를 함께 배치합니다.",
            )
        )
    if routine:
        insights.append(
            Insight(
                id="insight-routine",
                title="제품 홍보보다 루틴 교육형 콘텐츠가 저장 가치가 높습니다",
                summary=(
                    "리뷰에는 아침, 밤, 메이크업 전, 얇게 바르기처럼 사용 상황이 드러납니다. "
                    "제품 장점만 말하기보다 상황별 사용법을 제시하는 것이 자연스럽습니다."
                ),
                evidence_ids=[item.id for item in routine[:5]],
                confidence=confidence,
                action="캐러셀 주제를 피부 고민 해결법이 아니라 사용 상황별 루틴으로 잡습니다.",
            )
        )

    if not insights:
        insights.append(
            Insight(
                id="insight-baseline",
                title="공개 데이터가 부족해도 근거 기반 초안은 생성할 수 있습니다",
                summary="수집된 공개 데이터가 적을 때는 사용자 제공 리뷰와 페이지 텍스트를 분리해 표시해야 합니다.",
                evidence_ids=[item.id for item in evidence[:5]],
                confidence="low",
                action="보고서 첫 페이지에 데이터 한계와 추가 수집이 필요한 채널을 명시합니다.",
            )
        )
    return insights


def build_metrics(evidence: list[Evidence]) -> dict:
    reviews = [item for item in evidence if item.type == "customer_review"]
    return {
        "review_count": len(reviews),
        "channel_counts": dict(Counter(item.source for item in reviews)),
        "skin_type_counts": dict(
            Counter(skin for item in reviews for skin in item.signals.get("skin_types", []))
        ),
        "usage_period_counts": dict(
            Counter(period for item in reviews for period in item.signals.get("usage_periods", []))
        ),
        "friction_counts": dict(
            Counter(word for item in reviews for word in item.signals.get("frictions", []))
        ),
        "positive_counts": dict(
            Counter(word for item in reviews for word in item.signals.get("positives", []))
        ),
        "repurchase_count": sum(
            1 for item in reviews if item.signals.get("mentions_repurchase")
        ),
    }


def confidence_for(review_count: int) -> str:
    if review_count >= 30:
        return "high"
    if review_count >= 10:
        return "medium"
    return "low"
