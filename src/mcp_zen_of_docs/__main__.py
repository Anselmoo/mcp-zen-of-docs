"""Package entry point for python -m mcp_zen_of_docs."""

from __future__ import annotations

import sys

from typing import TYPE_CHECKING

from .interfaces import run_cli
from .interfaces import run_mcp_server


__all__ = ["main"]

if TYPE_CHECKING:
    from collections.abc import Sequence

cli_main = run_cli
server_main = run_mcp_server


def main(argv: Sequence[str] | None = None) -> int:
    """Run the package entry point with optional argv overrides."""
    args = list(argv) if argv is not None else sys.argv[1:]
    if args and args[0] == "mcp-serve":
        server_main()
        return 0
    return cli_main(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
