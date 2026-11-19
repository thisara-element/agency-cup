"""Shared code for the Agency Cup kit: the game clients, the NVIDIA model client and the notebook helpers.

`uv sync` installs this folder, so `from agency_kit import kit` works from the notebooks, the starters and anywhere else.
"""

import sys


def utf8_output() -> None:
    """Print emoji safely everywhere. On Windows, output sent to a file or pipe uses an old code page that has no
    ✅ or 🔧, and print() would crash with UnicodeEncodeError. Switch stdout and stderr to UTF-8 instead."""
    for stream in (sys.stdout, sys.stderr):
        if (getattr(stream, "encoding", "") or "").lower().replace("-", "") != "utf8" and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass


utf8_output()  # runs once, whenever anything imports agency_kit
