#!/usr/bin/env python3
"""Validate regional nanopore signal plot outputs."""

import argparse
import os
import sys


def validate_plot(path: str) -> list[str]:
    errors: list[str] = []
    if not os.path.isfile(path):
        return [f"plot file not found: {path}"]

    if os.path.getsize(path) == 0:
        errors.append(f"plot file is empty: {path}")

    lower = path.lower()
    with open(path, "rb") as handle:
        header = handle.read(8)

    if lower.endswith(".png"):
        if not header.startswith(b"\x89PNG\r\n\x1a\n"):
            errors.append(f"invalid PNG header: {path}")
    elif lower.endswith(".pdf"):
        if not header.startswith(b"%PDF"):
            errors.append(f"invalid PDF header: {path}")
    else:
        errors.append(f"unsupported plot extension (use .png or .pdf): {path}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a signal plot output file.")
    parser.add_argument("plot_path", help="Path to the generated .png or .pdf plot")
    args = parser.parse_args()

    errors = validate_plot(args.plot_path)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"OK: {args.plot_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
