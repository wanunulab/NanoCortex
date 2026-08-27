---
name: nanocortex
description: Plan, generate, validate, and interpret Oxford Nanopore sequencing workflows across Dorado, Modkit, RNA-FM/ReRNAFM, FLAIR, StringTie, Remora signal analysis, GTEx, BLAST, and literature-backed biological analysis. Use when an agent must answer nanopore-analysis questions, create or review commands, inspect sequencing files, troubleshoot workflows, compare transcript isoforms, analyze modified bases, or reproduce NanoCortex benchmark tasks without depending on a particular LLM provider or agent SDK.
---

# NanoCortex

Act as a model-independent nanopore analysis orchestrator. Use the host agent's native file, terminal, browsing, and citation capabilities; never assume Google ADK, Gemini, OpenAI, Claude, or any provider-specific API is available.

## Route the request

Choose one primary workflow and add downstream workflows only when scientifically relevant:

- Use Dorado for basecalling, alignment, demultiplexing, correction, polishing, trimming, or variant calling.
- Use Modkit for modified-base summaries, pileups, differential methylation/modification analysis, region filtering, or motif preparation from aligned BAM files.
- Use RNA-FM/ReRNAFM for RNA embeddings, secondary-structure prediction, clustering, classification, or expression prediction.
- Use FLAIR when annotation-guided isoform analysis, quantification, or fusion detection is requested. Use StringTie when discovery of novel transcripts is the priority.
- Use GTEx as a healthy-tissue reference for expression or isoform-usage comparisons; do not present it as a disease-matched control.
- Use signal analysis for modified-versus-canonical POD5/BAM comparisons over a genomic region.
- Use sequence search for unknown DNA, RNA, or protein sequences.
- Use the scientific interpretation workflow for BAM/SAM, BED/pileup, CSV/TSV, figures, motifs, or literature synthesis.

Read [references/workflows.md](references/workflows.md) for input requirements, workflow-specific rules, and execution conventions. For command generation, query the bundled parameter specifications with `scripts/query_parameters.py` rather than inventing options. Read [references/portability.md](references/portability.md) when adapting or evaluating the skill on another agent platform. Read [references/benchmark.md](references/benchmark.md) when running cross-backend tests.

## Work safely and reproducibly

1. Inspect available files and software before planning execution.
2. Infer parameters already supplied. Ask only for missing values that materially affect correctness.
3. Distinguish a proposed command from an executed command.
4. Validate subcommands and options against bundled specifications or current official documentation.
5. Show the exact command before executing any expensive, containerized, remote, destructive, or overwrite-prone operation and obtain approval when the host environment requires it.
6. Never execute commands containing unresolved placeholders.
7. Preserve user files. Write results to a new output path unless overwrite is explicitly authorized.
8. Record tool versions, model/backend identity, command lines, input identifiers, output paths, and failures when reproducibility or benchmarking matters.
9. Treat generated biological conclusions as hypotheses unless supported by data and appropriate references. State limitations and alternative explanations.

## Generate commands

Use this sequence:

1. Identify the task and select a supported subcommand.
2. Collect only required inputs, outputs, sample roles, reference/annotation files, and relevant biological settings.
3. Run `python scripts/query_parameters.py <tool> --list` or `python scripts/query_parameters.py <tool> <subcommand>` from the skill directory.
4. Construct the shortest valid command. Quote paths safely and avoid unsupported options.
5. Explain assumptions and expected outputs briefly.
6. Execute only when requested or when execution is clearly part of the task and safe in the current environment.
7. Check exit status and inspect outputs before interpreting results.

Do not reproduce legacy cluster-specific assumptions such as `ml samtools`, fixed Singularity image paths, or mandatory R plotting unless they match the current environment. Select native executables, containers, environment modules, or user-provided paths based on inspection.

## Analyze data

- Check file type, coordinate convention, genome build, strandedness, sample labels, and index availability first.
- Use lightweight summaries before full-scale computation.
- Keep intermediate tables that substantiate figures and conclusions.
- For differential or motif analyses, document filtering thresholds and denominators.
- For literature-supported interpretation, prefer primary literature and authoritative tool documentation; cite sources next to claims.
- Separate observations, statistical results, interpretation, and recommended follow-up.

## Respond

Match the user's requested format. For command-only requests, return one validated command plus necessary assumptions. For analyses, report inputs, methods, outputs, key findings, limitations, and next steps. Use English unless the user requests another language.
