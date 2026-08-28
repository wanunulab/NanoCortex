# RNA secondary-structure workflow

1. Run `scripts/inspect_fasta.py` and stop if records are empty, duplicated, or contain invalid symbols.
2. Query `scripts/query_parameters.py rnafm predict_ss`.
3. Run ReRNAFM `predict_ss` in the Singularity `RNA_FM` environment. Use CPU unless the task explicitly requests GPU.
4. Preserve FASTA identifiers and write results to an output directory so ReRNAFM can generate its supported formats.
5. Run `scripts/validate_ct.py` for CT outputs and `scripts/summarize_structure_outputs.py` for the final table.
6. Require one valid result per input record and matching sequence/structure lengths.

