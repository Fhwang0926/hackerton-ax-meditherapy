from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from mediinsight.compliance import review_phrases
from mediinsight.crawler import CremaReviewParser
from mediinsight.evidence import build_metrics, deduplicate_reviews, enrich_evidence
from mediinsight.models import Evidence
from mediinsight.project_store import get_project, save_project
from scripts.mediinsight_pipeline import decide_asset_usage
from mediinsight.crawler import Channel, extract_schema_reviews
from mediinsight.content import build_carousels
from mediinsight.models import Insight
from mediinsight.report import write_report


class ComplianceTests(unittest.TestCase):
    def test_visual_refund_claim_has_official_citation(self):
        findings = review_phrases(["불만족시 100% 환불보장"])
        self.assertEqual([item.rule_id for item in findings], ["COS-POLICY-006"])
        self.assertIn("law.go.kr", findings[0].citation)
        self.assertNotEqual(findings[0].phrase, findings[0].revised_phrase)

    def test_medical_claim_is_flagged(self):
        findings = review_phrases(["여드름 치료와 피부 재생"])
        self.assertEqual({item.rule_id for item in findings}, {"COS-DRUG-001", "COS-REGEN-003"})


class EvidenceTests(unittest.TestCase):
    def test_metrics_use_only_customer_reviews(self):
        evidence = enrich_evidence(
            [
                Evidence(
                    id="page",
                    source="site",
                    type="public_page_text",
                    text="재구매",
                ),
                Evidence(
                    id="review",
                    source="official",
                    type="customer_review",
                    text="민감성 피부로 2주 사용 후 재구매했습니다.",
                ),
            ]
        )
        metrics = build_metrics(evidence)
        self.assertEqual(metrics["review_count"], 1)
        self.assertEqual(metrics["repurchase_count"], 1)
        self.assertEqual(metrics["skin_type_counts"], {"민감성": 1})

    def test_duplicate_reviews_are_removed_with_audit_record(self):
        evidence = [
            Evidence(id="a", source="official", type="customer_review", text="2주 사용 후 만족했어요!"),
            Evidence(id="b", source="external", type="customer_review", text="2주 사용 후 만족했어요"),
        ]
        unique, duplicates = deduplicate_reviews(evidence)
        self.assertEqual([item.id for item in unique], ["a"])
        self.assertEqual(duplicates, [{"removed_id": "b", "kept_id": "a"}])


class DynamicReviewParserTests(unittest.TestCase):
    def test_crema_review_body_rating_and_images_are_extracted(self):
        parser = CremaReviewParser()
        parser.feed(
            """
            <div class="BodyPc__review review-758587">
              <ul><li class="AppRate__item"></li><li class="AppRate__item"></li></ul>
              <div class="AppReviewInfoSectionListV3__message">민감한 피부에도 잘 맞았고 2주 사용했습니다.</div>
              <img src="https://assets5.cre.ma/p/shop/reviews/image1.webp">
            </div>
            """
        )
        self.assertEqual(len(parser.reviews), 1)
        self.assertEqual(parser.reviews[0]["review_id"], "758587")
        self.assertEqual(parser.reviews[0]["rating"], 2)
        self.assertIn("2주 사용", parser.reviews[0]["text"])
        self.assertEqual(len(parser.reviews[0]["images"]), 1)


class McpServerTests(unittest.TestCase):
    def test_stdio_mcp_lists_and_calls_tools(self):
        requests = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "review_cosmetic_claims",
                    "arguments": {"phrases": ["2주 만에 개선"]},
                },
            },
        ]
        payload = "\n".join(json.dumps(item, ensure_ascii=False) for item in requests) + "\n"
        result = subprocess.run(
            [sys.executable, str(SRC / "mcp" / "mediinsight_law_server.py")],
            input=payload,
            text=True,
            capture_output=True,
            check=True,
        )
        responses = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(responses[0]["result"]["serverInfo"]["name"], "mediinsight-law")
        self.assertEqual(len(responses[1]["result"]["tools"]), 2)
        findings = responses[2]["result"]["structuredContent"]["findings"]
        self.assertEqual(findings[0]["rule_id"], "COS-TIME-004")


