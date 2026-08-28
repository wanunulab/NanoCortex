# Modification workflow

For BAM input, use Modkit through Singularity. For an existing Modkit BED/DMR result, analyze the table directly; do not rerun upstream calling.

- Confirm whether the table has a header and determine the effect, coverage, probability/fraction, and significance columns from the producing schema or task context.
- State contrast direction before labeling increased/decreased sites.
- Prefer `scripts/analyze_modification_table.py` for filtering and classification.
- Use `scripts/plot_category_counts.py` for a simple reproducible figure.
- Require total and category counts to reconcile; report excluded or unclassified rows.
- For Modkit commands, query `scripts/query_parameters.py modkit <subcommand>`.

