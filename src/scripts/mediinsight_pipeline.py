#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mediinsight.compliance import load_external_findings, review_phrases
from mediinsight.content import (
    all_copy,
    apply_compliance,
    build_carousels,
    build_imagegen_prompts,
    render_png,
    write_product_ad,
    write_svg_carousel,
)
from mediinsight.crawler import (
    download_public_asset,
    fetch_embedded_reviews,
    fetch_public_page,
    extract_schema_reviews,
    find_chrome,
    normalize_manual_review,
)
from mediinsight.evidence import build_insights, build_metrics, deduplicate_reviews, enrich_evidence
from mediinsight.models import Channel, Evidence, RawReview
from mediinsight.law_client import review_with_bundled_mcp, verify_legal_sources
from mediinsight.project_store import (
    DEFAULT_STORE,
    get_project,
    list_projects,
    merge_config,
    save_project,
)
from mediinsight.report import write_compliance_report, write_html_report, write_report
from mediinsight.utils import ensure_dir, read_json, slugify, write_json


def collect(config_source: Path | dict[str, Any], out_dir: Path) -> list[Evidence]:
    config = load_config_source(config_source)
    evidence: list[Evidence] = []
    capture_dir = out_dir / "captures"
    channel_by_url = {
        channel_data["url"]: channel_data["name"]
        for channel_data in config.get("channels", [])
    }
    for channel_data in config.get("channels", []):
        channel = Channel(
            name=channel_data["name"],
            type=channel_data.get("type", "public_page"),
            url=channel_data["url"],
        )
        page_evidence = fetch_public_page(channel, capture_dir=capture_dir)
        evidence.append(page_evidence)
        chrome = find_chrome()
        if chrome and page_evidence.type != "page_fetch_error":
            evidence.extend(
                fetch_embedded_reviews(
                    channel,
                    page_evidence,
                    capture_dir,
                    chrome,
                    max_pages=int(config.get("max_review_pages", 2)),
                )
            )
            html_path = capture_dir / f"{channel.name}.html"
            if html_path.exists():
                evidence.extend(
                    extract_schema_reviews(html_path.read_text(encoding="utf-8"), channel)
                )

    for index, review_data in enumerate(config.get("reviews", config.get("manual_reviews", [])), start=1):
        review = RawReview(
            channel=channel_by_url.get(
                review_data.get("url"),
                review_data.get("channel", "manual"),
            ),
            text=review_data["text"],
            rating=review_data.get("rating"),
            skin_type=review_data.get("skin_type"),
            usage_period=review_data.get("usage_period"),
            url=review_data.get("url"),
            captured_at=review_data.get("captured_at"),
            provenance=review_data.get("provenance", "user_or_browser_verified_review"),
        )
        evidence.append(normalize_manual_review(index, review))

    product_image_url = config.get("product_image_url")
    if product_image_url:
        suffix = Path(str(product_image_url).split("?", 1)[0]).suffix or ".jpg"
        try:
            download_public_asset(
                product_image_url,
                capture_dir / f"product_image{suffix}",
            )
            error_path = capture_dir / "product_image_error.json"
            if error_path.exists():
                error_path.unlink()
        except Exception as exc:
            write_json(
                capture_dir / "product_image_error.json",
                {"url": product_image_url, "error": str(exc)},
            )

    evidence, duplicates = deduplicate_reviews(evidence)
    write_json(out_dir / "evidence" / "raw_evidence.json", evidence)
    write_json(
        out_dir / "evidence" / "collection_stats.json",
        {
            "evidence_count": len(evidence),
            "review_count": sum(item.type == "customer_review" for item in evidence),
            "duplicate_count": len(duplicates),
            "duplicates": duplicates,
        },
    )
    write_json(
        out_dir / "evidence" / "review_media_manifest.json",
        [
            {
                "evidence_id": item.id,
                "source": item.source,
                "review_url": item.url,
                "image_url": image_url,
                "vlm_status": "pending",
                "allowed_analysis": ["visible_text_transcription", "layout", "product_presence"],
                "prohibited_analysis": ["skin_diagnosis", "efficacy_judgment", "identity_inference"],
            }
            for item in evidence
            if item.type == "customer_review"
            for image_url in item.signals.get("image_urls", [])
        ],
    )
    return evidence


def evidence_from_json(path: Path) -> list[Evidence]:
    return [Evidence(**item) for item in read_json(path)]


