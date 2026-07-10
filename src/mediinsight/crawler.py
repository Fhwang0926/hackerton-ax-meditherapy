from __future__ import annotations

import json
import re
import shutil
import subprocess
import ssl
import urllib.error
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

from .models import Channel, Evidence, RawReview
from .utils import short_text


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self.chunks: list[str] = []
        self.images: list[str] = []
        self.iframes: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1
        if tag == "img":
            src = dict(attrs).get("src") or dict(attrs).get("data-src")
            if src:
                self.images.append(src)
        if tag == "iframe":
            src = dict(attrs).get("src")
            if src:
                self.iframes.append(src)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        text = re.sub(r"\s+", " ", data).strip()
        if len(text) >= 8:
            self.chunks.append(text)


def fetch_public_page(
    channel: Channel,
    timeout: int = 15,
    capture_dir: Path | None = None,
) -> Evidence:
    if capture_dir:
        chrome = find_chrome()
        if chrome:
            captured = fetch_with_chrome(channel, capture_dir, chrome, timeout)
            if captured.type != "page_fetch_error":
                return captured

    return fetch_with_http(channel, timeout)


def fetch_with_http(channel: Channel, timeout: int = 15) -> Evidence:
    request = urllib.request.Request(
        channel.url,
        headers={
            "User-Agent": "MediInsightHackathonBot/0.1 (+public-data-research)"
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get("content-type", "")
            raw = response.read(800_000)
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        return Evidence(
            id=f"page-{channel.name}",
            source=channel.name,
            type="page_fetch_error",
            text=f"Could not fetch public page: {exc}",
            url=channel.url,
            tags=["fetch_error"],
        )

    if "text/html" not in content_type and b"<html" not in raw[:1000].lower():
        return Evidence(
            id=f"page-{channel.name}",
            source=channel.name,
            type="page_metadata",
            text=f"Fetched non-HTML public resource with content-type {content_type}",
            url=channel.url,
            tags=["non_html"],
        )

    parser = TextExtractor()
    parser.feed(raw.decode("utf-8", errors="ignore"))
    text = " ".join(parser.chunks[:80])
    return Evidence(
        id=f"page-{channel.name}",
        source=channel.name,
        type="public_page_text",
        text=short_text(text, 2000) if text else "No readable text extracted.",
        url=channel.url,
        tags=["public_page"],
        captured_at=now_iso(),
        provenance="http_visible_text",
        signals={
            "content_type": content_type,
            "chunks": len(parser.chunks),
            "image_urls": [urljoin(channel.url, src) for src in parser.images[:30]],
            "iframe_urls": [urljoin(channel.url, src) for src in parser.iframes[:20]],
        },
    )


def find_chrome() -> str | None:
    candidates = [
        shutil.which("google-chrome"),
        shutil.which("chromium"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    ]
    return next((path for path in candidates if path and Path(path).is_file()), None)


def fetch_with_chrome(
    channel: Channel,
    capture_dir: Path,
    chrome: str,
    timeout: int,
) -> Evidence:
    capture_dir.mkdir(parents=True, exist_ok=True)
    screenshot = capture_dir / f"{channel.name}.png"
    base_args = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--window-size=1440,2400",
        "--virtual-time-budget=6000",
    ]
    try:
        dom = subprocess.run(
            [*base_args, "--dump-dom", channel.url],
            check=True,
            capture_output=True,
            text=True,
            timeout=max(timeout, 20),
        ).stdout
        subprocess.run(
            [*base_args, f"--screenshot={screenshot}", channel.url],
            check=True,
            capture_output=True,
            timeout=max(timeout, 20),
        )
    except (subprocess.SubprocessError, OSError) as exc:
        return Evidence(
            id=f"page-{channel.name}",
            source=channel.name,
            type="page_fetch_error",
            text=f"Browser capture failed: {exc}",
            url=channel.url,
            captured_at=now_iso(),
            provenance="chrome_headless",
            tags=["fetch_error"],
        )

    (capture_dir / f"{channel.name}.html").write_text(dom, encoding="utf-8")
    parser = TextExtractor()
    parser.feed(dom)
    text = " ".join(parser.chunks)
    return Evidence(
        id=f"page-{channel.name}",
        source=channel.name,
        type="public_page_text",
        text=short_text(text, 12_000) if text else "No readable text extracted.",
        url=channel.url,
        captured_at=now_iso(),
        provenance="chrome_rendered_dom",
        tags=["public_page", "browser_captured"],
        signals={
            "chunks": len(parser.chunks),
            "screenshot": str(screenshot),
            "image_urls": [urljoin(channel.url, src) for src in parser.images[:50]],
            "iframe_urls": [urljoin(channel.url, src) for src in parser.iframes[:20]],
        },
    )


class CremaReviewParser(HTMLParser):
    VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}

    def __init__(self) -> None:
        super().__init__()
        self.reviews: list[dict] = []
        self._review: dict | None = None
        self._review_depth = 0
        self._message_depth = 0
        self._message_chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        classes = attr.get("class") or ""
        if self._review is None and tag == "div":
            match = re.search(r"(?:^|\s)review-(\d+)(?:\s|$)", classes)
            if match and "BodyPc__review" in classes:
                self._review = {
                    "review_id": match.group(1),
                    "rating": 0,
                    "images": [],
                    "messages": [],
                }
                self._review_depth = 1
                return
        if self._review is None:
            return
        if tag not in self.VOID_TAGS:
            self._review_depth += 1
        if tag == "li" and "AppRate__item" in classes:
            self._review["rating"] += 1
        if tag == "img":
            src = attr.get("src") or attr.get("data-src")
            if src and "/reviews/" in src:
                self._review["images"].append(src)
        if tag == "div" and "AppReviewInfoSectionListV3__message" in classes:
            self._message_depth = 1
            self._message_chunks = []
        elif self._message_depth and tag not in self.VOID_TAGS:
            self._message_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if self._review is None:
            return
        if self._message_depth:
            self._message_depth -= 1
            if self._message_depth == 0:
                message = re.sub(r"\s+", " ", " ".join(self._message_chunks)).strip()
                if message and message not in self._review["messages"]:
                    self._review["messages"].append(message)
                self._message_chunks = []
        self._review_depth -= 1
        if self._review_depth == 0:
            messages = sorted(self._review["messages"], key=len, reverse=True)
            if messages:
                self._review["text"] = messages[0]
                self._review["images"] = list(dict.fromkeys(self._review["images"]))
                self.reviews.append(self._review)
            self._review = None

    def handle_data(self, data: str) -> None:
        if self._message_depth:
            text = re.sub(r"\s+", " ", data).strip()
            if text:
                self._message_chunks.append(text)


def fetch_embedded_reviews(
    channel: Channel,
    page_evidence: Evidence,
    capture_dir: Path,
    chrome: str,
    timeout: int = 20,
    max_pages: int = 2,
) -> list[Evidence]:
    iframe_urls = page_evidence.signals.get("iframe_urls", [])
    list_urls = [url for url in iframe_urls if "review" in url and "list_v3" in url]
    if not list_urls:
        return []

    base_url = list_urls[0]
    reviews: list[Evidence] = []
    for page in range(1, max(1, max_pages) + 1):
        page_url = with_query_value(base_url, "page", str(page))
        try:
            dom = subprocess.run(
                [
                    chrome,
                    "--headless=new",
                    "--disable-gpu",
                    "--hide-scrollbars",
                    "--virtual-time-budget=8000",
                    "--dump-dom",
                    page_url,
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=max(timeout, 25),
            ).stdout
        except (subprocess.SubprocessError, OSError):
            continue
        (capture_dir / f"{channel.name}_reviews_page_{page}.html").write_text(dom, encoding="utf-8")
        parser = CremaReviewParser()
        parser.feed(dom)
        if not parser.reviews:
            break
        for row in parser.reviews:
            review_id = row["review_id"]
            reviews.append(
                Evidence(
                    id=f"review-{channel.name}-crema-{review_id}",
                    source=channel.name,
                    type="customer_review",
                    text=row["text"],
                    url=f"https://review5.cre.ma/v2/meditherapy.co.kr/reviews/{review_id}",
                    rating=row["rating"] or None,
                    captured_at=now_iso(),
                    provenance="chrome_rendered_public_review_iframe",
                    tags=["browser_review", "embedded_review"],
                    signals={"image_urls": row["images"], "iframe_url": page_url},
                )
            )
    return reviews


def extract_schema_reviews(dom: str, channel: Channel) -> list[Evidence]:
    """Extract public Review objects from JSON-LD without treating page copy as reviews."""
    reviews: list[Evidence] = []
    scripts = re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        dom,
        flags=re.IGNORECASE | re.DOTALL,
    )
    for script in scripts:
        try:
            payload = json.loads(script.strip())
        except json.JSONDecodeError:
            continue
        for row in iter_schema_reviews(payload):
            text = str(row.get("reviewBody", "")).strip()
            if not text:
                continue
            rating_value = row.get("reviewRating", {}).get("ratingValue") if isinstance(row.get("reviewRating"), dict) else None
            try:
                rating = int(float(rating_value)) if rating_value is not None else None
            except (TypeError, ValueError):
                rating = None
            reviews.append(
                Evidence(
                    id=f"review-{channel.name}-schema-{len(reviews) + 1:03d}",
                    source=channel.name,
                    type="customer_review",
                    text=text,
                    url=channel.url,
                    rating=rating,
                    captured_at=now_iso(),
                    provenance="chrome_rendered_schema_org_review",
                    tags=["browser_review", "structured_data_review"],
                    signals={"author": schema_author(row.get("author"))},
                )
            )
    return reviews


def iter_schema_reviews(value):
    if isinstance(value, dict):
        rows = value.get("review")
        if isinstance(rows, dict):
            yield rows
        elif isinstance(rows, list):
            yield from (row for row in rows if isinstance(row, dict))
        for child in value.values():
            yield from iter_schema_reviews(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_schema_reviews(child)


def schema_author(value) -> str | None:
    if isinstance(value, dict):
        name = value.get("name")
        return str(name).strip() if name else None
    return str(value).strip() if value else None


def with_query_value(url: str, key: str, value: str) -> str:
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query[key] = value
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def normalize_manual_review(index: int, review: RawReview) -> Evidence:
    tags: list[str] = ["manual_review"]
    if review.rating is not None and review.rating >= 4:
        tags.append("positive")
    if review.rating is not None and review.rating <= 3:
        tags.append("friction")
    if any(word in review.text for word in ["재구매", "또 샀", "한 통", "다 쓰"]):
        tags.append("repurchase")
    if any(word in review.text for word in ["1주", "2주", "3주", "4주", "한 달", "1개월"]):
        tags.append("time_journey")

    return Evidence(
        id=f"review-{index:03d}",
        source=review.channel,
        type="customer_review",
        text=review.text,
        rating=review.rating,
        skin_type=review.skin_type,
        usage_period=review.usage_period,
        url=review.url,
        captured_at=review.captured_at or now_iso(),
        provenance=review.provenance,
        tags=tags,
    )


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def download_public_asset(url: str, destination: Path, timeout: int = 20) -> Path:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 MediInsight/0.2"},
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = response.read(12_000_000)
        destination.write_bytes(data)
    except urllib.error.URLError as exc:
        if not isinstance(exc.reason, ssl.SSLError) or not shutil.which("curl"):
            raise
        subprocess.run(
            [
                "curl",
                "--fail",
                "--location",
                "--silent",
                "--show-error",
                "--max-time",
                str(timeout),
                "--output",
                str(destination),
                url,
            ],
            check=True,
            timeout=timeout + 5,
        )
    return destination
