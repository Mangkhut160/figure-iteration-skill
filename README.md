# figure-iteration skill

A reusable skill (SKILL.md format, built and tested with Claude Code) for iterating scripted vector paper figures that the author hand-edits as `.pptx` (WPS / PowerPoint) and delivers as PDF. Each round patches a copy of the author's latest saved deck, never regenerates over their edits, then renders, audits and hands over PDF / PNG / pptx.

The skill holds no paper-specific rules. A paper's page width, fonts, colours, terms and red lines live in that paper's own `figure-profile.md`, found by walking up from the figure folder; switching papers means writing a new profile, not editing the skill. The documentation is written in Chinese.

## Contents

- `SKILL.md` — entry point: the red lines and the steps of one iteration round.
- `references/` — how to iterate on a saved deck, draft from scratch, fill a data panel, sync text with the paper, talk to the author, start a new paper, set up the environment.
- `scripts/` — the patching kit (`pptx_kit.py`), the `make_from_saved.sh` and `make_draft.sh` pipelines, renderers and audits.
- `templates/` — profile and `figure.env` templates, patch and from-scratch skeletons, forms for the author to fill in.

## Install

Copy the repository into a skills directory as `figure-iteration`, for example `<project>/.claude/skills/figure-iteration` or `~/.claude/skills/figure-iteration`.

## First use on a paper

1. Read `references/new-paper.md`: copy `templates/profile_template.md` to the paper's `figure-profile.md`, measure the column width with the paper's LaTeX class, and write the figure's `figure.env`.
2. `bash scripts/make_from_saved.sh --check` reports which tools are missing.
3. Dry run with `scripts/make_test_deck.py`.

## Requirements

Python with python-pptx, lxml, Pillow, numpy and PyMuPDF; LibreOffice (rendering); TeX Live (formulas). Optional: the figgenie-paper-diagram skill (drafting from scratch, `K.formula`). How each tool is found, and the environment variables, are in `references/toolchain.md`.

## Status

- Tested on Windows + Git Bash only; macOS and Linux are untested.
- The from-scratch skeleton covers boxes, edges, formulas and a legend; bitmaps and containers are not covered.
- Built from one real paper's figure and checked on a fictitious second paper; not yet used on another real one.

## License

No license file is included yet. Add the license appropriate for your use before redistributing the repository.
