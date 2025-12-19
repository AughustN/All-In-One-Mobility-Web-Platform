## What this repo is

This repository is a LaTeX project for a CISUC internal call / project proposal. The single entry point is `0-main.tex` which sets document metadata (e.g. `\thesistype`, `\docLanguage`), loads the preamble, and `\input{}`s the frontmatter and `text/` sections.

Key folders/files
- `0-main.tex` — project root and build/preamble. Edit top-level metadata here (title, author, date, language).
- `frontmatter/` — cover, title page, abstract, acronyms. Example: `frontmatter/1-coverpage.tex` is included by the main file.
- `text/` — the main content chapters: `1-Excellence.tex`, `2-Impact.tex`, `3-Implementation.tex` are pulled via `\input{}`.
- `figures/` — images and assets referenced from frontmatter or chapters.
- `references.bib` — bibliography database used by `\bibliography{references}` and `natbib`/`apalike`.

Build & typical commands
- Build a PDF (recommended):
  - `latexmk -pdf -interaction=nonstopmode 0-main.tex` — preferred; runs BibTeX and multiple passes automatically.
  - Alternative: `pdflatex 0-main.tex && bibtex 0-main && pdflatex 0-main.tex && pdflatex 0-main.tex`
- Clean build artifacts: `latexmk -C` (run in repo root).
- If images fail to appear, check relative paths in `frontmatter/` (images are referred to with paths like `frontmatter/<name>.png`).

CI / Automated builds
- This repo includes an optional GitHub Actions workflow at `.github/workflows/latex.yml` that runs on push and pull requests to build `0-main.tex` and upload the generated `0-main.pdf` as an artifact. If you modify CI behaviour, update that workflow file.

Conventions and patterns to follow
- Small modular chapters: Add new content by creating a `text/<n>-MySection.tex` file and adding `\input{text/<n>-MySection}` to `0-main.tex` in the desired order.
- Metadata flags: `0-main.tex` uses macros such as `\thesistype` (`msc`/`phd`) and `\docLanguage` (`en`/`pt`). Change these at the top of `0-main.tex` rather than editing the generated title pages manually.
- Keep the preamble in `0-main.tex`. Preamble contains package imports, page geometry, glossary setup, and bibliographystyle; avoid duplicating those settings in chapter files.
- Bibliography: single `references.bib` file; the project uses `natbib` and `\bibliographystyle{apalike}`. Add BibTeX entries to `references.bib` and use `\cite{key}` in tex files.

Debugging LaTeX failures
- Check the `.log` file (same basename as the tex root, e.g. `0-main.log`) for error lines and missing file names.
- If LaTeX stops on the first error, run `latexmk -pdf -interaction=nonstopmode 0-main.tex` to get a full build run; inspect `.blg`/`.bbl` for bibliography problems.
- Common problems in this repo: missing frontmatter images, wrong `\input{}` paths, or UTF-8 encoding issues. `0-main.tex` already sets `\usepackage[utf8]{inputenc}` and `T1` fonts.

Small edit examples (copy/paste)
- Add a new chapter file and include it:
  - Create `text/4-Dissemination.tex` with `\chapter{Dissemination}` and content.
  - Add to `0-main.tex`: `\input{text/4-Dissemination}` just after other `\input{}` lines.
- Update title/author/date (edit only the top section of `0-main.tex` near the CONFIGURATION comment block): change `\def\titleEN{...}`, `\def\author{...}`, `\def\dateEN{...}`.

What NOT to change
- Avoid restructuring the preamble unless you understand LaTeX package interactions; small changes can break compilation across different TeX installations.
- Don’t move `references.bib` without updating `\bibliography{}` in `0-main.tex`.

Integration points & external deps
- The project relies on a standard TeX toolchain (pdfLaTeX, BibTeX, latexmk). No external CI is configured in the repo.
- Images and logos live in `frontmatter/` and `figures/`; keep these under version control to ensure reproducible builds.

If you're an AI assistant working on this repo
- Read `0-main.tex` first — it encodes the document contract and includes all key inputs.
- When changing text, make edits in `text/*.tex` or `frontmatter/*.tex` and run the build command above to verify output.
- For suggestions that alter formatting (preamble, packages), provide a small diff and a short justification; prefer additive/non-destructive changes.

Questions or missing details
- If you need CI build commands, platform-specific TeX installation notes, or a packaging step, ask the repo maintainer (there's a contact comment at the top of `0-main.tex`).

— End of instructions —
