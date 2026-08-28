# Regional nanopore signal plotting (Gemini ADK)

Use the bundled NanoCortex Remora implementation; do not recreate the signal-alignment or plotting code.

For Gemini ADK deployments, route signal-plot requests through `agents/signal_agent.py` when the native ADK graph is available. Otherwise execute the Singularity command below through the ADK code-execution tool.

Required inputs:

- Remora k-mer model (`.model`)
- modified-sample POD5 and indexed BAM
- canonical/control POD5 and indexed BAM
- contig, strand, zero-based start, and zero-based end
- output `.pdf` or `.png`

Confirm only that the paths exist, BAM indexes are available, `start < end`, and the requested contig occurs in both BAMs. Then run:

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

- `<SKILL_DIR>`: absolute path to this Gemini skill directory
- `<DATA_ROOT>`: absolute path to the directory containing inputs/outputs
- `<BOT_SIF>`: absolute path to `singularity/bot.sif`

Keep the defaults unless the request supplies different plotting limits. Validate with:

```bash
python3 <SKILL_DIR>/scripts/validate_plot.py <OUTPUT>
```

Report the genomic interval, sample roles, reads cap, y-axis range, and output path.

Implementation provenance:

- `scripts/signal/signal_function.py`: CLI and Remora orchestration
- `scripts/signal/newio.py`: signal mapping, aggregation, and plotting
- `agents/signal_agent.py`: original Google ADK instruction retained for provenance; use only inside Gemini ADK
