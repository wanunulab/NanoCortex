#!/usr/bin/env python3
"""Filter and classify a headered or headerless modification table by selected columns."""

import argparse
import csv
from collections import Counter
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("--effect-col", type=int, required=True, help="1-based effect-size column")
    ap.add_argument("--coverage-cols", type=int, nargs="*", default=[], help="1-based coverage columns")
    ap.add_argument("--min-coverage", type=float, default=0)
    ap.add_argument("--effect-threshold", type=float, required=True)
    ap.add_argument("--delimiter", default="\t")
    ap.add_argument("--header", action="store_true")
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--summary", type=Path, required=True)
    args = ap.parse_args()
    counts, output = Counter(), []
    with args.input.open() as h:
        rows = csv.reader(h, delimiter=args.delimiter)
        header = next(rows, None) if args.header else None
        for line_no, row in enumerate(rows, 2 if args.header else 1):
            counts["total"] += 1
            try:
                effect = float(row[args.effect_col - 1])
                cov = [float(row[i - 1]) for i in args.coverage_cols]
            except (ValueError, IndexError):
                counts["unclassified"] += 1
                continue
            if cov and min(cov) < args.min_coverage:
                counts["filtered_coverage"] += 1
                continue
            label = "increased" if effect >= args.effect_threshold else (
                "decreased" if effect <= -args.effect_threshold else "unchanged")
            counts[label] += 1
            output.append(row + [label])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as h:
        w = csv.writer(h, delimiter="\t")
        if header: w.writerow(header + ["classification"])
        w.writerows(output)
    with args.summary.open("w", newline="") as h:
        w = csv.writer(h, delimiter="\t"); w.writerow(["category", "count"])
        for key in ("total", "increased", "decreased", "unchanged", "filtered_coverage", "unclassified"):
            w.writerow([key, counts[key]])
    print("\t".join(f"{k}={counts[k]}" for k in ("total", "increased", "decreased", "unchanged", "filtered_coverage", "unclassified")))


if __name__ == "__main__":
    main()