class ProductionGuardTests(unittest.TestCase):
    def test_demo_requires_explicit_flag(self):
        with tempfile.TemporaryDirectory() as temp:
            result = subprocess.run(
                [
                    sys.executable,
                    str(SRC / "scripts" / "mediinsight_pipeline.py"),
                    "run",
                    "--input",
                    str(SRC / "examples" / "meditherapy_sample_input.json"),
                    "--out",
                    str(Path(temp) / "run"),
                ],
                text=True,
                capture_output=True,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Refusing demo data", result.stderr)


class ProjectStoreTests(unittest.TestCase):
    def test_urls_are_merged_and_remembered(self):
        with tempfile.TemporaryDirectory() as temp:
            store = Path(temp) / "projects.json"
            save_project(
                {
                    "project_id": "pdrn",
                    "product_name": "PDRN serum",
                    "channels": [{"name": "official", "url": "https://example.com/product"}],
                },
                store,
            )
            save_project(
                {
                    "project_id": "pdrn",
                    "product_name": "PDRN serum",
                    "channels": [{"name": "external", "url": "https://example.org/reviews"}],
                },
                store,
            )
            profile = get_project("pdrn", store)
        self.assertEqual(profile["project_id"], "pdrn")
        self.assertEqual([item["name"] for item in profile["channels"]], ["official", "external"])

    def test_risky_visual_claim_quarantines_product_image(self):
        with tempfile.TemporaryDirectory() as temp:
            image = Path(temp) / "product.jpg"
            image.write_bytes(b"image")
            findings = review_phrases(["불만족시 100% 환불보장"])
            decision = decide_asset_usage(
                {
                    "visual_claims": [
                        {"phrase": "불만족시 100% 환불보장", "source": "product_image"}
                    ]
                },
                findings,
                image,
            )
        self.assertEqual(decision["product_image"]["status"], "quarantined")

    def test_storyboards_are_four_scene_comics(self):
        carousels = build_carousels(
            [
                Insight(
                    id="insight",
                    title="루틴",
                    summary="사용 맥락",
                    evidence_ids=["review-001"],
                    confidence="low",
                    action="천천히 사용",
                )
            ],
            "PDRN 세럼",
            [
                Evidence(
                    id="review-001",
                    source="official",
                    type="customer_review",
                    text="아침 루틴으로 사용했습니다.",
                    signals={"routine_context": ["아침"]},
                )
            ],
        )
        self.assertEqual(len(carousels), 3)
        self.assertTrue(all(len(carousel.frames) == 4 for carousel in carousels))
        self.assertTrue(all(frame.scene and frame.speaker for carousel in carousels for frame in carousel.frames))

    def test_report_is_korean_and_reader_friendly(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "report.md"
            evidence = [
                Evidence(
                    id="review-001",
                    source="official",
                    type="customer_review",
                    text="민감성 피부로 2주 사용했습니다.",
                    skin_type="민감성",
                    usage_period="2주",
                    signals={"skin_types": ["민감성"], "usage_periods": ["2주"], "positives": ["좋"]},
                )
            ]
            write_report(
                path,
                "테스트 프로젝트",
                "PDRN 세럼",
                evidence,
                [],
                {
                    "review_count": 1,
                    "channel_counts": {"official": 1},
                    "repurchase_count": 0,
                    "skin_type_counts": {"민감성": 1},
                    "usage_period_counts": {"2주": 1},
                    "positive_counts": {"좋": 1},
                    "friction_counts": {},
                },
            )
            report = path.read_text(encoding="utf-8")
        self.assertIn("한눈에 보는 결과", report)
        self.assertIn("고객 관점에서 답한 네 가지 질문", report)
        self.assertNotIn("## Data Sources", report)

    def test_schema_org_reviews_are_collected_from_marketplace_html(self):
        dom = '''<script type="application/ld+json">{"@type":"Product","review":[{"reviewBody":"보습감이 좋고 재구매했습니다.","reviewRating":{"ratingValue":"5"},"author":{"name":"공개 사용자"}}]}</script>'''
        rows = extract_schema_reviews(
            dom,
            Channel(name="hwahae", type="external_review_page", url="https://example.com/product"),
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].rating, 5)
        self.assertEqual(rows[0].provenance, "chrome_rendered_schema_org_review")

    def test_risky_visual_claim_is_quarantined_even_when_download_failed(self):
        findings = review_phrases(["불만족시 100% 환불보장"])
        decision = decide_asset_usage(
            {
                "visual_claims": [
                    {"phrase": "불만족시 100% 환불보장", "source": "product_image"}
                ]
            },
            findings,
            None,
        )
        self.assertEqual(decision["product_image"]["status"], "quarantined")


if __name__ == "__main__":
    unittest.main()
