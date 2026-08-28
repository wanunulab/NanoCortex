#!/usr/bin/env python3
"""Match FASTA records to RNA-structure output files and write a compact TSV."""

import argparse
import csv
from pathlib import Path


def fasta_lengths(path):
    out, name, seq = {}, None, []
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if line.startswith(">"):
            if name is not None: out[name] = len("".join(seq))
            name, seq = line[1:].split()[0], []
        elif line: seq.append(line)
    if name is not None: out[name] = len("".join(seq))
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("fasta", type=Path); ap.add_argument("output_dir", type=Path); ap.add_argument("--tsv", type=Path, required=True); args = ap.parse_args()
    rows = []
    for ident, length in fasta_lengths(args.fasta).items():
        files = sorted(str(p) for p in args.output_dir.glob(f"{ident}.*"))
        rows.append({"sequence_id": ident, "length": length, "ct_present": any(x.endswith(".ct") for x in files),
                     "plot_present": any(x.endswith((".png", ".svg", ".pdf")) for x in files), "files": ";".join(files)})
    args.tsv.parent.mkdir(parents=True, exist_ok=True)
    with args.tsv.open("w", newline="") as h:
        w = csv.DictWriter(h, fieldnames=rows[0].keys() if rows else ["sequence_id", "length", "ct_present", "plot_present", "files"], delimiter="\t"); w.writeheader(); w.writerows(rows)
    return 0 if rows and all(r["ct_present"] for r in rows) else 2


if __name__ == "__main__":
    raise SystemExit(main())

