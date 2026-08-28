#!/usr/bin/env python3
"""Create a simple category-count bar chart from a two-column TSV."""

import argparse
import csv
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("tsv", type=Path); ap.add_argument("output", type=Path); args = ap.parse_args()
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    with args.tsv.open() as h:
        rows = list(csv.DictReader(h, delimiter="\t"))
    names = [r["category"] for r in rows if r["category"] != "total"]
    values = [int(r["count"]) for r in rows if r["category"] != "total"]
    fig, ax = plt.subplots(figsize=(6, 4)); bars = ax.bar(names, values, color="#4C78A8")
    ax.bar_label(bars, padding=2); ax.set_ylabel("Sites"); ax.tick_params(axis="x", rotation=25)
    fig.tight_layout(); fig.savefig(args.output, dpi=200); plt.close(fig)


if __name__ == "__main__":
    main()

