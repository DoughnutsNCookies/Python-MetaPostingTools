# Python-MetaPostingTools

A collection of Python tools for managing Schuah Solutions content.

## Tools

- **`publish.py`** — Full blog publishing workflow: copies markdown, updates paths.ts, converts PNG to WEBP, commits, pushes, and creates a PR
- **`convert.py`** — Converts PNG blog cover images to WEBP and saves them to the landing page's `public/blogs/` directory
- **`meta_post.py`** — Schedules image posts to Facebook and Instagram for the coming Tuesday at 10am MYT via Meta Business Suite
- **`setup.py`** — One-time login setup for Meta Business Suite (saves browser session)

## One-Time Setup

**1. Create a `.env` file** (copy from `.env.example`):
```
META_PAGE_ID=202884486244813
```

**2. Set up the venv:**
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

**3. Save your Meta Business Suite session (run once):**
```
python setup.py
```
Log in manually including 2FA, then press Enter. Session is saved and reused automatically.

---

## publish.py — Full Blog Publishing Workflow

```
python publish.py "C:\path\to\blog.md" "C:\path\to\image.png" --worktree "C:\path\to\worktree"
```

Copies the markdown, updates `paths.ts`, converts the PNG to WEBP, commits everything, and opens a PR.

**Options:**
| Argument | Required | Description |
|----------|----------|-------------|
| `blog` | Yes | Path to the `.md` file |
| `image` | Yes | Path to the cover image PNG |
| `--worktree` | No | Path to the git worktree. Defaults to the main project directory |
| `--quality` | No | WEBP quality 1–100. Default: 82 |

**Example:**
```
python publish.py "C:\Users\schuah\Downloads\my-post.md" "C:\Users\schuah\Downloads\cover.png" --worktree "C:\Code\WebApp-SchuahSolutions-WebDevLandingPage\.claude\worktrees\<worktree-name>"
```

---

## convert.py — PNG to WEBP

```
python convert.py "C:\path\to\image.png" <slug>
```

**Options:**
| Argument | Required | Description |
|----------|----------|-------------|
| `input` | Yes | Path to source PNG |
| `slug` | Yes | Output slug (lowercase, hyphens only) |
| `--quality` | No | WEBP quality 1–100. Default: 82 |
| `--force` | No | Overwrite if slug already exists |
| `--target` | No | Override output directory (for worktree branches) |

**Example:**
```
python convert.py "C:\Users\schuah\Downloads\Blog Cover Image.png" my-new-blog-post
```

---

## meta_post.py — Schedule Social Media Post

```
python meta_post.py "C:\path\to\image.png" <slug> --caption-file caption.txt
```

Schedules the post for the coming Tuesday at 10:00 AM MYT on both Facebook and Instagram. Facebook post includes the blog link automatically.

**Example:**
```
python meta_post.py "C:\Users\schuah\Downloads\Social Media Post.png" my-new-blog-post --caption-file caption.txt
```

---

## Session Refresh

If the Meta Business Suite session expires, re-run:
```
python setup.py
```

## Deactivate venv when done

```
deactivate
```