def generate(
    config_source: Path | dict[str, Any],
    evidence_path: Path,
    out_dir: Path,
    law_results_path: Path | None = None,
    allow_demo: bool = False,
) -> None:
    config = load_config_source(config_source)
    assert_production_input(config, allow_demo)

    project = config.get("project", "MediInsight project")
    product_name = config.get("product_name", "Meditherapy product")
    evidence = enrich_evidence(evidence_from_json(evidence_path))
    valid_reviews = [item for item in evidence if item.type == "customer_review" and item.text.strip()]
    if not valid_reviews:
        raise SystemExit(
            "No verified customer reviews were collected. Add browser-visible reviews with source URLs before generation."
        )

    metrics = build_metrics(evidence)
    insights = build_insights(evidence, product_name)
    original_carousels = build_carousels(insights, product_name, evidence)
    original_phrases = all_copy(original_carousels, product_name)
    original_phrases.extend(
        str(item["phrase"])
        for item in config.get("visual_claims", [])
        if item.get("phrase")
    )
    findings = (
        load_external_findings(read_json(law_results_path))
        if law_results_path
        else review_phrases(original_phrases)
    )
    carousels = apply_compliance(deepcopy(original_carousels), findings)

    ensure_dir(out_dir)
    write_json(out_dir / "evidence" / "evidence.json", evidence)
    write_json(out_dir / "report" / "metrics.json", metrics)
    write_json(out_dir / "report" / "insights.json", insights)
    write_json(out_dir / "instagram" / "storyboards.json", original_carousels)
    write_json(
        out_dir / "instagram" / "imagegen_prompts.json",
        build_imagegen_prompts(original_carousels, product_name),
    )
    write_json(out_dir / "compliance" / "pending_claims.json", build_pending_claims(original_phrases))
    write_json(out_dir / "compliance" / "risk_findings.json", findings)
    write_json(
        out_dir / "compliance" / "before_after.json",
        build_before_after(original_phrases, findings),
    )
    write_report(
        out_dir / "report" / "mediinsight_report.md",
        project,
        product_name,
        evidence,
        insights,
        metrics,
    )
    write_compliance_report(out_dir / "compliance" / "compliance_report.md", findings)
    write_html_report(
        out_dir / "report" / "index.html",
        project,
        product_name,
        evidence,
        insights,
        metrics,
        findings,
    )

    comic_backgrounds = [Path(value).expanduser() for value in config.get("comic_background_paths", [])]
    for index, carousel in enumerate(carousels):
        svg_path = out_dir / "instagram" / f"{carousel.id}.svg"
        comic_background = comic_backgrounds[index] if index < len(comic_backgrounds) else None
        write_svg_carousel(svg_path, carousel, product_name, comic_background)
        require_png(svg_path)

    image_value = config.get("product_image_path")
    product_image = Path(image_value).expanduser() if image_value else find_captured_product_image(out_dir)
    asset_decisions = decide_asset_usage(config, findings, product_image)
    if asset_decisions["product_image"]["status"] == "quarantined":
        product_image = None
    hero_value = config.get("product_hero_path")
    product_hero = Path(hero_value).expanduser() if hero_value else None
    write_json(out_dir / "compliance" / "asset_decisions.json", asset_decisions)
    ad_path = out_dir / "instagram" / "product_ad.svg"
    write_product_ad(
        ad_path,
        product_name,
        "재구매 리뷰에서 확인한 루틴 경험",
        product_image,
        product_hero,
    )
    require_png(ad_path)
    write_instagram_text(out_dir / "instagram", product_name, insights)


def find_captured_product_image(out_dir: Path) -> Path | None:
    candidates = sorted((out_dir / "captures").glob("product_image.*"))
    return candidates[0] if candidates else None


def require_png(svg_path: Path) -> Path:
    png_path = render_png(svg_path)
    if not png_path:
        raise RuntimeError(
            f"Required PNG was not rendered from {svg_path}. Install or allow headless Chrome, then rerun."
        )
    return png_path


def decide_asset_usage(config: dict, findings, product_image: Path | None) -> dict:
    risky_visual_claims = []
    for claim in config.get("visual_claims", []):
        phrase = str(claim.get("phrase", "")).strip()
        matching = [
            finding
            for finding in findings
            if finding.phrase == phrase and finding.severity in {"high", "medium"}
        ]
        if matching and claim.get("source") == "product_image":
            risky_visual_claims.append(
                {
                    "phrase": phrase,
                    "finding_ids": [finding.claim_id for finding in matching],
                    "reason": "제품 이미지 내부 문구가 법률 검수에서 위험 표현으로 분류됨",
                }
            )
    if risky_visual_claims:
        status = "quarantined"
    elif product_image:
        status = "approved"
    else:
        status = "unavailable"
    return {
        "product_image": {
            "path": str(product_image) if product_image else None,
            "status": status,
            "action": (
                "원본을 최종 홍보물에서 제외하고 안전한 제품 실루엣으로 대체"
                if status == "quarantined"
                else "최종 홍보물에 사용" if status == "approved" else "안전한 제품 실루엣 사용"
            ),
            "risks": risky_visual_claims,
        }
    }


