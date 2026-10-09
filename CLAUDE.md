# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo does

CLI tools for the full Schuah Solutions blog publishing and social media workflow. The landing page repo lives at `C:\Code\WebApp-SchuahSolutions-WebDevLandingPage\`.

- **`blog_publish.py`** — Full blog publishing workflow: copies markdown, updates paths.ts, converts PNG to WEBP, commits, pushes, and creates a PR
- **`blog_convert.py`** — Converts a PNG blog cover image to WEBP and saves it to the landing page's `public/blogs/` directory
- **`meta_post.py`** — Schedules an image post to Facebook and Instagram via Meta Business Suite (Playwright browser automation).
- **`linkedin_post.py`** — Schedules an image post to the Schuah Solutions LinkedIn company page. Add `--post-now` to publish immediately.
- **`scheduling.py`** — Shared by both posting scripts. Both take the same flags:
  - `--type blog|testimonial|portfolio` (required) — default day Tuesday / Thursday / Wednesday, always 10:00 AM MYT
  - `--weekday mon..sun` — override the default day (e.g. `--weekday thu`)
  - `--week N` — 1 = the coming occurrence of that day (today counts if it's that day and before 10 AM), 2 = the week after, etc.
  - Always pass identical flags to both scripts so Meta and LinkedIn land on the same date.
- **`setup_meta_browser.py`** — Attaches to a Chrome running with `--remote-debugging-port=9222` (which you log into manually) and saves the session to `sessions/session_meta.json`. Uses CDP attach because Google OAuth blocks Playwright's own launched Chromium.
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

Before deleting, copy to Downloads as a named archive:
```bash
cp "C:\Code\Python-MetaPostingTools\social-post.png" "C:\Users\schuah\Downloads\testimonial-YYYY-MM-DD.png"
```
Use today's date for the filename (e.g. `testimonial-2026-05-02.png`). Then delete the original.

### Step 2 — Run meta_post.py (Facebook + Instagram)

Write the caption to `caption.txt`, then:

```bash
cd "C:\Code\Python-MetaPostingTools"
venv\Scripts\activate
python meta_post.py "C:\Code\Python-MetaPostingTools\social-post.png" --caption-file caption.txt --type testimonial
```

### Step 3 — Run linkedin_post.py

```bash
python -u linkedin_post.py "C:\Code\Python-MetaPostingTools\social-post.png" --caption-file caption.txt --type testimonial
```

That's it — no publish, no PR, no GBP reminder, no worktree sync.

---

## Portfolio Posting Workflow

The user sends a batch of finished client websites (usually 4), each with the business name, domain, some info about the business, and an image. Each one is scheduled a week apart: the first on the coming Wednesday, the next on the Wednesday after, and so on. If the user asks for Thursdays (or any other day), add `--weekday thu` to every command.

No Canva export — use the images the user provides. No blog, no PR, no GBP reminder.

### Caption template

```
🎉 [Business] has now officially launched its website with us!

[Short description about the business, 1-2 lines]

Visit at [website domain]

🔍 Looking to get a website for your own business?

🔥 We’re running a promotion of only RM375 (instead of RM2840) for a professional website to celebrate the new year!

⭐ No down payments and hidden costs. Guaranteed.
```

Use the user's description if they give one; otherwise write 1-2 plain lines from the facts they gave (what the business does, where). No marketing buzzwords.

### For each portfolio (N = 1, 2, 3, 4 in the order given)

Write its caption to `caption.txt`, then:

```bash
cd "C:\Code\Python-MetaPostingTools"
venv\Scripts\activate
python meta_post.py "<image path>" --caption-file caption.txt --type portfolio --week N
python -u linkedin_post.py "<image path>" --caption-file caption.txt --type portfolio --week N
```

Finish one portfolio on both platforms before starting the next. At the end, list each business with its scheduled date.

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

Before deleting, copy `social-post.png` to Downloads as a named archive:
```bash
cp "C:\Code\Python-MetaPostingTools\social-post.png" "C:\Users\schuah\Downloads\<slug>.png"
```
Then delete both files.

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
python -u linkedin_post.py "C:\Code\Python-MetaPostingTools\social-post.png" <slug> --caption-file caption.txt --type blog
```

Both schedule for the coming Tuesday at 10:00 AM MYT.

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

**`meta_post.py`** — Uses `sessions/session_meta.json` (saved by `setup_meta_browser.py`) to restore the Meta Business Suite browser session without re-authenticating. Schedule date comes from `scheduling.py` (see above). Blog posts auto-append the blog link (`https://schuahsolutions.com/blogs/<slug>`); testimonial and portfolio posts use the caption as-is. Both Facebook and Instagram date/time inputs are filled — Meta Business Suite renders two sets of scheduling fields.

Key selector details for Meta Business Suite (discovered through runtime debugging — may break if Meta changes their UI):

- File upload: `expect_file_chooser()` triggered by the upload button. Meta keeps renaming it ("Add photo/video", "Add Photo", ...), so the script tries every label in `PHOTO_BUTTON_NAMES` and prints the page's buttons if none match — add the new label there.
- Caption field: `get_by_label("Text")`
- Schedule toggle: `get_by_text("Set date and time")`
- Date inputs: `input[placeholder="dd/mm/yyyy"]` — two instances (FB + IG)
- Time inputs: `aria-label="hours"` and `aria-label="minutes"` — must use `press_sequentially()`, not `fill()`

**`linkedin_post.py`** — Opens the Schuah Solutions company admin composer directly (`/company/99303319/admin/page-posts/published/?share=true`) so no identity switching is needed. Uses Playwright + CDP `Input.dispatchMouseEvent` to bypass LinkedIn's `interop-outlet` shadow DOM, which blocks normal Playwright clicks. Scheduling works by clicking the calendar day cell (paging forward with the calendar's "next month" button when the date is in a later month) and using `scrollIntoView()` on the time dropdown option. If the day can't be found it exits with an error instead of scheduling on the wrong date. Requires `sessions/session_linkedin.json` — if missing or expired, run `setup_linkedin_browser.py` from a real terminal.

## Session refresh

If `meta_post.py` fails to load Meta Business Suite properly, the session has likely expired. To refresh:

1. Close all Chrome windows.
2. In PowerShell: `& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\Code\Python-MetaPostingTools\sessions\chrome_profile_meta"`
3. In that Chrome, log into https://business.facebook.com (Google OAuth works here).
4. Run `python setup_meta_browser.py` from the venv — it attaches to that Chrome via CDP and saves the session.

If `linkedin_post.py` fails with an auth error or redirects to the login page, the LinkedIn session has expired. Re-run `setup_linkedin_browser.py` from a terminal.
