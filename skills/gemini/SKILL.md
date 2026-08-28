---
name: nanocortex
description: Execute Oxford Nanopore and RNA workflows in Gemini ADK with NanoCortex's Singularity image, including Dorado, Modkit, transcript/splicing analysis, RNA-FM structure prediction, and Remora signal plotting. Use for nanopore BAM/BED, GTF isoforms, RNA FASTA, POD5 signal plots, ADK agent workflows, validation, or biological summaries in Gemini.
---

# NanoCortex for Gemini ADK

Load this directory as the instruction context for a Gemini ADK agent deployed on Linux with filesystem and shell access (Always Allow). Run tasks from the NanoCortex repository root.

Default container: `singularity/bot.sif` relative to the NanoCortex repository. Do not install alternative software when the container is available.

Read [references/environment.md](references/environment.md) only when the direct Singularity command is unavailable.

## Gemini ADK execution model

1. Route signal-plotting requests to `agents/signal_agent.py` when using the native ADK agent graph.
2. For all other workflows, follow the reference files and execute commands through the ADK code-execution tool.
3. Use absolute paths for inputs, outputs, `SKILL_DIR`, and `BOT_SIF`.
4. Preserve command records, exit codes, stderr excerpts, and validation results in the agent response.
5. On failure, apply one targeted correction from stderr, then retry.

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
