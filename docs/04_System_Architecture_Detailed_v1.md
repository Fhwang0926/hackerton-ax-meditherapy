# 04. System Architecture (Detailed)

## 목적
본 문서는 MediInsight 시스템의 전체 아키텍처와 각 모듈의 책임을 정의한다.

# 1. 전체 파이프라인

User Input
→ URL Validator
→ Crawler
→ Screenshot Engine
→ OCR
→ VLM Analyzer
→ Review Parser
→ Evidence Extractor
→ Insight Engine
→ Report Generator
→ Carousel Generator
→ Product Ad Generator
→ Law MCP Compliance Review
→ Export

# 2. 모듈 정의

## URL Validator
책임
- URL 형식 검증
- 중복 제거
- robots.txt 확인
- 접근 가능 여부 확인

입력
- URL[]

출력
- ValidURL[]

예외
- Timeout
- 404
- SSL 오류

## Crawler
수집
- HTML
- 리뷰
- 평점
- 작성일
- 이미지 URL
- 제품 정보

저장
crawler/raw/

## Screenshot Engine

생성
- Desktop Screenshot
- Mobile Screenshot

저장
assets/screenshots/

## OCR

추출
- 이미지 내 문구
- 숫자
- CTA

## VLM

분석
- Before/After 이미지 여부
- 제품 노출
- 사용 장면
- 피부 타입 표시
- 시각적 레이아웃

주의
효능 자체를 판정하지 않는다.

## Review Parser

추출
- 피부타입
- 사용기간
- 만족
- 불만
- 재구매
- 계절
- 연령

## Evidence Extractor

모든 Insight에는
- 리뷰 근거
- URL
- 채널
- 리뷰 날짜

를 연결한다.

## Insight Engine

생성
- Persona
- Journey
- Pain Point
- Delight Point
- Recommendation

## Report Generator

출력
report.md
report.pdf

## Carousel Generator

입력
Insight JSON

출력
Card1 Hook
Card2 Evidence
Card3 Insight
Card4 CTA

## Product Ad Generator

입력
USP
Evidence
제품 정보

출력
홍보 이미지 Prompt
홍보 카피

## Law MCP

검사
- Carousel
- Caption
- Product Copy

출력
- Risk
- Legal Basis
- Suggested Rewrite
- Diff

## Export

output/
 report/
 assets/
 compliance/
 marketing/

# 3. 로그 정책

각 단계는
logs/{module}.jsonl

에 기록한다.

# 4. 실패 정책

실패한 URL은 건너뛰고 나머지 작업을 계속 수행한다.

Law MCP 실패 시
원본과 수정안을 모두 저장한다.
