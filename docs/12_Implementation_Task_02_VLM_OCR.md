# 12. Implementation Task 02 - VLM & OCR

## 목적
Crawler가 저장한 스크린샷과 이미지를 분석하여 구조화된 시각 정보를 생성한다.

## 구현 범위
- OCR 실행
- VLM 분석
- JSON 출력
- Law MCP 입력 데이터 생성

## 입력

assets/screenshots/
crawler/raw/

## 출력

analysis/
  ocr.json
  vlm.json
  compliance_input.json

## 디렉터리

src/
  vlm/
    engine.py
    ocr.py
    prompt.py
    parser.py
    models.py
    exporter.py

## OCR 추출 항목
- 제목
- 배너
- CTA
- 할인 문구
- 숫자
- 이미지 내 텍스트

## VLM 추출 항목
- 레이아웃
- Before/After 여부
- 제품 노출 위치
- 사용 장면
- 피부 타입 표시
- 시각 요소

## VLM 금지사항
- 효능 판정 금지
- 의학적 추론 금지
- 피부 상태 진단 금지

## JSON Schema

vlm.json
{
 image_id:"",
 layout:"",
 visual_elements:[],
 cta:[],
 claims:[]
}

ocr.json
{
 image_id:"",
 texts:[]
}

## Law MCP 연계

OCR에서 추출한 모든 텍스트를
compliance_input.json으로 저장한다.

## 예외 처리

- OCR 실패
- 이미지 손상
- VLM Timeout
- 빈 이미지

## 로그

logs/vlm.jsonl

## 테스트

- 텍스트만 있는 배너
- 제품 사진
- Before/After
- 리뷰 이미지
- 모바일 캡처

## Acceptance Criteria

[ ] OCR 성공
[ ] VLM 성공
[ ] JSON 저장
[ ] Law MCP 입력 생성
[ ] 로그 저장
