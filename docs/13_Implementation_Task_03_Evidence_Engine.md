# 13. Implementation Task 03 - Evidence Engine

## 목적
여러 채널의 공개 데이터를 하나의 Evidence 모델로 통합하여 이후 Insight Engine이 신뢰 가능한 근거를 사용할 수 있도록 한다.

## 구현 범위
- Raw Review 정규화
- Evidence 생성
- Journey 생성
- Confidence 계산
- Evidence JSON 출력

## 입력
crawler/raw/*.json
analysis/ocr.json
analysis/vlm.json

## 출력
analysis/evidence.json
analysis/journey.json
analysis/statistics.json

## 디렉터리
src/analysis/evidence/
  models.py
  normalizer.py
  clustering.py
  journey.py
  confidence.py
  exporter.py

## Evidence Model

필수 필드
- evidence_id
- source
- channel
- product_name
- review_text
- rating
- review_date
- page_url
- image_urls
- normalized_tags[]

## 정규화 규칙

피부타입
- 지성
- 건성
- 복합성
- 민감성

사용기간
- 3일
- 1주
- 2주
- 1개월
- 3개월

감정
- 만족
- 불만
- 재구매
- 추천

## 클러스터링

동일 의미 리뷰는 하나의 Topic으로 묶는다.

예)
"흡수가 빨라요"
"금방 스며들어요"
→ 흡수성

## Journey 생성

시간 표현을 Timeline으로 변환한다.

구매
→ 초기 사용
→ 적응
→ 효과 체감
→ 재구매

## Confidence

HIGH
- 3개 이상 채널
- 30건 이상 Evidence

MEDIUM
- 2개 채널

LOW
- 단일 채널

## 예외 처리
- 날짜 없음
- 별점 없음
- 리뷰 중복
- 언어 혼합

## 테스트
- 동일 리뷰 중복
- 채널별 상충 리뷰
- 시간 표현 없음

## Acceptance Criteria
[ ] Evidence 생성
[ ] Journey 생성
[ ] Confidence 계산
[ ] JSON 저장
