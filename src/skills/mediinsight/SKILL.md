---
name: mediinsight
description: Collect real public Meditherapy product pages and customer reviews with a browser, analyze skin type, usage period, friction and repurchase signals, generate an evidence-backed report plus three four-panel Instagram PNGs and one product ad PNG, and review visible marketing copy with the bundled cosmetic-law MCP. Use for Meditherapy public customer-voice analysis, Instagram content production, URL-based cosmetic review research, or Korean cosmetic advertising copy QA.
---

# MediInsight

Execute the complete evidence-to-content workflow. Never substitute demo reviews when live collection fails.

## Required workflow

1. Check `.mediinsight/projects.json` with `project show` before asking for URLs. If the product profile exists, reuse every saved official-store and external-marketplace URL without asking again.
2. When the user supplies a URL for the first time or changes one, immediately persist it with `project save`. Merge new channels into the existing profile; never discard previously saved channels unless the user explicitly asks.
3. Use the in-app Browser or Chrome to open every saved URL. Read [browser-collection.md](references/browser-collection.md) before collecting. The runtime automatically follows public Crema `list_v3` review iframes for up to `max_review_pages` pages, reads public Schema.org `Review` JSON-LD when a marketplace exposes it, and records rendered review text, ratings and media URLs.
4. Save any additional browser-visible reviews with source URL, capture time, channel, visible text, rating when shown, skin type when explicit, and usage period when explicit. The collector canonicalizes matching URLs and removes exact normalized duplicates.
5. Capture the rendered product page and collect a product image. After collection, inspect `evidence/review_media_manifest.json`. Use VLM only for a small relevant sample to transcribe visible text and describe layout or product placement. Never infer skin diagnosis, efficacy or identity from review images. Store transcribed advertising copy in `visual_claims`.
6. Create a run input JSON using the schema in [browser-collection.md](references/browser-collection.md). The input may omit channels when `--project` supplies the saved profile. Do not set `demo: true`.
7. Run the complete workflow. This collects real public pages, creates the Korean report and storyboards, invokes the bundled law MCP over every carousel title/body and product-ad phrase, regenerates corrected copy, quarantines risky source imagery, and writes a run manifest:

```bash
python3 scripts/mediinsight_pipeline.py run \
  --project <saved-project-name> \
  --input <run-input.json> \
  --out <output-directory>
```
8. Read `instagram/storyboards.json` and `instagram/imagegen_prompts.json`. Use the built-in imagegen capability, without an API key, to generate three text-free 2x2 webtoon sheets and one clean product hero. Keep the same character across each sheet. Do not ask imagegen to render Korean text; the Python renderer must overlay the Law-MCP-reviewed Korean copy exactly.
9. Save the generated sheets under `<output-directory>/generated/`. Add their paths to the resolved run input as `comic_background_paths` in carousel order, and add the clean product image path as `product_hero_path`. Regenerate using the existing `raw_evidence.json` and `law_mcp_results.json`; do not recollect or replace real evidence for this visual pass.
10. Inspect `run_manifest.json`, `evidence/collection_stats.json`, and `compliance/source_verification.json`. If `data_quality.status` is `limited`, state the exact review/channel limitation instead of presenting the report as conclusive. Treat an unreachable official citation as a verification warning, not proof that the source is invalid.
11. Open `report/index.html` and visually inspect all four PNG files. Final delivery requires three genuine 4-panel story comics plus one product introduction image. Flat text grids are not acceptable. Fix overflow, unreadable text, missing product imagery, unsupported claims and broken interactions before reporting completion.

## Remember URLs

On the first request, save the user's official and external URLs:

```bash
python3 scripts/mediinsight_pipeline.py project save \
  --name meditherapy-pdrn \
  --product-name "메디테라피 PDRN 스킨부스터 세럼" \
  --channel official=https://meditherapy.co.kr/... \
  --channel external=https://...
```

On later requests, run `project show --name meditherapy-pdrn` and use that profile. Ask for URLs only when no saved profile exists or the user explicitly changes the target product.

## Required output

- `report/mediinsight_report.md`
- `report/index.html`
- `report/metrics.json`
- `evidence/evidence.json`
- `evidence/collection_stats.json`
- `evidence/review_media_manifest.json`
- `captures/<channel>.png`
- `instagram/carousel_01.png`
- `instagram/carousel_02.png`
- `instagram/carousel_03.png`
- `instagram/product_ad.png`
- `instagram/storyboards.json`
- `instagram/imagegen_prompts.json`
- `compliance/pending_claims.json`
- `compliance/risk_findings.json`
- `compliance/before_after.json`
- `compliance/compliance_report.md`
- `compliance/asset_decisions.json`
- `compliance/source_verification.json`
- `run/resolved_input.json`
- `run_manifest.json`

## Evidence rules

- Distinguish live public reviews from user-provided text and demo fixtures.
- Keep every URL and capture timestamp.
- Cite evidence ids in every insight and generated frame.
- Report sample size and use low confidence below 10 reviews.
- Preserve fetch errors as errors; never count them as customer evidence.
- Treat the compliance result as preliminary review, not legal advice.

Read [law-review.md](references/law-review.md) when explaining legal findings or MCP fallback behavior.
