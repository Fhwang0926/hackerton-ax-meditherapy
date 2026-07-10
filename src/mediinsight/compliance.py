from __future__ import annotations

import re

from .models import ComplianceFinding


RULES = [
    {
        "id": "COS-DRUG-001",
        "severity": "high",
        "patterns": ["치료", "완치", "피부염", "아토피", "여드름 치료"],
        "reason": "질병 치료 또는 의약품 오인 우려가 있는 표현입니다.",
        "rewrite": "피부 고민 케어 루틴에 도움을 줄 수 있음",
        "citation": "화장품법 제13조 제1항 제1호 (https://www.law.go.kr/lsLinkCommonInfo.do?lsJoLnkSeq=1025608537)",
    },
    {
        "id": "COS-GUARANTEE-002",
        "severity": "high",
        "patterns": [r"100\s*%\s*(?:개선|효과|회복|치료)", "무조건", "반드시", "즉시 개선", "기적"],
        "reason": "효과를 보증하거나 소비자를 오인시킬 수 있는 절대 표현입니다.",
        "rewrite": "개인차가 있을 수 있으며 고객 리뷰에서 긍정적인 경험이 확인됨",
        "citation": "화장품법 제13조 제1항 제4호 (https://www.law.go.kr/lsLinkCommonInfo.do?lsJoLnkSeq=1025608537)",
        "regex": True,
    },
    {
        "id": "COS-REGEN-003",
        "severity": "medium",
        "patterns": ["재생", "복구", "회복"],
        "reason": "피부 조직의 의학적 회복처럼 보일 수 있어 완화된 표현이 필요합니다.",
        "rewrite": "피부 컨디션 관리",
        "citation": "식약처 화장품 표시·광고 관리 지침 안내서-0086-07 (https://www.mfds.go.kr/brd/m_1060/view.do?seq=15700)",
    },
    {
        "id": "COS-TIME-004",
        "severity": "medium",
        "patterns": [r"\d+\s*(?:일|주|개월)\s*만에\s*(?:개선|효과|변화)"],
        "reason": "특정 기간 내 효과를 단정하는 표현은 근거 없이는 위험합니다.",
        "rewrite": "꾸준히 사용한 고객 리뷰에서 긍정적인 반응이 확인됨",
        "regex": True,
        "citation": "화장품법 제14조 표시·광고 내용의 실증 (https://www.law.go.kr/LSW/lsSideInfoP.do?docCls=jo&joNo=0014&lsiSeq=270323)",
    },
    {
        "id": "COS-RANK-005",
        "severity": "medium",
        "patterns": ["1위", "최고", "유일", "독보적"],
        "reason": "순위, 최상급, 배타적 표현은 객관적 근거가 필요합니다.",
        "rewrite": "많은 고객이 선택한",
        "citation": "화장품법 제13조 제1항 제4호 (https://www.law.go.kr/lsLinkCommonInfo.do?lsJoLnkSeq=1025608537)",
    },
    {
        "id": "COS-POLICY-006",
        "severity": "medium",
        "patterns": ["100% 환불", "환불보장", "환불 보장"],
        "reason": "환불 보장 문구는 적용 조건과 예외가 이미지 안에서 함께 확인되어야 합니다.",
        "rewrite": "환불 조건과 예외는 상세페이지 정책을 확인하세요",
        "citation": "화장품법 제13조 제1항 제4호 (https://www.law.go.kr/lsLinkCommonInfo.do?lsJoLnkSeq=1025608537)",
    },
]


def review_phrases(phrases: list[str], source: str = "built-in-rulebook") -> list[ComplianceFinding]:
    findings: list[ComplianceFinding] = []
    for phrase_index, phrase in enumerate(phrases, start=1):
        for rule in RULES:
            for pattern in rule["patterns"]:
                matched = re.search(pattern, phrase) if rule.get("regex") else pattern in phrase
                if matched:
                    findings.append(
                        ComplianceFinding(
                            claim_id=f"claim-{phrase_index:03d}-{rule['id']}",
                            phrase=phrase,
                            revised_phrase=_revise_by_rule(phrase, str(rule["id"])),
                            severity=str(rule["severity"]),
                            reason=str(rule["reason"]),
                            safer_rewrite=str(rule["rewrite"]),
                            rule_id=str(rule["id"]),
                            source=source,
                            citation=str(rule.get("citation")) if rule.get("citation") else None,
                        )
                    )
                    break
    return findings


def revise_phrase(phrase: str, findings: list[ComplianceFinding]) -> str:
    revised = phrase
    for finding in findings:
        if finding.phrase != phrase:
            continue
        if finding.source != "built-in-rulebook" and finding.revised_phrase:
            revised = finding.revised_phrase
            continue
        if finding.rule_id == "COS-DRUG-001":
            revised = re.sub("치료|완치|피부염|아토피|여드름 치료", "피부 고민 케어", revised)
        elif finding.rule_id == "COS-GUARANTEE-002":
            revised = re.sub(
                r"100\s*%\s*(?:개선|효과|회복|치료)|무조건|반드시|즉시 개선|기적",
                "고객 리뷰 기반",
                revised,
            )
        elif finding.rule_id == "COS-REGEN-003":
            revised = re.sub("재생|복구|회복", "피부 컨디션 관리", revised)
        elif finding.rule_id == "COS-TIME-004":
            revised = re.sub(
                r"\d+\s*(?:일|주|개월)\s*만에\s*(?:개선|효과|변화)",
                "꾸준한 사용 경험",
                revised,
            )
        elif finding.rule_id == "COS-RANK-005":
            revised = re.sub("1위|최고|유일|독보적", "고객 리뷰에서 확인된", revised)
        elif finding.rule_id == "COS-POLICY-006":
            revised = "환불 조건과 예외는 상세페이지 정책을 확인하세요"
    return revised


def load_external_findings(rows: list[dict]) -> list[ComplianceFinding]:
    findings = []
    for index, row in enumerate(rows, start=1):
        phrase = str(row.get("phrase", "")).strip()
        if not phrase:
            continue
        findings.append(
            ComplianceFinding(
                claim_id=str(row.get("claim_id", f"law-claim-{index:03d}")),
                phrase=phrase,
                revised_phrase=str(row.get("revised_phrase") or row.get("safer_rewrite") or phrase),
                severity=str(row.get("severity", "medium")),
                reason=str(row.get("reason", "Law MCP review")),
                safer_rewrite=str(row.get("safer_rewrite") or row.get("revised_phrase") or phrase),
                rule_id=str(row.get("rule_id", "LAW-MCP")),
                source=str(row.get("source", "mediinsight-law")),
                citation=row.get("citation"),
            )
        )
    return findings


def _revise_by_rule(phrase: str, rule_id: str) -> str:
    placeholder = ComplianceFinding(
        claim_id="preview",
        phrase=phrase,
        revised_phrase=phrase,
        severity="medium",
        reason="",
        safer_rewrite="",
        rule_id=rule_id,
        source="built-in-rulebook",
    )
    return revise_phrase(phrase, [placeholder])
