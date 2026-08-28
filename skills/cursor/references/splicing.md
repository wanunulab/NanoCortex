# Transcript and splicing workflow

For an existing GTF, summarize it directly; do not rerun StringTie.

- Match the requested gene using `gene_name`, `ref_gene_name`, `gene_id`, or `ref_gene_id`.
- Parse GTF attributes by key and reconstruct exon chains in strand-aware genomic order.
- Use `scripts/summarize_gtf_gene.py` to produce transcript and exon-chain tables.
- Compare isoforms using available TPM or coverage. A single-sample GTF supports isoform description, not differential-splicing inference.
- Validate transcript count, exon count, exon ordering, and transcript-bound consistency.

