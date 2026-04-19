# Python-MetaPostingTools

A collection of Python tools for managing Schuah Solutions content.

## Tools

- **`convert.py`** — Converts PNG blog cover images to WEBP and saves them to the landing page's `public/blogs/` directory
- **`post.py`** — Schedules image posts to Facebook and Instagram for the coming Tuesday at 10am MYT via Meta Business Suite
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

## post.py — Schedule Social Media Post

```
python post.py "C:\path\to\image.png" <slug> --caption-file caption.txt
```

Schedules the post for the coming Tuesday at 10:00 AM MYT on both Facebook and Instagram. Facebook post includes the blog link automatically.

**Example:**
```
python post.py "C:\Users\schuah\Downloads\Social Media Post.png" my-new-blog-post --caption-file caption.txt
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
