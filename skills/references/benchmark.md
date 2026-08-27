# Cross-backend benchmark

Use identical task text, input files, skill files, shell access, filesystem permissions, network setting, timeout, and scoring rules for every backend. Do not tune a task after seeing one backend's result unless every backend is rerun.

## Minimal matched test

Use three inexpensive tasks derived from submitted NanoCortex benchmark categories:

1. Inspect a small FASTA and generate a validated RNA-FM secondary-structure command without running the model.
2. Inspect WT, KO, and reference fixtures and generate a validated Modkit DMR pair command without executing the expensive analysis.
3. Execute a tiny modification-site summary with a deliberately invalid option, consult help after the non-zero exit, correct the option, and produce a deterministic JSON result.

Do not rerun Dorado basecalling or reproduce biological figures solely to establish backend portability.

## Objective scoring

Score only machine-checkable conditions:

- required input files were inspected;
- the intended domain tool and subcommand were selected;
- required paths, sample order, reference, threshold, and output were correct;
- prohibited or unsupported options were absent;
- a non-zero exit code was recorded;
- help was consulted after failure;
- a corrected command returned zero;
- the expected output exists, parses, and has the reference values.

Report each check as pass or fail. Do not use an LLM judge or a subjective quality score.

## Run metadata

Record provider, exact model identifier, agent interface, date, skill archive hash, operating system, Python version, exposed tools, shell access, filesystem read/write scope, network access, and per-task timeout. Preserve raw commands, exit codes, stdout, stderr, and output artifacts.

Compatibility is supported when the same unmodified skill and matched environment complete the prespecified checks on more than one backend. Do not claim scientific-performance equivalence from this conformance test.
