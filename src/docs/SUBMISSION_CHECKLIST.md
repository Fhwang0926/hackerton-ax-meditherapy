# Submission Checklist

- [x] `src/.codex-plugin/plugin.json`
- [x] executable `skills/mediinsight/SKILL.md`
- [x] API-key-free bundled `mediinsight-law` MCP
- [x] real public product input with URL and capture provenance
- [x] real rendered page capture
- [x] evidence-backed Markdown report and metrics JSON
- [x] three 1080x1080 four-panel carousel PNGs
- [x] one 1080x1080 product-ad PNG
- [x] original/revised compliance records
- [ ] original unedited AI conversation logs supplied by the entrant
- [ ] five submission questionnaire answers supplied with the final form
- [ ] final `submission.zip` built after logs are present

Run validation before packaging:

```bash
python3 ../.codex/skills/.system/plugin-creator/scripts/validate_plugin.py src
python3 ../.codex/skills/.system/skill-creator/scripts/quick_validate.py src/skills/mediinsight
python3 -m unittest discover -s tests -v
```
