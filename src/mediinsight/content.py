from __future__ import annotations

import html
import base64
import mimetypes
import re
import shutil
import subprocess
import textwrap
from pathlib import Path

from .compliance import review_phrases, revise_phrase
from .models import Carousel, ContentFrame, Evidence, Insight
from .utils import ensure_dir


def build_carousels(
    insights: list[Insight],
    product_name: str,
    evidence: list[Evidence] | None = None,
) -> list[Carousel]:
    evidence = evidence or []
    journey_ids = evidence_ids_for(evidence, lambda item: bool(item.signals.get("usage_periods")))
    routine_ids = evidence_ids_for(evidence, lambda item: bool(item.signals.get("routine_context")))
    repurchase_ids = evidence_ids_for(evidence, lambda item: bool(item.signals.get("mentions_repurchase")))
    fallback_ids = [item.id for item in evidence if item.type == "customer_review"][:3]

    return [
        Carousel(
            id="carousel_01",
            theme="first-week-journey",
            frames=[
                ContentFrame(
                    title="새 세럼, 괜찮을까?",
                    body="피부가 예민해서 새 제품은 늘 망설여져.",
                    evidence_ids=journey_ids or fallback_ids,
                    scene="세면대 앞에서 새 세럼을 들고 걱정하는 직장인 여성",
                    speaker="고객",
                    emotion="걱정",
                ),
                ContentFrame(
                    title="먼저 후기를 확인",
                    body="나와 비슷한 피부의 사용 경험부터 찾아보자.",
                    evidence_ids=journey_ids or fallback_ids,
                    scene="휴대폰으로 여러 공개 리뷰를 비교하는 모습",
                    speaker="고객",
                    emotion="집중",
                ),
                ContentFrame(
                    title="루틴에 천천히",
                    body="아침·저녁 루틴에 소량부터 더해봤어.",
                    evidence_ids=routine_ids or journey_ids or fallback_ids,
                    scene="거울 앞에서 세럼을 소량 펴 바르는 모습",
                    speaker="고객",
                    emotion="차분",
                ),
                ContentFrame(
                    title="내 피부 반응 기록",
                    body="빠른 효과보다 꾸준한 사용 경험을 지켜보기로!",
                    evidence_ids=journey_ids or fallback_ids,
                    scene="달력에 루틴을 체크하며 미소 짓는 모습",
                    speaker="고객",
                    emotion="안도",
                ),
            ],
        ),
        Carousel(
            id="carousel_02",
            theme="morning-routine",
            frames=[
                ContentFrame(
                    title="화장 전에 써도 될까?",
                    body="세럼이 밀리면 아침 루틴이 꼬이는데…",
                    evidence_ids=routine_ids or fallback_ids,
                    scene="출근 준비 중 화장대 앞에서 시간을 확인하는 모습",
                    speaker="고객",
                    emotion="초조",
                ),
                ContentFrame(
                    title="리뷰에서 찾은 힌트",
                    body="가볍게 바르고 흡수시킨 경험이 보였어.",
                    evidence_ids=routine_ids or fallback_ids,
                    scene="휴대폰 후기 속 아침 루틴 순서를 확인하는 모습",
                    speaker="고객",
                    emotion="발견",
                ),
                ContentFrame(
                    title="얇게, 충분히 흡수",
                    body="오늘은 욕심내지 않고 한 겹만 발라볼게.",
                    evidence_ids=routine_ids or fallback_ids,
                    scene="손끝으로 세럼을 얇게 펴 바르는 클로즈업",
                    speaker="고객",
                    emotion="집중",
                ),
                ContentFrame(
                    title="아침 루틴 완성",
                    body="내 메이크업 루틴에 맞는 사용량을 찾았어.",
                    evidence_ids=routine_ids or fallback_ids,
                    scene="깔끔하게 준비를 마치고 현관을 나서는 모습",
                    speaker="고객",
                    emotion="만족",
                ),
            ],
        ),
        Carousel(
            id="carousel_03",
            theme="repurchase-decision",
            frames=[
                ContentFrame(
                    title="다시 살까 말까?",
                    body="한 병의 느낌만으로 결정해도 괜찮을까?",
                    evidence_ids=repurchase_ids or fallback_ids,
                    scene="거의 비어가는 세럼 병을 들고 고민하는 모습",
                    speaker="고객",
                    emotion="고민",
                ),
                ContentFrame(
                    title="재구매 후기를 비교",
                    body="사용 기간과 피부 타입이 함께 적힌 후기를 봤어.",
                    evidence_ids=repurchase_ids or fallback_ids,
                    scene="여러 채널의 리뷰를 나란히 비교하는 휴대폰 화면",
                    speaker="고객",
                    emotion="신중",
                ),
                ContentFrame(
                    title="결국 중요한 건 루틴",
                    body="제품보다 내가 꾸준히 쓸 수 있는지가 먼저야.",
                    evidence_ids=routine_ids or repurchase_ids or fallback_ids,
                    scene="정돈된 화장대에 세럼을 루틴 순서대로 놓는 모습",
                    speaker="고객",
                    emotion="확신",
                ),
                ContentFrame(
                    title="나에게 맞게 선택",
                    body="리뷰는 참고하고, 내 피부 반응은 직접 확인하기.",
                    evidence_ids=repurchase_ids or fallback_ids,
                    scene=f"{product_name}을 화장대에 두고 편안하게 미소 짓는 모습",
                    speaker="고객",
                    emotion="편안",
                ),
            ],
        ),
    ]


