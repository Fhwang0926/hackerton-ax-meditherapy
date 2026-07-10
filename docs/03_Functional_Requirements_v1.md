# 03. Functional Requirements

## 목적
본 문서는 MediInsight의 모든 기능 요구사항을 정의한다.

# FR-001 프로젝트 생성
목표: Codex Plugin 기본 구조 생성

입력: 없음
출력:
- src/.codex-plugin/plugin.json
- src/.mcp.json
- skills/medinsight/SKILL.md

완료조건
- Codex에서 플러그인 인식

---

# FR-002 URL 입력

입력
- 자사몰 URL
- 올리브영 URL
- 네이버 URL
- 쿠팡 URL
- 추가 URL(0~N)

검증
- URL 형식 검사
- 중복 제거
- robots.txt 확인

예외
- 접근 실패
- 404
- timeout

---

# FR-003 Crawler

수집 대상
- HTML
- 리뷰
- 평점
- 작성일
- 작성자(공개 범위)
- 이미지 URL
- 제품명
- 옵션

산출물
crawler/raw/*.json

---

# FR-004 Screenshot

각 URL마다
- Full Page Screenshot
- Mobile Screenshot

산출물
assets/screenshots/

---

# FR-005 OCR/VLM

입력
- Screenshot

추출
- 이미지 내 문구
- Before/After 여부
- CTA
- 제품 노출
- 피부 타입 표현

산출물
analysis/vlm.json

---

# FR-006 Review Normalizer

정규화 항목
- 피부타입
- 사용기간
- 만족
- 불만
- 재구매
- 계절
- 연령
- 채널

---

# FR-007 Insight Engine

생성
- Executive Summary
- Persona
- Journey
- Pain Point
- Delight Point
- 재구매 패턴
- 채널 비교

모든 인사이트는 근거 리뷰를 포함한다.

---

# FR-008 Report Generator

출력
report.md
report.pdf

목차
1 Executive Summary
2 Data Overview
3 Persona
4 Journey
5 Evidence
6 Recommendation

---

# FR-009 Carousel Generator

생성 수
- 3세트

구성
Card1 Hook
Card2 Evidence
Card3 Insight
Card4 CTA

각 카드에는 근거 기반 문구 사용.

---

# FR-010 Product Ad

출력
product_ad.png

요구사항
- USP
- CTA
- 제품 이미지 위치
- 브랜드 톤

---

# FR-011 Law MCP

검사 대상
- Carousel 문구
- Caption
- Product Ad 문구

출력
- 위험도
- 법률 근거
- 수정안
- Before/After Diff

---

# FR-012 Export

최종 구조

output/
 report/
 carousel/
 marketing/
 compliance/

Acceptance
- 모든 파일 생성
- 오류 로그 저장
