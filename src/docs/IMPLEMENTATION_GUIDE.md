# Implementation Guide

Use `skills/mediinsight/SKILL.md` as the executable orchestration contract.

The runtime has four boundaries:

1. Codex Browser collects visible public reviews, source URLs, screenshots, product imagery and VLM-transcribed image copy.
2. `mediinsight_pipeline.py collect` captures rendered pages and normalizes supplied browser evidence.
3. `mediinsight_pipeline.py generate` computes metrics, writes the report and renders SVG plus PNG assets.
4. The bundled `mediinsight-law` MCP reviews `pending_claims.json`; a second generate pass records its findings and before/after copy.

Production generation requires at least one verified customer review. Demo inputs require `--allow-demo`.

```bash
python3 scripts/mediinsight_pipeline.py run \
  --input examples/meditherapy_real_input.json \
  --out ../output/real-run
```
