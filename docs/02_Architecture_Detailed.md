# 아키텍처

## Pipeline
URL 입력
→ Crawler
→ Screenshot
→ OCR/VLM
→ Review Parser
→ Insight Engine
→ Report Generator
→ Carousel Generator
→ Law MCP Review
→ Export

## 모듈 책임
crawler: 데이터 수집
vlm: 이미지 분석
analysis: 인사이트
content: 콘텐츠 생성
compliance: 법률 검토
export: 최종 결과물 생성
