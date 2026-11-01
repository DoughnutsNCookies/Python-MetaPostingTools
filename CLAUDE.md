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
- **`render_blog_graphics.py`** — Renders a blog's square social post and landscape website cover from an SVG drawing and a three-part title (uses `assets/Anton-Regular.ttf` and `assets/logo.webp`).
- **`plan_blog_batch.py`** — Prints (JSON) the Tuesdays the monthly blog run must fill and every existing post's title/slug/date. See Monthly Blog Batch below.
- **`setup_meta_browser.py`** — Opens real Chrome on the Meta profile (`sessions/chrome_profile_meta`) so the user can log in. `meta_post.py` drives that same profile.
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

No Canva export — use the images the user provides. No blog, no PR, no GBP reminder. `meta_post.py` goes through Meta Business Suite, so each post lands on both Facebook and Instagram — that's intended.

### Caption template

```
🎉 [Business] has now officially launched its website with us!

[Short description about the business, 1-2 lines]

Visit at [website domain]

🔍 Looking to get a website for your own business?

🔥 We’re running a promotion of only RM375 (instead of RM2840) for a professional website to celebrate our anniversary!

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

## Monthly Blog Batch (automated — 1st of each month, 7:00 AM)

A scheduled task runs this in `C:\Code\Python-MetaPostingTools`. Claude writes the blogs itself, publishes them, and schedules one per Tuesday 10:00 AM MYT on Facebook/Instagram, LinkedIn and Google Business Profile.

**Standing approval (Sean, 2026-11-01):** the whole run is hands-off. Write and publish the blogs, draw the graphics, and schedule every post without asking. Sean reviews after they're posted. Don't touch the Canva designs (testimonials still live there).

### Step 0 — Plan

```bash
venv\Scripts\python plan_blog_batch.py
```

`tuesdays_to_fill` lists the dates (every Tuesday after the last blog's date, up to Meta's 30-day limit, so usually 4 or 5). If it's empty, report "nothing to schedule" and stop. Work through the dates **oldest first and finish each blog on every platform before starting the next** — on a 1st that's a Tuesday, the first post is only three hours away. Put all working files in `batch\` (git-ignored).

### Step 1 — Write the blog

- **Topic:** something a Malaysian small-business owner actually types into Google: "how much does…", "why isn't my…", "do I need…", "X vs Y", "how to…", with a location (Shah Alam, Klang Valley, KL, Selangor) or industry where natural. The goal is SEO. Don't repeat or near-repeat anything in `existing_posts`, and vary the batch (websites, SEO, Google Business Profile, Google/Meta ads, specific industries).
- **Voice:** read the 3 newest posts in `C:\Code\WebApp-SchuahSolutions-WebDevLandingPage\landing-page\src\blogs\` first and match them: short punchy lines, "you", RM prices, honest and slightly blunt, `##` sections, about 900–1,300 words. End with `## What Now?`, a pitch for the relevant Schuah Solutions service (website posts: `**RM375/month. No downpayment. No hidden fees. No BS.**`), then `Contact us below. **NOW.**`. No made-up client names, quotes or statistics.
- **Frontmatter:** `title` (the search query, sentence case), `description` (under 160 characters), `slug` (kebab-case of the title), `date` = the Tuesday as `"D MONTH YYYY"` with the month in capitals, e.g. `"3 NOVEMBER 2026"`. The date must be exact: it's how the next run knows this Tuesday is taken.
- Save as `batch\<slug>.md`.

### Step 2 — Captions

- **Facebook/LinkedIn caption** (`batch\<slug>.caption.txt`): same shape as past blog captions — a short hook, the pain point, an emoji list (✅ / ❌ / 🔍 / 📊), a closing "I broke down…" line, then `👉 https://schuahsolutions.com/blogs/<slug>`.
- **Google Business Profile text:** the same caption with the "I broke down…" line and the 👉 link line replaced by `Read it now by clicking on the "Learn more" button`. Max 1,500 characters.

### Step 3 — Illustration (SVG, drawn by Claude)

No Canva and no AI image credits. Write the illustration yourself as an SVG file, `batch\<slug>.svg`:

- `viewBox="0 0 800 600"` (4:3), transparent background, the subject centred and filling most of the frame.
- House style: flat cartoon, bold dark outlines (`stroke="#2b2b2b"`, `stroke-width` 8–10, round joins and caps), soft friendly fills, one clear subject for the topic (e.g. a phone with stars for reviews, a map pin over a shopfront for Google Maps). Simple objects, not people's faces in detail.
- No text, letters, numbers or brand logos inside the drawing.

### Step 4 — Graphics

Split the title into prefix / highlighted keyword (2–5 words) / suffix, all non-empty, and pick an accent colour that suits the drawing (default `#e29d5f`; vary it across the batch). Then:

```bash
venv\Scripts\python render_blog_graphics.py batch\<slug>.svg --prefix "How to get more " --highlight "Google reviews" --suffix " for your business" --accent "#e8a417" --social batch\<slug>-social.png --cover batch\<slug>-cover.png
```

