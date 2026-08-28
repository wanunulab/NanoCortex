# Singularity environment

Default image: `singularity/bot.sif` relative to the NanoCortex repository. If the task prompt supplies another `.sif`, use that path directly.

Host command pattern:

```bash
singularity exec <IMAGE.sif> <TOOL> <ARGS>
```

Known container tools: Dorado 1.4.0, Modkit 0.6.1, samtools, minimap2, bedtools, StringTie, R/ggplot2, and conda environments `RNA_FM`, `flair`, and `remora_env`.

Environment command patterns:

```bash
singularity exec <IMAGE.sif> bash -lc 'source /opt/conda/etc/profile.d/conda.sh && conda activate RNA_FM && ReRNAFM --help'
singularity exec <IMAGE.sif> bash -lc 'source /opt/conda/etc/profile.d/conda.sh && conda activate flair && flair --help'
singularity exec <IMAGE.sif> bash -lc 'source /opt/conda/etc/profile.d/conda.sh && conda activate remora_env && remora --help'
```

Do not enumerate the whole image. Test only the command required by the selected workflow.

