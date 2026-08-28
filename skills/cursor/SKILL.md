---
name: nanocortex
description: Execute Oxford Nanopore and RNA workflows in Cursor with NanoCortex's Singularity image, including Dorado, Modkit, transcript/splicing analysis, RNA-FM structure prediction, and Remora signal plotting. Use when the user mentions NanoCortex, nanopore reads, BAM/BED modifications, GTF isoforms, RNA FASTA, POD5 signal plots, Singularity workflows, or asks to run @nanocortex.
disable-model-invocation: true
---

# NanoCortex for Cursor

Install this directory at `~/.cursor/skills/nanocortex` (personal) or `.cursor/skills/nanocortex` (project). Invoke explicitly with `@nanocortex`.

Open the NanoCortex repository as the workspace when possible. Default container: `singularity/bot.sif`. Do not install alternative software when the container is available.

Read [references/environment.md](references/environment.md) only when the direct Singularity command is unavailable.

## Cursor execution model

1. Use the integrated terminal for shell commands. Keep commands copy-pasteable and minimal.
2. Prefer workspace-relative paths when the NanoCortex repo is open; otherwise use absolute paths.
3. Read only the selected reference, script `--help`, and named input files. Do not recursively search the repo.
4. On failure, make one targeted correction from stderr, then retry once before escalating.

## Fast path

1. Identify the task from the request and input suffix.
2. Read exactly one reference:
   - raw reads/basecalling: [references/dorado.md](references/dorado.md)
   - modification BAM/BED: [references/modification.md](references/modification.md)
   - GTF/isoforms/splicing: [references/splicing.md](references/splicing.md)
   - RNA FASTA/structure: [references/rna-structure.md](references/rna-structure.md)
   - POD5/BAM signal plot: [references/signal.md](references/signal.md)
3. Prefer bundled scripts. Run `python3 scripts/<script>.py --help` from this skill directory.
4. Verify the selected container tool once with `--help` or `--version`, then execute.
5. Validate outputs with the bundled validator or the checks in the selected reference.
6. Summarize method, parameters, main results, output paths, and limitations.

For Dorado, Modkit, or RNA-FM option lookup, use `scripts/query_parameters.py` with the bundled JSON specifications.
