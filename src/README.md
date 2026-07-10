# MediInsight Plugin Source

This directory is the Codex plugin root.

MediInsight captures real rendered public pages and browser-visible reviews, normalizes evidence, produces a Korean reader-friendly report, creates three story-driven four-panel webtoon PNGs and one product-introduction PNG, then runs preliminary cosmetic-advertising QA through the bundled `mediinsight-law` MCP.

Save official-store and external-marketplace URLs once. They are remembered in the invoking workspace under `.mediinsight/projects.json` and merged when another channel is added:

```bash
python3 scripts/mediinsight_pipeline.py project save \
  --name meditherapy-pdrn \
  --product-name "메디테라피 PDRN 스킨부스터 세럼" \
  --channel official=https://meditherapy.co.kr/... \
  --channel external=https://...
```

The single `run` command performs rendered public review-iframe collection, duplicate removal, draft generation, MCP review, official citation reachability checks, compliant regeneration, mandatory PNG rendering and run-manifest creation:

```bash
python3 scripts/mediinsight_pipeline.py run \
  --project meditherapy-pdrn \
  --input examples/meditherapy_real_input.json \
  --out ../output/real-run
```

For the final visual pass, ask Codex to read `instagram/storyboards.json` and `instagram/imagegen_prompts.json`, then use built-in imagegen to create three connected text-free 2x2 webtoon background sheets and one clean product hero. The renderer adds the Law-MCP-reviewed Korean copy afterward, so do not ask imagegen to render Korean text directly:

```text
$mediinsight 저장된 meditherapy-pdrn 프로젝트로 분석하고,
스토리보드에 맞는 컷툰 4컷 이미지 3장과 제품 소개 이미지 1장을 만들어줘.
같은 인물과 분위기로 이어지게 하고, 최종 문구는 한글로 읽기 쉽게 넣어줘.
```

The included reproducible visual-input example is:

```bash
python3 scripts/mediinsight_pipeline.py run \
  --project meditherapy-pdrn \
  --input examples/meditherapy_visual_input.json \
  --out ../output/real-run
```

Expected final files are `output/real-run/instagram/carousel_01.png`, `carousel_02.png`, `carousel_03.png`, and `product_ad.png`. Inspect them together with `output/real-run/report/index.html`; a flat text grid is not considered a valid final result.

The repository also includes the latest verified sample output in `examples/outputs/meditherapy-pdrn/`. It was generated from `output/meditherapy-pdrn-comic-run-20260710/` with 12 public reviews across the saved official and Hwahae channels. The source product image's `불만족시 100% 환불보장` claim was quarantined by the bundled law MCP, so `product_ad.png` uses the generated clean product hero.

URL profiles persist by project name. To add or update one channel later, run `project save` again with the same `--name`; existing official and external URLs are kept in `.mediinsight/projects.json`.

The MCP runs locally without an API key and returns findings with official Korean legal and MFDS source links. Citation reachability is recorded separately and does not replace legal review. Review image URLs are exported for constrained Codex VLM transcription. A risky VLM-transcribed claim inside a source product image quarantines that image from the final ad. Missing required PNGs fail the run instead of silently reporting success. The demo fixture requires the explicit `--allow-demo` flag.
