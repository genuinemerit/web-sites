"""Command line for the music catalog check (websites.music.catalog).

    python -m websites.music.check            # catalog + translations
    python -m websites.music.check --status   # translation status and the
                                              # fingerprints to record

Separate from catalog.py so `python -m` doesn't import that module
twice (the websites.music package imports it too).
"""

from __future__ import annotations

import sys

from websites.music.catalog import main

if __name__ == "__main__":
    sys.exit(main())
