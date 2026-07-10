from __future__ import annotations

from pathlib import Path
from collections import defaultdict
import html
import json

from .models import ComplianceFinding, Evidence, Insight
from .utils import ensure_dir


def write_report(
    path: Path,
    project: str,
    product_name: str,
    evidence: list[Evidence],
    insights: list[Insight],
    metrics: dict,
) -> None:
    ensure_dir(path.parent)
    reviews = [item for item in evidence if item.type == "customer_review"]
    channel_names = list(metrics.get("channel_counts", {}).keys())
    top_skin = top_count(metrics.get("skin_type_counts", {}))
    top_period = top_count(metrics.get("usage_period_counts", {}))
    top_positive = top_count(metrics.get("positive_counts", {}))
    top_friction = top_count(metrics.get("friction_counts", {}))
    quality = "활용 가능" if len(reviews) >= 10 and len(channel_names) >= 2 else "추가 수집 권장"
    lines = [
        f"# 메디테라피 고객 리뷰 인사이트 보고서",
        "",
        f"> 분석 제품: **{product_name}**  ",
        f"> 분석 프로젝트: {project}  ",
        f"> 데이터 상태: **{quality}**",
        "",
        "## 한눈에 보는 결과",
        "",
        "| 확인 항목 | 결과 | 이렇게 해석하세요 |",
        "|---|---:|---|",
        f"| 분석 리뷰 | {len(reviews)}건 | {len(channel_names)}개 공개 채널의 리뷰를 함께 봤습니다. |",
        f"| 재구매 신호 | {metrics.get('repurchase_count', 0)}건 | 효과 보장보다 반복 사용 경험을 보여주는 근거입니다. |",
        f"| 많이 언급된 피부 타입 | {display_count(top_skin)} | 명시적으로 피부 타입을 밝힌 리뷰만 집계했습니다. |",
        f"| 많이 확인된 사용 기간 | {display_count(top_period)} | 즉각적인 효과를 단정하지 않고 사용 시점을 설명할 수 있습니다. |",
        f"| 자주 보인 만족 표현 | {display_count(top_positive)} | 고객이 사용 과정에서 긍정적으로 표현한 단어입니다. |",
        f"| 자주 보인 불편 표현 | {display_count(top_friction)} | 사용법 콘텐츠에서 먼저 설명하면 좋은 지점입니다. |",
        "",
        "### 결론부터 말하면",
        "",
        summary_sentence(product_name, len(reviews), len(channel_names), metrics),
        "",
        "## 고객 관점에서 답한 네 가지 질문",
        "",
        f"### 1. 누가 관심을 보였나요?\n\n{audience_sentence(top_skin, len(reviews))}",
        "",
        f"### 2. 언제 사용했나요?\n\n{period_sentence(top_period)}",
        "",
        f"### 3. 왜 만족했나요?\n\n{positive_sentence(top_positive, metrics.get('repurchase_count', 0))}",
        "",
        f"### 4. 무엇이 불편했나요?\n\n{friction_sentence(top_friction)}",
        "",
        "## 핵심 인사이트와 실행안",
        "",
    ]
    for insight in insights:
        lines.extend(
            [
                f"### {insight.title}",
                "",
                insight.summary,
                "",
                f"- **권장 실행:** {insight.action}",
                f"- **근거 리뷰:** {len(insight.evidence_ids)}건",
                f"- **신뢰 수준:** {confidence_ko(insight.confidence)}",
                "",
            ]
        )

    lines.extend(
        [
            "## 이번 콘텐츠 제작 방향",
            "",
            "1. **처음 시작하는 루틴:** 새 제품을 망설이는 고객이 후기를 확인하고 천천히 루틴에 넣는 이야기",
            "2. **아침 메이크업 루틴:** 화장 전 사용량과 흡수 시간을 찾아가는 이야기",
            "3. **재구매 판단:** 여러 채널의 사용 기간·피부 타입을 비교하고 내 피부 기준으로 결정하는 이야기",
            "4. **제품 소개:** 과장된 효과 대신 공개 리뷰에서 확인한 루틴 경험과 개인차 고지를 함께 제시",
            "",
            "## 데이터 출처",
            "",
        ]
    )
    grouped = defaultdict(list)
    for item in evidence:
        if item.type == "customer_review":
            grouped[item.source].append(item)
    for source, items in grouped.items():
        sample_url = next((item.url for item in items if item.url), None)
        link = f" · [공개 원문 확인]({sample_url})" if sample_url else ""
        lines.append(f"- **{source}**: {len(items)}건{link}")
    lines.extend(
        [
            "",
            "## 읽을 때 주의할 점",
            "",
            "- 리뷰는 고객 개인의 사용 경험이며 제품 효과를 보장하지 않습니다.",
            "- 피부 타입과 사용 기간은 리뷰에 명시된 경우만 집계했습니다.",
            "- 공개 페이지 구조나 접근 정책이 바뀌면 수집량이 달라질 수 있습니다.",
            "- 법률 검수는 게시 전 위험 표현을 줄이기 위한 예비 검토이며 법률 자문을 대신하지 않습니다.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def top_count(counts: dict) -> tuple[str, int] | None:
    return max(counts.items(), key=lambda item: item[1]) if counts else None


def display_count(value: tuple[str, int] | None) -> str:
    return f"{value[0]} {value[1]}건" if value else "확인 가능한 정보 부족"


def summary_sentence(product_name: str, reviews: int, channels: int, metrics: dict) -> str:
    return (
        f"{product_name}은 공개 채널 {channels}곳의 리뷰 {reviews}건에서 사용 기간과 루틴 맥락이 확인됐습니다. "
        f"재구매 신호는 {metrics.get('repurchase_count', 0)}건이었으며, 광고 문구는 빠른 효과를 약속하기보다 "
        "고객이 언제 어떻게 사용했는지를 보여주는 방향이 더 적합합니다."
    )


def audience_sentence(top_skin, review_count: int) -> str:
    if not top_skin:
        return f"리뷰 {review_count}건은 확인했지만 피부 타입을 명시한 사례가 충분하지 않아 특정 고객군으로 단정하지 않았습니다."
    return f"피부 타입을 직접 밝힌 리뷰 중 **{top_skin[0]}** 언급이 {top_skin[1]}건으로 가장 많았습니다. 다른 피부 타입에도 같은 결과가 난다고 확대 해석하면 안 됩니다."


def period_sentence(top_period) -> str:
    if not top_period:
        return "사용 기간을 명시한 리뷰가 적어 효과 시점을 계산하지 않았습니다."
    return f"사용 기간 표현 중 **{top_period[0]}**가 {top_period[1]}건으로 가장 많이 확인됐습니다. 이는 효과 발생 시점이 아니라 고객이 후기를 남긴 사용 맥락입니다."


def positive_sentence(top_positive, repurchase_count: int) -> str:
    positive = f"**{top_positive[0]}** 관련 표현이 {top_positive[1]}건으로 가장 자주 보였습니다." if top_positive else "특정 만족 표현이 뚜렷하게 반복되지는 않았습니다."
    return f"{positive} 재구매 의향이나 반복 구매 신호는 {repurchase_count}건이었습니다."


def friction_sentence(top_friction) -> str:
    if not top_friction:
        return "반복적으로 나타난 불편 표현이 많지 않았습니다. 그래도 사용량과 사용 순서는 제품 안내에 포함하는 편이 안전합니다."
    return f"**{top_friction[0]}** 관련 표현이 {top_friction[1]}건 확인됐습니다. 제품 결함으로 단정하기보다 사용량·시간대·함께 쓴 제품을 설명하는 콘텐츠로 대응하는 것이 좋습니다."


def confidence_ko(value: str) -> str:
    return {"high": "높음", "medium": "보통", "low": "낮음"}.get(value, value)


def write_compliance_report(path: Path, findings: list[ComplianceFinding]) -> None:
    ensure_dir(path.parent)
    lines = [
        "# Cosmetic Advertising Compliance Review",
        "",
        "본 문서는 생성된 인스타그램 카드 문구와 제품 홍보 문구에 대한 예비 검수 결과입니다.",
        "Law MCP가 연결된 환경에서는 공식 법령/가이드 조회 결과를 추가 근거로 보강하세요.",
        "",
    ]
    if not findings:
        lines.extend(["## Result", "", "위험 표현이 발견되지 않았습니다.", ""])
    else:
        lines.extend(["## Findings", ""])
        for finding in findings:
            lines.extend(
                [
                    f"### {finding.severity.upper()} / {finding.rule_id}",
                    "",
                    f"- Phrase: `{finding.phrase}`",
                    f"- Revised: `{finding.revised_phrase}`",
                    f"- Reason: {finding.reason}",
                    f"- Safer rewrite: {finding.safer_rewrite}",
                    f"- Source: {finding.source}",
                    f"- Citation: {finding.citation or '공식 근거 미연결'}",
                    "",
                ]
            )
    lines.extend(
        [
            "## Required Human Review",
            "",
            "- 최종 게시 전 실제 제품 임상/시험 자료와 문구가 일치하는지 확인하세요.",
            "- 기능성 화장품 표현은 신고/심사 범위와 맞는지 확인하세요.",
            "- 이미지 내부 문구도 동일한 기준으로 검토하세요.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_html_report(
    path: Path,
    project: str,
    product_name: str,
    evidence: list[Evidence],
    insights: list[Insight],
    metrics: dict,
    findings: list[ComplianceFinding],
) -> None:
    ensure_dir(path.parent)
    reviews = [item for item in evidence if item.type == "customer_review"]
    channels = list(metrics.get("channel_counts", {}).keys())
    review_rows = [
        {
            "id": item.id,
            "source": item.source,
            "text": item.text,
            "rating": item.rating,
            "skin_type": item.skin_type or ", ".join(item.signals.get("skin_types", [])),
            "usage_period": item.usage_period or ", ".join(item.signals.get("usage_periods", [])),
            "url": item.url,
            "provenance": item.provenance,
        }
        for item in reviews
    ]
    embedded = json.dumps(review_rows, ensure_ascii=False).replace("<", "\\u003c")
    insight_html = "".join(
        f'''<article class="insight">
          <div class="insight-top"><span class="confidence">신뢰 수준 {html.escape(confidence_ko(item.confidence))}</span><span>{len(item.evidence_ids)}건 근거</span></div>
          <h3>{html.escape(item.title)}</h3>
          <p>{html.escape(item.summary)}</p>
          <strong>실행안</strong><p>{html.escape(item.action)}</p>
        </article>'''
        for item in insights
    )
    finding_html = "".join(
        f'''<tr><td><span class="risk {html.escape(item.severity)}">{html.escape(severity_ko(item.severity))}</span></td>
        <td>{html.escape(item.phrase)}</td><td>{html.escape(item.revised_phrase)}</td>
        <td>{html.escape(item.reason)}</td><td>{citation_link(item.citation)}</td></tr>'''
        for item in findings
    ) or '<tr><td colspan="5">위험 표현이 발견되지 않았습니다.</td></tr>'
    quality = "활용 가능" if len(reviews) >= 10 and len(channels) >= 2 else "추가 수집 권장"
    top_skin = top_count(metrics.get("skin_type_counts", {}))
    top_period = top_count(metrics.get("usage_period_counts", {}))
    top_friction = top_count(metrics.get("friction_counts", {}))
    document = f'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(product_name)} 고객 리뷰 인사이트</title>
<style>
:root{{--ink:#172d29;--muted:#61736f;--paper:#fffdf9;--line:#d7dfdc;--green:#dcebe5;--coral:#ff7058;--yellow:#f7d66d;--blue:#8bb7d8}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--paper);color:var(--ink);font-family:Arial,"Apple SD Gothic Neo","Noto Sans KR",sans-serif;letter-spacing:0}}
header{{background:#17342f;color:white;padding:42px 6vw 34px}} header p{{color:#dcebe5;max-width:850px;line-height:1.7}} h1{{font-size:38px;margin:0 0 12px}} h2{{font-size:27px;margin:0 0 22px}} h3{{font-size:20px;margin:10px 0}} p{{line-height:1.7}}
nav{{position:sticky;top:0;z-index:5;display:flex;gap:6px;padding:10px 6vw;background:white;border-bottom:1px solid var(--line);overflow:auto}}
button{{border:0;background:white;padding:11px 15px;font-weight:700;color:var(--muted);cursor:pointer}} button.active{{background:var(--ink);color:white}} main{{max-width:1180px;margin:auto;padding:34px 24px 70px}}
.view{{display:none}} .view.active{{display:block}} .kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:34px}} .kpi{{border:1px solid var(--line);border-top:6px solid var(--coral);padding:18px;min-height:130px}} .kpi:nth-child(2){{border-top-color:var(--yellow)}} .kpi:nth-child(3){{border-top-color:var(--blue)}} .kpi:nth-child(4){{border-top-color:#72a98e}} .kpi b{{font-size:31px;display:block;margin-top:13px}} .kpi span{{color:var(--muted)}}
.answer{{border-left:6px solid var(--coral);padding:18px 22px;background:#fff5ef;margin:24px 0}} .insights{{display:grid;grid-template-columns:repeat(2,1fr);gap:16px}} .insight{{border:1px solid var(--line);padding:22px}} .insight-top{{display:flex;justify-content:space-between;color:var(--muted);font-size:14px}} .confidence{{color:#a33d2d}}
.filters{{display:flex;gap:10px;margin-bottom:18px}} input,select{{padding:12px;border:1px solid #aebbb7;background:white;min-width:220px;font-size:15px}} .review-list{{display:grid;gap:10px}} details{{border:1px solid var(--line);padding:15px;background:white}} summary{{cursor:pointer;font-weight:700}} .meta{{color:var(--muted);font-size:14px;margin-top:8px}}
table{{width:100%;border-collapse:collapse;background:white}} th,td{{padding:13px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}} th{{background:#eef4f1}} .risk{{display:inline-block;padding:4px 8px;font-weight:700}} .risk.high{{background:#ffd7d0;color:#8e2618}} .risk.medium{{background:#fff0b8;color:#6d5200}}
.content-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:18px}} .content-grid figure{{margin:0}} .content-grid img{{display:block;width:100%;border:1px solid var(--line)}} figcaption{{padding:10px 0;color:var(--muted)}} footer{{border-top:1px solid var(--line);padding:24px 6vw;color:var(--muted)}}
@media(max-width:760px){{.kpis,.insights,.content-grid{{grid-template-columns:1fr}} .filters{{flex-direction:column}} input,select{{width:100%}} h1{{font-size:29px}} table{{font-size:13px}}}}
</style></head><body>
<header><h1>{html.escape(product_name)} 고객 리뷰 인사이트</h1><p>{html.escape(project)} · 공개 리뷰를 모아 고객의 사용 맥락을 분석하고, 콘텐츠와 광고 문구 검수까지 연결한 결과입니다.</p></header>
<nav><button class="tab active" data-view="summary">한눈에 보기</button><button class="tab" data-view="insights">인사이트</button><button class="tab" data-view="reviews">리뷰 탐색</button><button class="tab" data-view="compliance">문구 검수</button><button class="tab" data-view="content">생성 콘텐츠</button></nav>
<main>
<section id="summary" class="view active"><h2>한눈에 보는 결과</h2><div class="kpis">
<div class="kpi"><span>분석 리뷰</span><b>{len(reviews)}건</b><small>{len(channels)}개 채널 통합</small></div>
<div class="kpi"><span>데이터 상태</span><b>{quality}</b><small>리뷰 수와 채널 분산 기준</small></div>
<div class="kpi"><span>재구매 신호</span><b>{metrics.get('repurchase_count', 0)}건</b><small>반복 구매 관련 표현</small></div>
<div class="kpi"><span>문구 수정</span><b>{len(findings)}건</b><small>Law MCP 예비 검수</small></div></div>
<div class="answer"><h3>결론</h3><p>{html.escape(summary_sentence(product_name, len(reviews), len(channels), metrics))}</p></div>
<h2>고객 질문에 바로 답하면</h2><div class="insights">
<article class="insight"><h3>누가 관심을 보였나요?</h3><p>{html.escape(audience_sentence(top_skin, len(reviews)))}</p></article>
<article class="insight"><h3>언제 사용했나요?</h3><p>{html.escape(period_sentence(top_period))}</p></article>
<article class="insight"><h3>왜 만족했나요?</h3><p>{html.escape(positive_sentence(top_count(metrics.get('positive_counts', dict())), metrics.get('repurchase_count', 0)))}</p></article>
<article class="insight"><h3>무엇이 불편했나요?</h3><p>{html.escape(friction_sentence(top_friction))}</p></article></div></section>
<section id="insights" class="view"><h2>핵심 인사이트와 실행안</h2><div class="insights">{insight_html}</div></section>
<section id="reviews" class="view"><h2>수집 리뷰 탐색</h2><div class="filters"><select id="sourceFilter"><option value="">전체 채널</option>{''.join(f'<option>{html.escape(value)}</option>' for value in channels)}</select><input id="reviewSearch" placeholder="리뷰 내용 검색"></div><div id="reviewList" class="review-list"></div></section>
<section id="compliance" class="view"><h2>Law MCP 문구 검수</h2><p>생성된 컷툰 제목·대사·제품 소개 문구 전체를 검사한 예비 검수 결과입니다. 최종 법률 자문을 대신하지 않습니다.</p><table><thead><tr><th>위험도</th><th>원문</th><th>수정 문구</th><th>이유</th><th>근거</th></tr></thead><tbody>{finding_html}</tbody></table></section>
<section id="content" class="view"><h2>스토리텔링 콘텐츠</h2><div class="content-grid">
<figure><img src="../instagram/carousel_01.png" alt="처음 시작하는 PDRN 루틴 4컷"><figcaption>1. 처음 시작하는 루틴</figcaption></figure>
<figure><img src="../instagram/carousel_02.png" alt="화장 전 세럼 루틴 4컷"><figcaption>2. 아침 메이크업 루틴</figcaption></figure>
<figure><img src="../instagram/carousel_03.png" alt="재구매 판단 4컷"><figcaption>3. 재구매 판단</figcaption></figure>
<figure><img src="../instagram/product_ad.png" alt="제품 소개 이미지"><figcaption>4. 제품 소개</figcaption></figure></div></section>
</main><footer>공개 리뷰 기반 분석 · 개인차가 있을 수 있음 · 최종 게시 전 광고·법무 검토 필요</footer>
<script>
const reviews={embedded};
document.querySelectorAll('.tab').forEach(btn=>btn.onclick=()=>{{document.querySelectorAll('.tab,.view').forEach(el=>el.classList.remove('active'));btn.classList.add('active');document.getElementById(btn.dataset.view).classList.add('active')}});
function esc(s){{return String(s??'').replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]))}}
function renderReviews(){{const q=document.getElementById('reviewSearch').value.toLowerCase();const source=document.getElementById('sourceFilter').value;const rows=reviews.filter(r=>(!source||r.source===source)&&(!q||r.text.toLowerCase().includes(q)));document.getElementById('reviewList').innerHTML=rows.map(r=>`<details><summary>${{esc(r.source)}} · ${{esc(r.rating?`${{r.rating}}점`:'평점 미표시')}}</summary><p>${{esc(r.text)}}</p><div class="meta">피부 타입: ${{esc(r.skin_type||'명시 없음')}} · 사용 기간: ${{esc(r.usage_period||'명시 없음')}} · 수집 방식: ${{esc(r.provenance)}}</div>${{r.url?`<p><a href="${{esc(r.url)}}" target="_blank" rel="noreferrer">공개 원문 보기</a></p>`:''}}</details>`).join('')||'<p>조건에 맞는 리뷰가 없습니다.</p>'}}
document.getElementById('reviewSearch').oninput=renderReviews;document.getElementById('sourceFilter').onchange=renderReviews;renderReviews();
</script></body></html>'''
    path.write_text(document, encoding="utf-8")


def severity_ko(value: str) -> str:
    return {"high": "높음", "medium": "보통", "low": "낮음"}.get(value, value)


def citation_link(value: str | None) -> str:
    if not value:
        return "공식 근거 미연결"
    start = value.find("http")
    if start < 0:
        return html.escape(value)
    url = value[start:].rstrip(")")
    label = value[:start].strip().rstrip("(") or "공식 근거"
    return f'<a href="{html.escape(url)}" target="_blank" rel="noreferrer">{html.escape(label)}</a>'


def format_counts(counts: dict) -> str:
    if not counts:
        return "none"
    return ", ".join(f"{key} {value}" for key, value in counts.items())
