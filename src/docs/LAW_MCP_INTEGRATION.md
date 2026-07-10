# Bundled Law MCP

`src/.mcp.json` launches `src/mcp/mediinsight_law_server.py`. No external API key is required.

The server exposes:

- `review_cosmetic_claims`: preliminary findings, revised copy and official citations.
- `search_cosmetic_ad_law`: official sources used by the rules.

The rules cite the National Law Information Center for Cosmetics Act Articles 13 and 14 and the Ministry of Food and Drug Safety cosmetic labeling and advertising guide, 안내서-0086-07.

The pipeline exports `compliance/pending_claims.json`. Codex passes those phrases to the MCP tool, saves its `findings` array as `law_mcp_results.json`, then regenerates with `--law-results`. Original and revised text remain in `before_after.json`.

This is a preliminary advertising QA gate and does not replace legal advice or final review against the product's substantiation documents.
