"""axross-headless-mcp: ``python -m axross_headless_mcp`` / ``axross-headless-mcp``.

The axross modules keep their names (core, models, security, axross) under
_ax/, which goes first on sys.path - only in this process, only when the
command starts (importing the package changes nothing)."""

import sys
from pathlib import Path

AX = str(Path(__file__).resolve().parent / "_ax")


def main() -> int:
    if AX not in sys.path:
        sys.path.insert(0, AX)
    from core.mcp_cli import main as run

    return run()


if __name__ == "__main__":
    sys.exit(main())
