# Project Structure

```text
src/
├── .codex-plugin/plugin.json
├── .mcp.json
├── mcp/mediinsight_law_server.py
├── skills/mediinsight/
│   ├── SKILL.md
│   ├── agents/openai.yaml
│   └── references/
├── scripts/mediinsight_pipeline.py
├── mediinsight/
└── examples/
    ├── meditherapy_real_input.json
    └── meditherapy_sample_input.json
```

The plugin uses the bundled MCP, Browser/Chrome for rendered public evidence, and Python standard-library runtime code. Chrome is also used to render the final 1080x1080 PNG files from editable SVG sources.