It renders the 1080×1080 social post and the 1920×1080 website cover with the logo, the drawing and the title in Anton. If it says the title doesn't fit, shorten the graphic's wording (the blog title can stay longer). Look at both PNGs before moving on; redraw the SVG if anything looks off.

### Step 5 — Publish to the website

```bash
venv\Scripts\python blog_publish.py batch\<slug>.md batch\<slug>-cover.png --worktree C:\Code\WebApp-SchuahSolutions-WebDevLandingPage
```

Pushes straight to the landing page's `main`, which is live.

### Step 6 — Schedule

```bash
venv\Scripts\python meta_post.py batch\<slug>-social.png <slug> --caption-file batch\<slug>.caption.txt --type blog --date <YYYY-MM-DD>
venv\Scripts\python -u linkedin_post.py batch\<slug>-social.png <slug> --caption-file batch\<slug>.caption.txt --type blog --date <YYYY-MM-DD>
```

- `meta_post.py` exit 3 = Meta login expired: skip Meta for the rest of the batch, carry on with the other platforms, and tell Sean to run `setup_meta_browser.py`.
- `meta_post.py` exit 4 = Meta didn't confirm: look at Meta Business Suite's Planner before retrying. Never re-run blindly — that risks a duplicate post.

**Google Business Profile** — via Claude in Chrome (Sean's own Chrome, already signed in):
1. `tabs_context_mcp`, new tab, open `https://www.google.com/search?q=schuah+solutions`.
2. In the "Your business on Google" panel click **Posts**, then **Add post**. Keep **Update** selected.
3. **Description**: the GBP text from Step 2.
4. **Select images and videos**: upload `batch\<slug>-social.png`.
5. Switch on **Schedule this post**. **Date**: calendar (weeks start Monday, month/year arrows). **Time**: 10:00 AM.
6. **+ Button** → "Add a button" dropdown → **Learn more** → link `https://schuahsolutions.com/blogs/<slug>`.
7. **Post**, then check it shows in the posts list as scheduled. Close the tab.

If the Chrome extension isn't connected, start Chrome (`start chrome`), wait, and retry once. If it still fails, skip GBP and put the copy-paste text and link in the report.

### Step 7 — Archive and clean up

Copy each `batch\<slug>-social.png` to `C:\Users\schuah\Downloads\<slug>.png`, then empty `batch\`.

### Step 8 — Report

One table: Tuesday, title, blog URL, and done/failed for website, Facebook+Instagram, LinkedIn, GBP. Then anything Sean has to do (expired login, a post to check). No other summary.

---

## Blog Publishing Workflow (manual — when the user sends a blog)

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

**`meta_post.py`** — Launches real Chrome on `sessions/chrome_profile_meta` (debug port 9223), drives it over CDP, and closes it through CDP so refreshed cookies are saved back to the profile (the old `storage_state` snapshot went stale within a week). Exits 3 if the login has expired, 4 if Meta didn't confirm the schedule. Schedule date comes from `scheduling.py` (see above). Blog posts auto-append the blog link (`https://schuahsolutions.com/blogs/<slug>`); testimonial and portfolio posts use the caption as-is. Both Facebook and Instagram date/time inputs are filled — Meta Business Suite renders two sets of scheduling fields.

Key selector details for Meta Business Suite (discovered through runtime debugging — may break if Meta changes their UI):

- File upload: `expect_file_chooser()` triggered by the upload button. Meta keeps renaming it ("Add photo/video", "Add Photo", ...), so the script tries every label in `PHOTO_BUTTON_NAMES` and prints the page's buttons if none match — add the new label there.
- Caption field: `get_by_label("Text")`
- Schedule toggle: `get_by_text("Set date and time")`
- Date inputs: `input[placeholder="dd/mm/yyyy"]` — two instances (FB + IG)
- Time inputs: `aria-label="hours"` and `aria-label="minutes"` — must use `press_sequentially()`, not `fill()`

**`linkedin_post.py`** — Opens the Schuah Solutions company admin composer directly (`/company/99303319/admin/page-posts/published/?share=true`) so no identity switching is needed. Uses Playwright + CDP `Input.dispatchMouseEvent` to bypass LinkedIn's `interop-outlet` shadow DOM, which blocks normal Playwright clicks. Scheduling works by clicking the calendar day cell (paging forward with the calendar's "next month" button when the date is in a later month) and using `scrollIntoView()` on the time dropdown option. If the day can't be found it exits with an error instead of scheduling on the wrong date. Requires `sessions/session_linkedin.json` — if missing or expired, run `setup_linkedin_browser.py` from a real terminal.

## Session refresh

If `meta_post.py` exits 3 (Meta login expired): run `python setup_meta_browser.py` from the venv, log in in the Chrome window it opens (Google sign-in works there), then close that window. Claude can run the script itself; only the login needs the user.

If `linkedin_post.py` fails with an auth error or redirects to the login page, the LinkedIn session has expired. Re-run `setup_linkedin_browser.py` from a terminal.
