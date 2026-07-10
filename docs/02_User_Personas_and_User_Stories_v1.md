# 02. User Personas & User Stories

## 목적
본 문서는 MediInsight를 실제 사용하는 사용자의 역할, 업무 흐름, Pain Point를 정의한다.

# Persona 1. 퍼포먼스 마케터

## 목표
- 신규 광고 소재 제작
- 리뷰 기반 콘텐츠 확보
- 법률 리스크 최소화

### 현재 업무
1. 자사몰 리뷰 확인
2. 올리브영 리뷰 확인
3. 경쟁사 참고
4. 콘텐츠 기획
5. 디자이너 협업
6. 법률 검토
7. 게시

### Pain Point
- 리뷰가 분산됨
- 반복 작업이 많음
- 어떤 리뷰를 활용해야 할지 모름
- 광고 문구 수정이 반복됨

### MediInsight가 제공하는 가치
- 여러 채널 리뷰 통합
- Evidence 자동 추출
- 캐러셀 초안 생성
- Law MCP 검수 완료

---

# Persona 2. 브랜드 매니저

목표
- 브랜드 메시지 일관성
- 제품 USP 발굴

Pain Point
- 채널별 고객 의견 차이
- 객관적 근거 부족

필요 산출물
- Executive Report
- Persona Insight
- 구매 동기
- 재구매 요인

---

# Persona 3. 콘텐츠 디자이너

목표
- 빠른 제작

필요 입력
- 카드별 문구
- 이미지 프롬프트
- CTA

---

# User Story

US-001
마케터로서
여러 쇼핑몰 리뷰를 한번에 분석하고 싶다.
그래서 고객 인사이트를 빠르게 얻고 싶다.

Acceptance
- URL 여러 개 입력 가능
- 리뷰 통합
- Report 생성

US-002
브랜드 매니저로서
재구매 고객의 특징을 알고 싶다.
그래서 다음 캠페인을 기획하고 싶다.

Acceptance
- 재구매 관련 리뷰 자동 추출
- Evidence 포함

US-003
디자이너로서
4컷 캐러셀 초안을 받고 싶다.
그래서 디자인만 수정하면 된다.

Acceptance
- 카드별 제목
- 본문
- CTA
- 제품 노출 위치

US-004
마케터로서
생성된 문구가 광고법을 위반하지 않았는지 알고 싶다.

Acceptance
- Law MCP 검사
- 위험도
- 수정안
- Before/After Diff

# Scope

In Scope
- 공개 URL
- 리뷰
- 이미지 OCR
- VLM
- Report
- Carousel
- Product Ad
- Law MCP

Out of Scope
- 로그인 필요 데이터
- 비공개 CRM
- 광고 자동 게시
- 결제 연동
