# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo does

CLI tools for the full Schuah Solutions blog publishing and social media workflow. The landing page repo lives at `C:\Code\WebApp-SchuahSolutions-WebDevLandingPage\`.

- **`blog_publish.py`** — Full blog publishing workflow: copies markdown, updates paths.ts, converts PNG to WEBP, commits, pushes, and creates a PR
- **`blog_convert.py`** — Converts a PNG blog cover image to WEBP and saves it to the landing page's `public/blogs/` directory
- **`meta_post.py`** — Schedules an image post to Facebook and Instagram via Meta Business Suite (Playwright browser automation). Blogs target Tuesday 10:00 AM MYT, testimonials target Thursday 10:00 AM MYT. Use `--type blog` or `--type testimonial` (required, no default).
- **`linkedin_post.py`** — Schedules an image post to the Schuah Solutions LinkedIn company page, targeting the coming Tuesday at 10:00 AM MYT. Add `--post-now` to publish immediately.
- **`setup_meta_browser.py`** — One-time login helper: opens a browser for manual Meta login + 2FA, then saves the session to `sessions/session_meta.json` for reuse
- **`setup_linkedin_browser.py`** — One-time login helper for LinkedIn: opens a browser for manual login, saves session to `sessions/session_linkedin.json`. Must be run directly from a terminal (uses `input()`).
- **`gbp_post.py`** — ⚠️ NOT YET ACTIVE. Google Business Profile post automation. Pending GBP API access approval (requested, ETA 7–10 business days). Once approved, replace the Playwright approach in this file with the proper API calls using `client_secret.json` + `token_gbp.json`.
- **`setup_gbp.py`** — ⚠️ NOT YET ACTIVE. GBP auth setup, to be wired up once API access is granted.

## Setup

```bash
py -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

