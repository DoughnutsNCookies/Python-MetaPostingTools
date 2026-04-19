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

When the user sends a new blog post (markdown file + cover image PNG), run `publish.py`:

```bash
venv\Scripts\activate
python publish.py "C:\path\to\blog.md" "C:\path\to\image.png" --worktree "C:\Code\WebApp-SchuahSolutions-WebDevLandingPage\.claude\worktrees\<worktree-name>"
```

This handles everything in one command:
1. Copies the `.md` file to `landing-page/src/blogs/<slug>.md`
2. Adds `/blogs/<slug>` to `landing-page/src/app/paths.ts`
3. Converts the PNG to WEBP → `landing-page/public/blogs/<slug>.webp`
4. Commits, pushes, and opens a PR against `main`

Omit `--worktree` to target the main project directory (not a worktree branch).

After the user merges the PR, sync the worktree branch:

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

### Schedule social media post (optional, same session)

```bash
python post.py "C:\path\to\social-image.png" <slug> --caption-file caption.txt
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
