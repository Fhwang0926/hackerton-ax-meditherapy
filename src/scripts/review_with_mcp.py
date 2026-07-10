#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mediinsight.law_client import review_with_bundled_mcp


def review(pending_path: Path, output_path: Path) -> None:
    review_with_bundled_mcp(ROOT / "mcp" / "mediinsight_law_server.py", pending_path, output_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Review pending MediInsight claims through the bundled MCP server.")
    parser.add_argument("--pending", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    review(args.pending, args.out)


if __name__ == "__main__":
    main()