def evidence_ids_for(evidence: list[Evidence], predicate) -> list[str]:
    return [item.id for item in evidence if item.type == "customer_review" and predicate(item)][:3]


def build_imagegen_prompts(carousels: list[Carousel], product_name: str) -> dict:
    sheets = []
    for carousel in carousels:
        scenes = "\n".join(
            f"Panel {index + 1}: {frame.scene}; emotion: {frame.emotion}."
            for index, frame in enumerate(carousel.frames)
        )
        sheets.append(
            {
                "id": carousel.id,
                "output_filename": f"{carousel.id}_art.png",
                "prompt": (
                    "Use case: illustration-story\n"
                    "Asset type: Korean beauty Instagram 4-panel comic background\n"
                    "Primary request: create one polished 2x2 four-panel comic sheet following these exact scenes.\n"
                    f"{scenes}\n"
                    "Subject: the same Korean woman in her late 20s across all four panels, consistent face, bob haircut, mint cardigan.\n"
                    "Style/medium: warm contemporary Korean webtoon illustration, clean expressive line art, editorial beauty color, detailed domestic backgrounds.\n"
                    "Composition/framing: square 2x2 grid, four equal panels, clear visual action, keep the lower 28 percent of each panel visually quiet for later speech-bubble overlay.\n"
                    "Color palette: balanced mint, coral, warm yellow, pale blue, off-white; dark green linework.\n"
                    "Constraints: no text, no letters, no numbers, no speech bubbles, no captions, no logos, no watermark; do not merge panels; preserve the same character and outfit."
                ),
            }
        )
    return {
        "comic_sheets": sheets,
        "product_hero": {
            "output_filename": "product_hero_art.png",
            "prompt": (
                "Use case: product-mockup\n"
                "Asset type: final Instagram product introduction image background\n"
                f"Primary request: premium clean studio product photograph inspired by the supplied {product_name} reference.\n"
                "Subject: one white PDRN serum pump bottle, centered slightly left, crisp bottle silhouette and realistic materials.\n"
                "Scene/backdrop: bright bathroom vanity with subtle mint glass and a small coral accent, generous negative space on the right for Korean copy.\n"
                "Lighting/mood: soft morning window light, trustworthy and fresh, realistic controlled shadow.\n"
                "Constraints: remove the large refund headline and every promotional banner from the reference; bottle label may remain; no added claims, no extra text, no watermark, no duplicate product."
            ),
        },
    }


def all_copy(carousels: list[Carousel], product_name: str) -> list[str]:
    phrases = [product_name]
    for carousel in carousels:
        for frame in carousel.frames:
            phrases.extend([frame.title, frame.body])
    phrases.append(f"{product_name}: 재구매 리뷰에서 확인한 루틴 경험")
    phrases.extend(
        [
            "분산된 공개 리뷰에서 발견한 고객 루틴 경험을 바탕으로 만든 홍보 초안입니다.",
            "개인차가 있을 수 있습니다.",
            "최종 게시 전 법무·광고 검수 필요.",
        ]
    )
    return phrases