Create `.env` from `.env.example`. Run `setup_meta_browser.py` once to authenticate with Meta. Run `setup_linkedin_browser.py` once to authenticate with LinkedIn. Sessions are saved to `C:\Code\Python-MetaPostingTools\sessions\` and shared across all worktrees — you only need to log in once per platform.

## Landing page

The landing page is a Next.js 15 App Router site. All npm commands run from `C:\Code\WebApp-SchuahSolutions-WebDevLandingPage\landing-page\`:

```bash
npm run dev     # Start dev server at localhost:3000
npm run build   # Production build
npm run lint    # ESLint with Next.js rules
```

**Key directories** (all under `landing-page/src/`):

- `app/(pages)/` — All routes, grouped by section (about, services, locations, legal, etc.)
- `app/sections/` — Full-width page sections (Hero, Pricing, FAQs, Testimonials, etc.)
- `app/components/` — Smaller reusable UI components
- `app/lib/blogs.ts` — Auto-discovers all `.md` files; infers `coverImagePath` as `/blogs/{slug}.webp`
- `app/api/` — Email submission via Nodemailer + Zapier webhook
- `blogs/` — Markdown files, one per blog post
- `../public/blogs/` — WebP cover images, one per blog post

**Central config:** `landing-page/template.config.ts` — defines the entire color palette, fonts, metadata, and analytics IDs (GA + Facebook Pixel). Change colors/branding here first.

A blog post requires three things in the landing page repo: a markdown file at `src/blogs/<slug>.md`, an entry in `src/app/paths.ts`, and a cover image at `public/blogs/<slug>.webp`. `blog_publish.py` handles all three automatically.

## Testimonial Posting Workflow

The user sends the social media caption. Claude handles everything else automatically.

### Step 1 — Export image from Canva (Claude does this via MCP)

| Design | Canva ID | Purpose |
|--------|----------|---------|
| Social Media Post | `DAGal3LsJUo` | Posted to Facebook + Instagram |

Export page 1 as PNG and download to:
- `C:\Code\Python-MetaPostingTools\social-post.png`

Delete after done.

### Step 2 — Run meta_post.py

Write the caption to `caption.txt`, then:

```bash
cd "C:\Code\Python-MetaPostingTools"
venv\Scripts\activate
python meta_post.py "C:\Code\Python-MetaPostingTools\social-post.png" --caption-file caption.txt --type testimonial
```

That's it — no publish, no PR, no GBP reminder, no worktree sync.

---

## Blog Publishing Workflow

The user sends only the blog markdown content. Claude handles everything else automatically.

### Step 1 — Export images from Canva (Claude does this via MCP)

Two Canva designs are always kept up to date — page 1 of each is always the latest blog:

| Design            | Canva ID      | Purpose                                     |
| ----------------- | ------------- | ------------------------------------------- |
| Blog Cover Image  | `DAGeyipWBWU` | Converted to WEBP for the website           |
| Social Media Post | `DAGal3LsJUo` | Posted to Facebook, Instagram, and LinkedIn |

Export page 1 of both as PNG using the Canva MCP `export-design` tool, then download each to the tools folder:

- `C:\Code\Python-MetaPostingTools\blog-cover.png`
- `C:\Code\Python-MetaPostingTools\social-post.png`

Delete both files after all scripts have finished.

### Step 2 — Save the blog markdown to a temp file

Write the markdown content the user provided to `C:\Code\Python-MetaPostingTools\blog.md`. Delete after done.

### Step 3 — Run blog_publish.py

```bash
cd "C:\Code\Python-MetaPostingTools"
venv\Scripts\activate
python blog_publish.py "C:\Code\Python-MetaPostingTools\blog.md" "C:\Code\Python-MetaPostingTools\blog-cover.png" --worktree "C:\Code\WebApp-SchuahSolutions-WebDevLandingPage\.claude\worktrees\<worktree-name>"
```

### Step 4 — Run meta_post.py (Meta: Facebook + Instagram)

Write the social media caption to `caption.txt`, then:

```bash
# Blog post (schedules Tuesday, appends blog link automatically)
python meta_post.py "C:\Code\Python-MetaPostingTools\social-post.png" <slug> --caption-file caption.txt --type blog
```

**Important:** `--type` is required — there is no default. Omitting it will error. Always pass it explicitly.

### Step 4b — Run linkedin_post.py

```bash
python -u linkedin_post.py "C:\Code\Python-MetaPostingTools\social-post.png" <slug> --caption-file caption.txt
```

Both meta_post.py and linkedin_post.py schedule for the coming Tuesday at 10:00 AM MYT by default.

### Step 5 — Output GBP reminder

Immediately after all scripts finish, output this reminder with ready-to-copy content (do not wait for the PR to be merged):

---

**Google Business Profile — Post manually**

**Image:** `C:\Code\Python-MetaPostingTools\social-post.png`

**Description:**

```
<full caption text with last CTA line replaced: "Read it now by clicking on the "Learn more" button">
```

**Button:** Learn more →

```
https://schuahsolutions.com/blogs/<slug>
```

---

Once GBP API access is approved, this step will be automated via `gbp_post.py`.

### Step 6 — After user merges the PR, sync the worktree branch

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

## PR Workflow

Claude Code works on a worktree branch (`claude/<session-id>`). The standard flow:

1. Make changes on the worktree branch
2. Commit and push: `git push origin HEAD:<branch-name>`
3. Create PR with `gh pr create --base main`
4. User merges on GitHub
5. After merge, sync the worktree branch (Step 6 above)

`gh` CLI is installed at `C:\Program Files\GitHub CLI\gh.exe` (not in PATH — use full path or fix PATH).

Branch protection on `main` requires all changes go through PRs — do not push directly to `main`.

---

## Key implementation details

**`blog_convert.py`** — TARGET_DIR is hardcoded to the main landing page path. Use `--target` to override for worktree branches. Default quality is 82; use `--force` to overwrite an existing slug.

**`meta_post.py`** — Uses `sessions/session_meta.json` (saved by `setup_meta_browser.py`) to restore the Meta Business Suite browser session without re-authenticating. `--type blog` schedules for next Tuesday, `--type testimonial` for next Thursday — both at 10:00 AM MYT (`Asia/Kuala_Lumpur`). Blog posts auto-append the blog link (`https://schuahsolutions.com/blogs/<slug>`); testimonial posts use the caption as-is. Both Facebook and Instagram date/time inputs are filled — Meta Business Suite renders two sets of scheduling fields.

Key selector details for Meta Business Suite (discovered through runtime debugging — may break if Meta changes their UI):

- File upload: `expect_file_chooser()` triggered by the "Add photo/video" button
- Caption field: `get_by_label("Text")`
- Schedule toggle: `get_by_text("Set date and time")`
- Date inputs: `input[placeholder="dd/mm/yyyy"]` — two instances (FB + IG)
- Time inputs: `aria-label="hours"` and `aria-label="minutes"` — must use `press_sequentially()`, not `fill()`

**`linkedin_post.py`** — Opens the Schuah Solutions company admin composer directly (`/company/99303319/admin/page-posts/published/?share=true`) so no identity switching is needed. Uses Playwright + CDP `Input.dispatchMouseEvent` to bypass LinkedIn's `interop-outlet` shadow DOM, which blocks normal Playwright clicks. Scheduling works by clicking the calendar day cell and using `scrollIntoView()` on the time dropdown option. `--type blog` schedules for next Tuesday, `--type testimonial` for next Thursday — both at 10:00 AM MYT. Requires `sessions/session_linkedin.json` — if missing or expired, run `setup_linkedin_browser.py` from a real terminal.

## Session refresh

If `meta_post.py` fails to load Meta Business Suite properly, the session has likely expired. Re-run `setup_meta_browser.py`.

If `linkedin_post.py` fails with an auth error or redirects to the login page, the LinkedIn session has expired. Re-run `setup_linkedin_browser.py` from a terminal.