def assert_production_input(config: dict, allow_demo: bool) -> None:
    if config.get("demo") and not allow_demo:
        raise SystemExit("Refusing demo data. Use real public evidence or pass --allow-demo explicitly.")


def load_config_source(source: Path | dict[str, Any]) -> dict[str, Any]:
    return read_json(source) if isinstance(source, Path) else dict(source)


def resolve_run_config(
    input_path: Path | None,
    project_name: str | None,
    store_path: Path,
) -> dict[str, Any]:
    supplied = read_json(input_path) if input_path else {}
    if project_name:
        try:
            supplied = merge_config(get_project(project_name, store_path), supplied)
        except KeyError as exc:
            raise SystemExit(str(exc)) from exc
    if not supplied:
        raise SystemExit("Provide --input or --project. URLs saved once can be reused with --project.")
    if not supplied.get("channels"):
        raise SystemExit("No public channel URLs configured. Save at least one product or marketplace URL.")
    save_project(supplied, store_path)
    return supplied


def parse_channel(value: str) -> dict[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("Channel must use NAME=URL format.")
    name, url = value.split("=", 1)
    if not name.strip() or not url.startswith(("http://", "https://")):
        raise argparse.ArgumentTypeError("Channel must include a name and public HTTP(S) URL.")
    return {"name": name.strip(), "type": "public_page", "url": url.strip()}


def quality_summary(evidence: list[Evidence]) -> dict[str, Any]:
    reviews = [item for item in evidence if item.type == "customer_review" and item.text.strip()]
    channels = sorted({item.source for item in reviews})
    warnings = []
    if len(reviews) < 10:
        warnings.append("리뷰가 10건 미만이므로 인사이트 신뢰도는 low입니다.")
    if len(channels) < 2:
        warnings.append("고객 리뷰 채널이 2개 미만이므로 채널 간 편향 비교가 제한됩니다.")
    return {
        "review_count": len(reviews),
        "review_channels": channels,
        "channel_count": len(channels),
        "status": "ready" if len(reviews) >= 10 and len(channels) >= 2 else "limited",
        "warnings": warnings,
    }


def run_workflow(config: dict[str, Any], out_dir: Path, law_results: Path | None, allow_demo: bool) -> None:
    started_at = datetime.now(timezone.utc).isoformat()
    assert_production_input(config, allow_demo)
    ensure_dir(out_dir)
    write_json(out_dir / "run" / "resolved_input.json", config)
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "project": config.get("project"),
        "product_name": config.get("product_name"),
        "started_at": started_at,
        "steps": [],
    }
    try:
        evidence = collect(config, out_dir)
        raw_path = out_dir / "evidence" / "raw_evidence.json"
        manifest["steps"].append({"name": "collect", "status": "completed"})
        manifest["data_quality"] = quality_summary(evidence)

        generate(config, raw_path, out_dir, None, allow_demo)
        manifest["steps"].append({"name": "draft", "status": "completed"})

        final_law_results = law_results or out_dir / "compliance" / "law_mcp_results.json"
        if law_results is None:
            law_findings = review_with_bundled_mcp(
                ROOT / "mcp" / "mediinsight_law_server.py",
                out_dir / "compliance" / "pending_claims.json",
                final_law_results,
            )
        else:
            law_findings = read_json(final_law_results)
        manifest["steps"].append(
            {"name": "law_mcp_review", "status": "completed", "result": str(final_law_results)}
        )

        source_verification = verify_legal_sources(law_findings)
        source_verification_path = out_dir / "compliance" / "source_verification.json"
        write_json(source_verification_path, source_verification)
        manifest["steps"].append(
            {
                "name": "legal_source_verification",
                "status": "completed",
                "reachable": sum(item["status"] == "reachable" for item in source_verification),
                "unreachable": sum(item["status"] != "reachable" for item in source_verification),
                "result": str(source_verification_path),
            }
        )

        generate(config, raw_path, out_dir, final_law_results, allow_demo)
        manifest["steps"].append({"name": "finalize", "status": "completed"})
        manifest["status"] = "completed"
    except (Exception, SystemExit) as exc:
        manifest["status"] = "failed"
        manifest["error"] = str(exc)
        raise
    finally:
        manifest["finished_at"] = datetime.now(timezone.utc).isoformat()
        manifest["outputs"] = {
            "report": str(out_dir / "report" / "index.html"),
            "report_markdown": str(out_dir / "report" / "mediinsight_report.md"),
            "instagram": str(out_dir / "instagram"),
            "compliance": str(out_dir / "compliance" / "compliance_report.md"),
        }
        write_json(out_dir / "run_manifest.json", manifest)


