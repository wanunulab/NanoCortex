#!/usr/bin/env python3
"""Validate one or more six-column connectivity-table (CT) files."""

import argparse
from pathlib import Path


def validate(path):
    lines = [x.split() for x in path.read_text().splitlines() if x.strip()]
    try:
        expected = int(lines[0][0]); body = lines[1:]
    except (IndexError, ValueError):
        return False, 0, "invalid header"
    if len(body) != expected:
        return False, 0, f"expected {expected} rows; found {len(body)}"
    pairs = {}
    for row in body:
        if len(row) < 6:
            return False, 0, "row has fewer than six columns"
        i, partner = int(row[0]), int(row[4])
        if i < 1 or i > expected or partner < 0 or partner > expected or partner == i:
            return False, 0, "pair index out of range"
        pairs[i] = partner
    if any(p and pairs.get(p) != i for i, p in pairs.items()):
        return False, 0, "pairing is not reciprocal"
    return True, sum(p > i for i, p in pairs.items()), "ok"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("ct", nargs="+", type=Path); args = ap.parse_args()
    failed = False
    print("file\tvalid\tbase_pairs\tnote")
    for path in args.ct:
        ok, n, note = validate(path); failed |= not ok
        print(f"{path}\t{str(ok).lower()}\t{n}\t{note}")
    return 2 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

