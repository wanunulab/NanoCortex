---
name: nanocortex
description: Execute Oxford Nanopore and RNA workflows in Claude Code with NanoCortex's Singularity image, including Dorado, Modkit, transcript/splicing analysis, RNA-FM structure prediction, and Remora signal plotting. Use for nanopore BAM/BED, GTF isoforms, RNA FASTA, POD5 signal plots, Singularity execution, validation, or biological summaries in Claude Code.
---

# NanoCortex for Claude Code

Install this directory at `~/.claude/skills/nanocortex` (personal) or `.claude/skills/nanocortex` (project). Run tasks from the NanoCortex repository root with Bash and file-access permissions approved.

Default container: `singularity/bot.sif` relative to the NanoCortex repository. Do not install alternative software when the container is available.

Read [references/environment.md](references/environment.md) only when the direct Singularity command is unavailable.

## Claude Code execution model

1. Use the Bash tool for all shell and Singularity commands.
2. Request only the permissions needed for the current step. Do not batch unrelated filesystem access.
3. Use absolute paths for inputs, outputs, `SKILL_DIR`, and `BOT_SIF`.
4. Keep a concise execution log: command, exit code, stderr summary, and output paths.
5. On failure, inspect stderr once, apply one targeted fix, and retry.

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

For Dorado, Modkit, or RNA-FM option lookup, use `scripts/query_parameters.py` with the bundled JSON specifications.
