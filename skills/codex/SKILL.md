---
name: nanocortex
description: Execute Oxford Nanopore and RNA workflows through OpenAI Codex with NanoCortex's Singularity image, including Dorado, Modkit, transcript/splicing analysis, RNA-FM structure prediction, and Remora signal plotting. Use for nanopore BAM/BED, GTF isoforms, RNA FASTA, POD5 signal plots, HPC workflow execution, validation, or biological summaries in Codex CLI.
---

# NanoCortex for OpenAI Codex

Install this directory at `$CODEX_HOME/skills/nanocortex`. Run tasks from the NanoCortex repository root with shell and filesystem access enabled (Auto-approve).

Default container: `singularity/bot.sif` relative to the NanoCortex repository. Do not install alternative software when the container is available.

Read [references/environment.md](references/environment.md) only when the direct Singularity command is unavailable.

## Codex execution model

1. Use the Codex shell tool for every command. Prefer one complete command per step.
2. Record command, exit code, stderr, and output paths in the final response.
3. Use absolute paths for inputs, outputs, `SKILL_DIR`, and `BOT_SIF`.
4. On non-zero exit, inspect stderr once, apply one targeted fix, and retry. Do not explore unrelated files.

## Fast path

1. Identify the task from the request and input suffix.
2. Read exactly one reference:
   - raw reads/basecalling: [references/dorado.md](references/dorado.md)
   - modification BAM/BED: [references/modification.md](references/modification.md)
   - GTF/isoforms/splicing: [references/splicing.md](references/splicing.md)
   - RNA FASTA/structure: [references/rna-structure.md](references/rna-structure.md)
   - POD5/BAM signal plot: [references/signal.md](references/signal.md)
3. Prefer bundled scripts. Run `python3 <SKILL_DIR>/scripts/<script>.py --help` before use.
4. Verify the selected container tool once with `--help` or `--version`, then execute.
5. Validate outputs with the bundled validator or the checks in the selected reference.
6. Return method, parameters, main results, output paths, and limitations.

## Singularity pattern

```bash
singularity exec <BOT_SIF> <TOOL> <ARGS>
```

For conda-backed tools:

```bash
singularity exec <BOT_SIF> bash -lc 'source /opt/conda/etc/profile.d/conda.sh && conda activate <ENV> && <TOOL> <ARGS>'
```

For Dorado, Modkit, or RNA-FM option lookup, use `scripts/query_parameters.py` with the bundled JSON specifications.
