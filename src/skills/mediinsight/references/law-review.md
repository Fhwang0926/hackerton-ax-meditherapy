# Cosmetic Advertising Review

The bundled `mediinsight-law` MCP performs deterministic preliminary review without an API key. It exposes:

- `review_cosmetic_claims`: review phrases and return findings with safer copy and official citations.
- `search_cosmetic_ad_law`: return the official sources used by the rulebook.

Primary sources embedded in the rules:

- 화장품법 제13조: 의약품 오인, 기능성 범위 오인, 사실과 다른 소비자 오인 광고 금지.
- 화장품법 제14조: 표시·광고 내용 실증 자료.
- 식품의약품안전처 화장품 표시·광고 관리 지침, 안내서-0086-07.

Review all carousel titles, bodies, CTA copy, product-ad copy and VLM-transcribed text. Keep original and revised phrases in `before_after.json`. A passing preliminary review is not final legal approval.
