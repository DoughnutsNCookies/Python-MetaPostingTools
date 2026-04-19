# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo does

Two CLI tools for managing Schuah Solutions content:

- **`convert.py`** — Converts a PNG blog cover image to WEBP and saves it to the landing page's `public/blogs/` directory
- **`post.py`** — Schedules an image post to Facebook and Instagram via Meta Business Suite (Playwright browser automation), targeting the coming Tuesday at 10:00 AM MYT
- **`setup.py`** — One-time login helper: opens a browser for manual Meta login + 2FA, then saves the session to `session.json` for reuse

## Setup

```bash
py -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

Create `.env` from `.env.example`. Run `setup.py` once to authenticate.

## Usage

```bash
# Convert PNG to WEBP
python convert.py "C:\path\to\image.png" <slug>

# For a worktree branch (so image lands on the right branch):
python convert.py "C:\path\to\image.png" <slug> --target "C:\Code\WebApp-SchuahSolutions-WebDevLandingPage\.claude\worktrees\<worktree-name>\landing-page\public\blogs"

# Schedule a social media post
python post.py "C:\path\to\image.png" <slug> --caption-file caption.txt
```

## Blog Publishing Workflow

The user sends only the blog markdown content. Claude handles everything else automatically.

### Step 1 — Export images from Canva (Claude does this via MCP)

Two Canva designs are always kept up to date — page 1 of each is always the latest blog:

| Design | Canva ID | Purpose |
|--------|----------|---------|
| Blog Cover Image | `DAGeyipWBWU` | Converted to WEBP for the website |
| Social Media Post | `DAGal3LsJUo` | Posted to Facebook + Instagram |

Export page 1 of both as PNG using the Canva MCP `export-design` tool, then download each to a temp path (e.g. `C:\Users\schuah\AppData\Local\Temp\blog-cover.png` and `C:\Users\schuah\AppData\Local\Temp\social-post.png`).

### Step 2 — Save the blog markdown to a temp file

Write the markdown content the user provided to a temp file (e.g. `C:\Users\schuah\AppData\Local\Temp\blog.md`).

### Step 3 — Run publish.py

```bash
cd "C:\Code\Python-MetaPostingTools"
venv\Scripts\activate
python publish.py "C:\Users\schuah\AppData\Local\Temp\blog.md" "C:\Users\schuah\AppData\Local\Temp\blog-cover.png" --worktree "C:\Code\WebApp-SchuahSolutions-WebDevLandingPage\.claude\worktrees\<worktree-name>"
```

### Step 4 — Run post.py

Write the social media caption to `caption.txt`, then:

```bash
python post.py "C:\Users\schuah\AppData\Local\Temp\social-post.png" <slug> --caption-file caption.txt
```

### Step 5 — After user merges the PR, sync the worktree branch

```bash
git fetch origin main && git merge origin/main --no-edit && git push origin HEAD:<branch-name>
```

### Blog markdown format

```yaml
---
title: "Post Title"
description: "Short description for meta and card preview"
slug: "post-slug"
date: "DD MONTH YYYY"
---

Content here...
```

---

## Key implementation details

**`convert.py`** — TARGET_DIR is hardcoded to the main landing page path. Use `--target` to override for worktree branches. Default quality is 82; use `--force` to overwrite an existing slug.

**`post.py`** — Uses `session.json` (saved by `setup.py`) to restore the Meta Business Suite browser session without re-authenticating. Schedules for the next Tuesday at 10:00 AM MYT (`Asia/Kuala_Lumpur`). Appends the blog link (`https://schuahsolutions.com/blogs/<slug>`) to the Facebook caption automatically. Both Facebook and Instagram date/time inputs are filled — Meta Business Suite renders two sets of scheduling fields.

Key selector details for Meta Business Suite (discovered through runtime debugging — may break if Meta changes their UI):
- File upload: `expect_file_chooser()` triggered by the "Add photo/video" button
- Caption field: `get_by_label("Text")`
- Schedule toggle: `get_by_text("Set date and time")`
- Date inputs: `input[placeholder="dd/mm/yyyy"]` — two instances (FB + IG)
- Time inputs: `aria-label="hours"` and `aria-label="minutes"` — must use `press_sequentially()`, not `fill()`

## Session refresh

If `post.py` fails to load Meta Business Suite properly, the session has likely expired. Re-run `setup.py`.
