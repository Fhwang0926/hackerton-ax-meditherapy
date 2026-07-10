# 11. Implementation Task 01 - Crawler

## 목적
이 문서는 Codex가 Crawler 모듈만 구현하기 위한 작업지시서이다.

---

# 작업 목표

다음 기능을 구현한다.

- URL 입력
- URL 검증
- robots.txt 확인
- Playwright 기반 페이지 수집
- HTML 저장
- Screenshot 저장
- Raw JSON 저장

본 작업에서는 분석 기능을 구현하지 않는다.

---

# 생성해야 하는 디렉터리

src/
  crawler/
    __init__.py
    validator.py
    robots.py
    browser.py
    collector.py
    models.py
    schemas.py
    storage.py

---

# 클래스

## URLValidator

책임

- URL 검증
- 중복 제거

Method

validate(url)

Return

ValidatedURL

---

## RobotsChecker

Method

is_allowed(url)

Return

bool

---

## Browser

기술

Playwright

Method

open()

close()

goto(url)

screenshot()

html()

---

## Collector

Method

collect()

Return

ProductPage

---

# ProductPage Schema

product_name

product_url

source

rating

review_count

html

images[]

reviews[]

captured_at

---

# Review Schema

review_id

rating

date

content

image_urls

source

---

# Storage

저장 위치

crawler/raw/

파일명

{domain}.json

---

# 로그

logs/crawler.jsonl

필드

timestamp

url

status

elapsed_ms

error

---

# 예외 처리

Timeout

Retry 3회

404

Skip

SSL

Skip

robots.txt

Skip

---

# 테스트

Case1

정상 URL

Case2

404

Case3

robots.txt 차단

Case4

리뷰 없음

Case5

페이지네이션 종료

---

# Acceptance Criteria

[ ] URL 검증

[ ] robots 확인

[ ] HTML 저장

[ ] Screenshot 저장

[ ] JSON 저장

[ ] 로그 저장

[ ] 테스트 통과
