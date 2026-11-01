"""
Opens Chrome on the Meta profile so you can log in. meta_post.py reuses this profile.

Run it, log in to Meta Business Suite in the window that opens (Google sign-in works,
because this is ordinary Chrome, not an automated one), then close the window.
"""

import subprocess

from meta_post import CHROME_EXE, PROFILE_DIR


def main():
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    subprocess.Popen([CHROME_EXE, f"--user-data-dir={PROFILE_DIR}", "--no-first-run",
                      "https://business.facebook.com"])
    print("\n  Chrome is open on the Meta profile. Log in, check you can see the dashboard,")
    print("  then close that Chrome window. Nothing else to do.\n")


if __name__ == "__main__":
    main()
