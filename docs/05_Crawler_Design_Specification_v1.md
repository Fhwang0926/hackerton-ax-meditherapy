# 05. Crawler Design Specification

## 목적
공개 데이터만을 대상으로 안정적으로 수집하는 크롤러를 설계한다.

# 1. 범위

지원 대상
- 메디테라피 자사몰
- 올리브영
- 네이버쇼핑
- 쿠팡(공개 페이지)
- 사용자 지정 공개 URL

수집 제외
- 로그인 필요 데이터
- 비공개 API
- CAPTCHA 우회

# 2. 기술 스택

- Playwright
- BeautifulSoup
- lxml
- requests (보조)

Playwright를 기본으로 사용한다.

# 3. 입력

{
 product_name,
 urls:[]
}

# 4. 출력

crawler/raw/{domain}.json

필드
- source
- product_name
- review
- rating
- date
- image_urls
- product_url
- page_url

# 5. URL 처리

1. URL 검증
2. 중복 제거
3. robots.txt 확인
4. 접근 테스트
5. Queue 등록

# 6. 페이지 처리

- 제품 정보
- 리뷰
- 리뷰 이미지
- 옵션
- 평점

페이지네이션 종료 조건
- 다음 버튼 없음
- 리뷰 없음
- 최대 페이지 도달

# 7. 이미지 처리

다운로드하지 않고 URL 저장을 기본으로 한다.
사용자가 요청한 경우만 다운로드.

# 8. Retry 정책

- timeout : 3회
- 429 : exponential backoff
- 5xx : 최대 5회

# 9. 로그

logs/crawler.jsonl

항목
- 시작시간
- 종료시간
- URL
- 성공여부
- 오류

# 10. Acceptance Criteria

- URL 검증 성공
- 공개 리뷰 수집
- JSON 저장
- 로그 저장
- 실패 URL 분리

# 11. 향후 확장

- RSS
- YouTube 댓글
- 블로그
- 인스타 공개 게시물
