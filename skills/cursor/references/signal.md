# Regional nanopore signal plotting (Cursor)

Use the bundled NanoCortex Remora implementation; do not recreate the signal-alignment or plotting code.

Required inputs:

- Remora k-mer model (`.model`)
- modified-sample POD5 and indexed BAM
- canonical/control POD5 and indexed BAM
- contig, strand, zero-based start, and zero-based end
- output `.pdf` or `.png`

Confirm only that the paths exist, BAM indexes are available, `start < end`, and the requested contig occurs in both BAMs. Run in the integrated terminal:

```bash
singularity exec \
  -B <SKILL_DIR>/scripts/signal:/opt/nanocortex_signal \
  -B <DATA_ROOT>:<DATA_ROOT> \
  <BOT_SIF> \
  /opt/conda/envs/remora_env/bin/python \
  /opt/nanocortex_signal/signal_function.py \
  --kmer_table <KMER_MODEL> \
  --mod_pod5 <MOD_POD5> --mod_bam <MOD_BAM> \
  --can_pod5 <CAN_POD5> --can_bam <CAN_BAM> \
  --chr <CONTIG> --strand <+|-> --start <START> --end <END> \
  --save_path <OUTPUT> --max_reads 100 --ylim_min -3 --ylim_max 3
```

Placeholders:

- `<SKILL_DIR>`: path to this Cursor skill directory
- `<DATA_ROOT>`: workspace directory containing inputs/outputs when possible
- `<BOT_SIF>`: `singularity/bot.sif` in the open NanoCortex workspace

Keep the defaults unless the request supplies different plotting limits. Validate with:

```bash
python3 <SKILL_DIR>/scripts/validate_plot.py <OUTPUT>
```

Report the genomic interval, sample roles, reads cap, y-axis range, and output path.

Implementation provenance:

- `scripts/signal/signal_function.py`: CLI and Remora orchestration
- `scripts/signal/newio.py`: signal mapping, aggregation, and plotting