def apply_compliance(
    carousels: list[Carousel],
    findings=None,
) -> list[Carousel]:
    phrases = []
    for carousel in carousels:
        for frame in carousel.frames:
            phrases.extend([frame.title, frame.body])
    findings = findings if findings is not None else review_phrases(phrases)
    for carousel in carousels:
        for frame in carousel.frames:
            frame.title = revise_phrase(frame.title, findings)
            frame.body = revise_phrase(frame.body, findings)
    return carousels


def write_svg_carousel(
    path: Path,
    carousel: Carousel,
    product_name: str,
    comic_background: Path | None = None,
) -> None:
    ensure_dir(path.parent)
    width, height = 1080, 1350
    margin, gap, header_h, footer_h = 34, 18, 116, 54
    panel_w = (width - margin * 2 - gap) // 2
    panel_h = (height - margin * 2 - header_h - footer_h - gap) // 2
    title = {
        "first-week-journey": "처음 시작하는 PDRN 루틴",
        "morning-routine": "화장 전 세럼, 이렇게 써봤어요",
        "repurchase-decision": "재구매 전에 확인한 세 가지",
    }.get(carousel.theme, product_name)
    chunks = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="1080" height="1350" fill="#FFF9F2"/>',
        '<text x="540" y="66" text-anchor="middle" font-family="Arial, sans-serif" font-size="38" font-weight="800" fill="#162F2A">'
        + html.escape(title)
        + '</text>',
        '<text x="540" y="98" text-anchor="middle" font-family="Arial, sans-serif" font-size="18" fill="#668078">공개 리뷰에서 찾은 실제 사용 맥락을 4컷으로 재구성했습니다</text>',
    ]
    if comic_background and comic_background.is_file():
        mime = mimetypes.guess_type(comic_background.name)[0] or "image/png"
        encoded = base64.b64encode(comic_background.read_bytes()).decode("ascii")
        chunks.append(
            f'<image x="{margin}" y="{header_h}" width="{width - margin * 2}" height="{panel_h * 2 + gap}" '
            f'preserveAspectRatio="xMidYMid slice" href="data:{mime};base64,{encoded}"/>'
        )
    for idx, frame in enumerate(carousel.frames):
        x = margin + (panel_w + gap) * (idx % 2)
        y = header_h + (panel_h + gap) * (idx // 2)
        panel_fill = "none" if comic_background and comic_background.is_file() else "#DCEBE5"
        chunks.append(f'<rect x="{x}" y="{y}" width="{panel_w}" height="{panel_h}" rx="12" fill="{panel_fill}" stroke="#162F2A" stroke-width="7"/>')
        if not comic_background or not comic_background.is_file():
            chunks.extend(fallback_comic_scene(x, y, panel_w, panel_h, idx, frame.emotion))
        bubble_y = y + panel_h - 178
        chunks.append(f'<rect x="{x + 22}" y="{bubble_y}" width="{panel_w - 44}" height="142" rx="28" fill="#FFFFFF" stroke="#162F2A" stroke-width="4"/>')
        chunks.append(f'<circle cx="{x + 52}" cy="{y + 48}" r="27" fill="#FF7058"/>')
        chunks.append(f'<text x="{x + 52}" y="{y + 58}" text-anchor="middle" font-family="Arial, sans-serif" font-size="25" font-weight="800" fill="#FFFFFF">{idx + 1}</text>')
        chunks.append(f'<text x="{x + 42}" y="{bubble_y + 38}" font-family="Arial, sans-serif" font-size="25" font-weight="800" fill="#162F2A">{html.escape(frame.title)}</text>')
        for line_idx, line in enumerate(wrap_korean(frame.body, 24)[:3]):
            chunks.append(f'<text x="{x + 42}" y="{bubble_y + 76 + line_idx * 29}" font-family="Arial, sans-serif" font-size="21" fill="#203B37">{html.escape(line)}</text>')
        evidence = format_evidence_label(frame.evidence_ids[:3])
        chunks.append(f'<text x="{x + 30}" y="{y + panel_h - 12}" font-family="Arial, sans-serif" font-size="14" fill="#66736F">리뷰 근거 {html.escape(evidence)}</text>')
    chunks.append('<text x="540" y="1320" text-anchor="middle" font-family="Arial, sans-serif" font-size="16" fill="#668078">고객 리뷰를 바탕으로 재구성한 콘텐츠이며 개인차가 있을 수 있습니다.</text>')
    chunks.append("</svg>")
    path.write_text("\n".join(chunks), encoding="utf-8")


def fallback_comic_scene(x: int, y: int, w: int, h: int, index: int, emotion: str) -> list[str]:
    palette = ["#FFD8C8", "#D8EAF7", "#FFF1B8", "#DDEBD1"]
    face_y = y + 170
    mouth = "M -16 0 Q 0 14 16 0" if emotion in {"안도", "만족", "확신", "편안"} else "M -13 8 Q 0 -2 13 8"
    return [
        f'<rect x="{x + 7}" y="{y + 7}" width="{w - 14}" height="{h - 14}" rx="8" fill="{palette[index]}"/>',
        f'<circle cx="{x + w // 2}" cy="{face_y}" r="82" fill="#FFD5B5" stroke="#162F2A" stroke-width="6"/>',
        f'<path d="M {x + w // 2 - 86} {face_y - 24} Q {x + w // 2} {face_y - 118} {x + w // 2 + 88} {face_y - 22}" fill="#313A38"/>',
        f'<circle cx="{x + w // 2 - 28}" cy="{face_y - 4}" r="6" fill="#162F2A"/>',
        f'<circle cx="{x + w // 2 + 28}" cy="{face_y - 4}" r="6" fill="#162F2A"/>',
        f'<path d="{mouth}" transform="translate({x + w // 2} {face_y + 35})" fill="none" stroke="#162F2A" stroke-width="6" stroke-linecap="round"/>',
        f'<path d="M {x + w // 2 - 105} {face_y + 76} Q {x + w // 2} {face_y + 28} {x + w // 2 + 105} {face_y + 76} L {x + w // 2 + 128} {y + h - 190} L {x + w // 2 - 128} {y + h - 190} Z" fill="#5B9E8B" stroke="#162F2A" stroke-width="6"/>',
    ]


def write_product_ad(
    path: Path,
    product_name: str,
    headline: str,
    product_image: Path | None = None,
    product_hero: Path | None = None,
) -> None:
    ensure_dir(path.parent)
    safe_headline = revise_phrase(headline, review_phrases([headline]))
    body = "분산된 공개 리뷰에서 발견한 고객 루틴 경험을 바탕으로 만든 홍보 초안입니다."
    hero_visual = _hero_visual(product_hero)
    product_visual = _product_visual(product_image, product_name) if not hero_visual else ""
    title_lines = wrap_korean(product_name, 15)[:3]
    headline_lines = wrap_korean(safe_headline, 18)[:3]
    body_lines = wrap_korean(body, 25)[:4]
    title_svg = _text_lines(title_lines, 520, 255, 38, 52, "#17342F", "700")
    headline_svg = _text_lines(headline_lines, 520, 430, 30, 44, "#17342F", "700")
    body_svg = _text_lines(body_lines, 520, 610, 25, 38, "#203B37", "400")
    overlay = (
        '<rect width="1080" height="1080" fill="#EAF4F0"/>'
        if not hero_visual
        else '<rect x="465" y="70" width="565" height="850" rx="34" fill="#FFF9F2" opacity="0.88"/>'
    )
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1080" height="1080" viewBox="0 0 1080 1080">
  {hero_visual}
  {overlay}
  <circle cx="875" cy="170" r="125" fill="#F7F2EA"/>
  {product_visual}
  <text x="520" y="150" font-family="Arial, sans-serif" font-size="18" fill="#66736F">PUBLIC REVIEW SIGNAL</text>
  {title_svg}
  {headline_svg}
  {body_svg}
  <line x1="520" y1="790" x2="980" y2="790" stroke="#A8B8B3" stroke-width="2"/>
  <text x="520" y="840" font-family="Arial, sans-serif" font-size="21" fill="#66736F">개인차가 있을 수 있습니다.</text>
  <text x="520" y="880" font-family="Arial, sans-serif" font-size="21" fill="#66736F">최종 게시 전 법무·광고 검수 필요.</text>
</svg>"""
    path.write_text(svg, encoding="utf-8")


def _hero_visual(product_hero: Path | None) -> str:
    if not product_hero or not product_hero.is_file():
        return ""
    mime = mimetypes.guess_type(product_hero.name)[0] or "image/png"
    encoded = base64.b64encode(product_hero.read_bytes()).decode("ascii")
    return (
        '<rect width="1080" height="1080" fill="#FFFDF9"/>'
        f'<image x="0" y="0" width="520" height="1080" preserveAspectRatio="xMidYMid slice" '
        f'href="data:{mime};base64,{encoded}"/>'
    )


def _product_visual(product_image: Path | None, product_name: str) -> str:
    if product_image and product_image.is_file():
        mime = mimetypes.guess_type(product_image.name)[0] or "image/png"
        encoded = base64.b64encode(product_image.read_bytes()).decode("ascii")
        return (
            '<rect x="60" y="150" width="400" height="730" rx="8" fill="#FFFFFF"/>'
            f'<image x="75" y="165" width="370" height="700" preserveAspectRatio="xMidYMid meet" '
            f'href="data:{mime};base64,{encoded}"/>'
        )
    label = "PDRN" if "PDRN" in product_name.upper() else "SKINCARE"
    return f"""
      <ellipse cx="284" cy="824" rx="170" ry="30" fill="#C5D7D1" opacity="0.55"/>
      <rect x="212" y="180" width="144" height="78" rx="18" fill="#17342F"/>
      <rect x="238" y="132" width="92" height="72" rx="12" fill="#D7E5E0" stroke="#17342F" stroke-width="5"/>
      <rect x="135" y="240" width="298" height="570" rx="58" fill="#FCFDFC" stroke="#17342F" stroke-width="7"/>
      <rect x="168" y="318" width="232" height="318" rx="12" fill="#D6EBE4"/>
      <text x="284" y="382" text-anchor="middle" font-family="Arial, sans-serif" font-size="19" font-weight="700" fill="#17342F">MEDITHERAPY</text>
      <text x="284" y="468" text-anchor="middle" font-family="Arial, sans-serif" font-size="46" font-weight="700" fill="#17342F">{html.escape(label)}</text>
      <line x1="216" y1="500" x2="352" y2="500" stroke="#6D8F84" stroke-width="3"/>
      <text x="284" y="548" text-anchor="middle" font-family="Arial, sans-serif" font-size="18" fill="#46675E">SAFE REVIEW ASSET</text>
      <text x="284" y="690" text-anchor="middle" font-family="Arial, sans-serif" font-size="17" fill="#66736F">원본 위험 문구 제거본</text>
    """


def _text_lines(
    lines: list[str],
    x: int,
    y: int,
    size: int,
    line_height: int,
    color: str,
    weight: str,
) -> str:
    return "".join(
        f'<text x="{x}" y="{y + index * line_height}" font-family="Arial, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{color}">{html.escape(line)}</text>'
        for index, line in enumerate(lines)
    )


def render_png(svg_path: Path) -> Path | None:
    chrome = next(
        (
            candidate
            for candidate in [
                shutil.which("google-chrome"),
                shutil.which("chromium"),
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            ]
            if candidate and Path(candidate).is_file()
        ),
        None,
    )
    if not chrome:
        return None
    png_path = svg_path.with_suffix(".png")
    svg_source = svg_path.read_text(encoding="utf-8")
    viewport_height = 1350 if 'height="1350"' in svg_source else 1080
    try:
        subprocess.run(
            [
                chrome,
                "--headless=new",
                "--disable-gpu",
                "--hide-scrollbars",
                "--run-all-compositor-stages-before-draw",
                "--virtual-time-budget=1000",
                f"--window-size=1080,{viewport_height}",
                f"--screenshot={png_path}",
                svg_path.resolve().as_uri(),
            ],
            check=True,
            capture_output=True,
            timeout=30,
        )
    except (subprocess.SubprocessError, OSError):
        return None
    return png_path if png_path.exists() else None


def wrap_korean(text: str, width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.splitlines() or [text]:
        lines.extend(textwrap.wrap(paragraph, width=width, break_long_words=False))
    return lines


def format_evidence_label(evidence_ids: list[str]) -> str:
    if not evidence_ids:
        return "없음"
    labels = []
    for evidence_id in evidence_ids:
        match = re.search(r"(\d{3,})$", evidence_id)
        labels.append(f"#{match.group(1)}" if match else evidence_id[:12])
    return " · ".join(labels)
