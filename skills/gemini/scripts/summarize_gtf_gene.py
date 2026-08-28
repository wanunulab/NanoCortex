#!/usr/bin/env python3
"""Extract one gene from a GTF and summarize transcript exon chains."""

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path


def attrs(text):
    return dict(re.findall(r'(\S+)\s+"([^"]*)"', text))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("gtf", type=Path)
    ap.add_argument("gene")
    ap.add_argument("--transcripts", type=Path, required=True)
    ap.add_argument("--exons", type=Path, required=True)
    args = ap.parse_args()
    tx, exons = {}, defaultdict(list)
    keys = ("gene_name", "ref_gene_name", "gene_id", "ref_gene_id")
    with args.gtf.open() as h:
        for raw in h:
            if raw.startswith("#") or not raw.strip():
                continue
            f = raw.rstrip("\n").split("\t")
            if len(f) != 9:
                continue
            a = attrs(f[8])
            if args.gene not in {a.get(k) for k in keys}:
                continue
            tid = a.get("transcript_id")
            if not tid:
                continue
            base = {"transcript_id": tid, "chrom": f[0], "strand": f[6],
                    "start": int(f[3]), "end": int(f[4]), "TPM": a.get("TPM", ""),
                    "coverage": a.get("cov", ""), "reference_id": a.get("reference_id", "")}
            if f[2] == "transcript":
                tx[tid] = base
            elif f[2] == "exon":
                exons[tid].append((int(f[3]), int(f[4]), a.get("exon_number", "")))
    for tid in set(tx) | set(exons):
        if tid not in tx and exons[tid]:
            starts, ends = zip(*[(x[0], x[1]) for x in exons[tid]])
            tx[tid] = {"transcript_id": tid, "chrom": "", "strand": "", "start": min(starts),
                       "end": max(ends), "TPM": "", "coverage": "", "reference_id": ""}
        tx[tid]["exon_count"] = len(exons[tid])
        tx[tid]["exon_chain"] = ",".join(f"{s}-{e}" for s, e, _ in sorted(exons[tid]))
    args.transcripts.parent.mkdir(parents=True, exist_ok=True)
    fields = ["transcript_id", "chrom", "strand", "start", "end", "exon_count", "TPM", "coverage", "reference_id", "exon_chain"]
    with args.transcripts.open("w", newline="") as h:
        w = csv.DictWriter(h, fieldnames=fields, delimiter="\t"); w.writeheader()
        for row in sorted(tx.values(), key=lambda x: x["transcript_id"]): w.writerow(row)
    with args.exons.open("w", newline="") as h:
        w = csv.writer(h, delimiter="\t"); w.writerow(["transcript_id", "exon_number", "start", "end"])
        for tid in sorted(exons):
            for s, e, n in sorted(exons[tid]): w.writerow([tid, n, s, e])
    print(f"gene={args.gene}\ttranscripts={len(tx)}\texons={sum(map(len, exons.values()))}")
    return 0 if tx else 2


if __name__ == "__main__":
    raise SystemExit(main())

