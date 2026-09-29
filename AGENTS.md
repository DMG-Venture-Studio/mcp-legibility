# Agent instructions

The canonical instructions for working in this repository are in
[CLAUDE.md](CLAUDE.md): what the tool is, the layout, the rules (single-file
scripts with inline dependencies, never run the headless trial implicitly,
scoring stays a judgement, no personal names, no emojis), and where to change
what. Read it first. The audit procedure itself is
`skills/legibility-audit/SKILL.md`.

```sh
python3 -m unittest discover -s tests -v     # tests
uv run --script mcp/server.py --selftest      # the server audits this repo
```
