# 09. Carousel Generator Design Specification

## 목적
Insight Engine이 생성한 근거 기반 인사이트를 인스타그램 4컷 캐러셀(총 3세트)로 변환한다.

## 설계 원칙
- 리뷰를 그대로 광고 문구로 사용하지 않는다.
- 모든 핵심 문장은 Evidence를 기반으로 작성한다.
- Law MCP 검수 전에는 최종 산출물로 간주하지 않는다.

# 입력

- insight.json
- evidence.json
- product.json
- brand_profile.json

# 출력

carousel/
├── carousel_01.md
├── carousel_02.md
├── carousel_03.md
├── prompts/
└── assets.json

# 생성 규칙

## Carousel 1
목표: 문제 인식

Card1
Hook

Card2
Evidence

Card3
Insight

Card4
CTA

## Carousel 2
목표: 사용 경험

Card1
Persona

Card2
Journey

Card3
Evidence

Card4
CTA

## Carousel 3
목표: 재구매

Card1
재구매 패턴

Card2
Evidence

Card3
추천 루틴

Card4
제품 소개

# 카드 생성 규칙

각 카드에는

- 제목
- 본문
- 핵심 메시지
- 이미지 프롬프트
- 디자인 가이드
- 제품 노출 여부

가 반드시 존재해야 한다.

# 이미지 프롬프트 규칙

- 텍스트를 이미지 안에 직접 렌더링하지 않는다.
- 제품 위치를 명시한다.
- 브랜드 컬러를 사용한다.
- SNS 캐러셀 비율을 따른다.

# CTA 규칙

허용
- 자세히 보기
- 사용 후기 확인
- 제품 알아보기

금지
- 치료
- 완치
- 100% 효과
- 즉시 개선

# Law MCP 연계

생성 완료 후

1. 제목 검사
2. 본문 검사
3. CTA 검사

수정사항 발생 시

before_after_diff.md 생성

# Acceptance Criteria

- 캐러셀 3세트 생성
- 각 카드에 Evidence 존재
- 이미지 프롬프트 생성
- Law MCP 통과