def build_pending_claims(phrases: list[str]) -> list[dict]:
    return [
        {
            "claim_id": f"claim-{index:03d}",
            "phrase": phrase,
            "requested_sources": ["화장품법", "화장품 표시광고 지침", "식약처 공식 자료"],
        }
        for index, phrase in enumerate(phrases, start=1)
    ]


def build_before_after(phrases: list[str], findings) -> list[dict]:
    revised = []
    for phrase in phrases:
        matching = [finding for finding in findings if finding.phrase == phrase]
        after = phrase
        for finding in matching:
            after = finding.revised_phrase or after
        revised.append(
            {
                "before": phrase,
                "after": after,
                "changed": phrase != after,
                "finding_ids": [finding.claim_id for finding in matching],
            }
        )
    return revised


def write_instagram_text(path: Path, product_name: str, insights) -> None:
    ensure_dir(path)
    caption = [
        f"{product_name} 공개 리뷰에서 발견한 사용 루틴 신호를 정리했습니다.",
        "",
        "실제 고객이 공개 채널에 남긴 사용 기간과 루틴 경험을 바탕으로 만든 콘텐츠 초안입니다.",
        "개인차가 있을 수 있으며 최종 게시 전 광고·법무 검수가 필요합니다.",
        "",
        "근거 인사이트:",
    ]
    for insight in insights:
        caption.append(f"- {insight.title} ({', '.join(insight.evidence_ids[:3])})")
    (path / "caption.md").write_text("\n".join(caption) + "\n", encoding="utf-8")
    (path / "hashtags.md").write_text(
        "#메디테라피 #피부루틴 #화장품리뷰 #스킨케어루틴 #고객리뷰 #뷰티콘텐츠\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect real public evidence and generate MediInsight assets.")
    sub = parser.add_subparsers(dest="command", required=True)

    collect_parser = sub.add_parser("collect", help="Capture configured public URLs and supplied verified reviews.")
    collect_parser.add_argument("--input", type=Path)
    collect_parser.add_argument("--project")
    collect_parser.add_argument("--store", type=Path, default=DEFAULT_STORE)
    collect_parser.add_argument("--out", required=True, type=Path)

    generate_parser = sub.add_parser("generate", help="Generate report and assets from collected evidence.")
    generate_parser.add_argument("--input", required=True, type=Path)
    generate_parser.add_argument("--evidence", required=True, type=Path)
    generate_parser.add_argument("--out", required=True, type=Path)
    generate_parser.add_argument("--law-results", type=Path)
    generate_parser.add_argument("--allow-demo", action="store_true")

    run_parser = sub.add_parser("run", help="Collect and generate in one command.")
    run_parser.add_argument("--input", type=Path)
    run_parser.add_argument("--project")
    run_parser.add_argument("--store", type=Path, default=DEFAULT_STORE)
    run_parser.add_argument("--out", required=True, type=Path)
    run_parser.add_argument("--law-results", type=Path)
    run_parser.add_argument("--allow-demo", action="store_true")

    project_parser = sub.add_parser("project", help="Remember and reuse product/channel URLs.")
    project_sub = project_parser.add_subparsers(dest="project_command", required=True)
    project_save = project_sub.add_parser("save")
    project_save.add_argument("--name", required=True)
    project_save.add_argument("--product-name", required=True)
    project_save.add_argument("--channel", action="append", type=parse_channel, default=[])
    project_save.add_argument("--product-image-url")
    project_save.add_argument("--store", type=Path, default=DEFAULT_STORE)
    project_show = project_sub.add_parser("show")
    project_show.add_argument("--name", required=True)
    project_show.add_argument("--store", type=Path, default=DEFAULT_STORE)
    project_list = project_sub.add_parser("list")
    project_list.add_argument("--store", type=Path, default=DEFAULT_STORE)
    args = parser.parse_args()

    if args.command == "collect":
        config = resolve_run_config(args.input, args.project, args.store)
        collect(config, args.out)
    elif args.command == "generate":
        generate(args.input, args.evidence, args.out, args.law_results, args.allow_demo)
    elif args.command == "run":
        config = resolve_run_config(args.input, args.project, args.store)
        run_workflow(config, args.out, args.law_results, args.allow_demo)
    elif args.command == "project":
        if args.project_command == "save":
            profile = save_project(
                {
                    "project_id": args.name,
                    "project": args.name,
                    "product_name": args.product_name,
                    "channels": args.channel,
                    "product_image_url": args.product_image_url,
                },
                args.store,
            )
            print(json.dumps(profile, ensure_ascii=False, indent=2))
        elif args.project_command == "show":
            print(json.dumps(get_project(args.name, args.store), ensure_ascii=False, indent=2))
        elif args.project_command == "list":
            print(json.dumps(list_projects(args.store), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
