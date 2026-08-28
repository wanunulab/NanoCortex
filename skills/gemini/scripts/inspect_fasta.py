#!/usr/bin/env python3
"""Validate FASTA and write a compact per-record summary."""

import argparse
import csv
import json
from pathlib import Path


def records(path):
    name, seq = None, []
    with path.open() as handle:
        for raw in handle:
            line = raw.strip()
            if not line:
                continue
            if line.startswith(">"):
                if name is not None:
                    yield name, "".join(seq).upper()
                name, seq = line[1:].split()[0] if line[1:].strip() else "", []
            elif name is None:
                raise ValueError("sequence found before the first FASTA header")
            else:
                seq.append(line.replace(" ", ""))
    if name is not None:
        yield name, "".join(seq).upper()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("--tsv", type=Path, required=True)
    ap.add_argument("--json", type=Path, required=True)
    args = ap.parse_args()
    rows, seen = [], set()
    for ident, seq in records(args.input):
        valid = set(seq) <= set("ACGUTN")
        rows.append({"sequence_id": ident, "length": len(seq), "alphabet_valid": valid,
                     "duplicate_id": ident in seen, "empty": len(seq) == 0})
        seen.add(ident)
    args.tsv.parent.mkdir(parents=True, exist_ok=True)
    with args.tsv.open("w", newline="") as h:
        w = csv.DictWriter(h, fieldnames=rows[0].keys() if rows else
                           ["sequence_id", "length", "alphabet_valid", "duplicate_id", "empty"], delimiter="\t")
        w.writeheader(); w.writerows(rows)
    summary = {"sequence_count": len(rows), "valid": bool(rows) and all(
        r["alphabet_valid"] and not r["duplicate_id"] and not r["empty"] for r in rows), "records": rows}
    args.json.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary))
    return 0 if summary["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

