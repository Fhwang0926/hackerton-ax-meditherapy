# 10. Law MCP Integration Design

## 목적
생성된 마케팅 결과물을 게시 전에 법률 관점에서 자동 검토하여 위험 표현을 줄이고 수정안을 제안한다.

## 역할
Law MCP는 콘텐츠를 생성하지 않는다.
생성된 결과물을 검토하고 근거와 수정안을 제공한다.

# 적용 대상
- Carousel 제목
- Carousel 본문
- CTA
- Caption
- Product Ad 문구
- OCR로 추출한 이미지 내 텍스트

# 입력
compliance_request.json

필드
- source
- content_type
- original_text
- product_name
- evidence

# 처리 순서
1. Carousel 생성 완료
2. 모든 문구 수집
3. Law MCP 호출
4. 위험 문구 식별
5. 법률 근거 조회
6. 수정안 생성
7. Before/After Diff 생성
8. compliance_report.md 생성

# 출력

compliance/
├── compliance_report.md
├── compliance.json
├── before_after_diff.md

# Risk Level

High
- 사용 금지 또는 강한 오인 우려 표현

Medium
- 상황에 따라 검토가 필요한 표현

Low
- 권장 수정 표현

# Report 형식

문구:
위험도:
근거:
설명:
수정안:

# 자동 수정 원칙
- 원래 의미 유지
- 과장 표현 제거
- 근거 없는 단정 제거
- Evidence와 일치하도록 수정

# 실패 처리
Law MCP 실패 시
- 원문 유지
- 오류 로그 기록
- 재시도 2회

# Acceptance Criteria
- 모든 문구 검사
- 근거 포함
- Risk Level 포함
- Before/After Diff 생성
- compliance_report.md 생성
