#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "submission.zip"


def should_skip(path: Path) -> bool:
    parts = set(path.parts)
    return (
        "__pycache__" in parts
        or path.suffix == ".pyc"
        or path.name == ".DS_Store"
        or path.name == "submission.zip"
        or ".git" in parts
        or "output" in parts
    )


def add_tree(zip_file: zipfile.ZipFile, base: Path, arc_base: str) -> None:
    for path in sorted(base.rglob("*")):
        if path.is_dir() or should_skip(path.relative_to(ROOT)):
            continue
        zip_file.write(path, Path(arc_base) / path.relative_to(base))


def build(output: Path) -> None:
    required = [ROOT / "src", ROOT / "README.md", ROOT / "logs"]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    if missing:
        raise SystemExit(f"Missing required submission paths: {', '.join(missing)}")
    log_files = [
        path
        for path in (ROOT / "logs").rglob("*")
        if path.is_file() and path.name.lower() != "readme.md" and path.suffix.lower() in {".md", ".txt", ".json", ".jsonl"}
    ]
    if not log_files:
        raise SystemExit(
            "No original AI conversation log found in logs/. Add the unedited source log before building submission.zip."
        )

    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        add_tree(zip_file, ROOT / "src", "src")
        zip_file.write(ROOT / "README.md", "README.md")
        add_tree(zip_file, ROOT / "logs", "logs")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build hackathon submission.zip.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    build(args.out)
    print(args.out)


if __name__ == "__main__":
    main()
