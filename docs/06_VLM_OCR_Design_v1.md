# 06. VLM & OCR Design Specification

## 목적
텍스트 크롤링으로 얻을 수 없는 시각적 정보를 추출하여 보고서와 콘텐츠 생성의 근거 데이터로 사용한다.

# 설계 원칙
- VLM은 '효능 판정'을 하지 않는다.
- VLM은 화면에 존재하는 시각 정보를 구조화한다.
- OCR은 이미지 내부 텍스트를 추출한다.

# 입력
- Desktop Screenshot
- Mobile Screenshot
- Review Image
- Detail Image

# OCR 추출 항목
- 제목
- CTA
- 할인 문구
- 숫자(%, 기간)
- 배너 문구

출력:
ocr.json

# VLM 추출 항목
- Before/After 이미지 존재 여부
- 제품 노출 위치
- 사용 장면
- 피부 타입 표시 여부
- 주요 시각 요소
- 이미지 분위기
- 카드 레이아웃

출력:
vlm.json

# 금지 사항
- 피부가 실제로 좋아졌다고 판정하지 않는다.
- 의학적 효과를 추론하지 않는다.

# JSON Schema
{
 "image_id":"",
 "layout":"",
 "visual_elements":[],
 "cta":[],
 "claims":[],
 "warnings":[]
}

# Law MCP 연계
OCR로 추출한 모든 문구는 Law MCP 입력으로 전달한다.

# Acceptance
- OCR 성공
- VLM 결과 저장
- JSON 생성
- Law MCP 입력 가능
