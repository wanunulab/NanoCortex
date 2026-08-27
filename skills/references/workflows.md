# NanoCortex workflow reference

## Contents

- Dorado
- Modkit
- RNA-FM/ReRNAFM
- Transcriptome analysis
- GTEx
- Signal analysis
- Sequence and scientific interpretation
- Execution environments

## Dorado

Use Dorado for raw-read processing. Determine the goal, molecule type, input path, output path, and whether modified-base detection or alignment is requested.

For basecalling, default to the `hac` model only when the user has not specified an accuracy tier. Use `fast`, `hac`, or `sup` as supported by the installed Dorado version. Do not infer a chemistry-specific model name without inspecting the data/model inventory. If modification detection is requested, identify the exact modifications and verify model compatibility against current Dorado documentation or the installed model list.

Ask for a reference genome only when alignment is requested. Suggest move-table emission only when downstream signal-to-sequence alignment requires it.

## Modkit

Use Modkit after basecalling/alignment or with an existing compatible BAM. Confirm that the BAM is sorted/indexed when required and that modified-base tags are present. Identify reference build, region or motif scope, sample comparison, filtering thresholds, and output format.

For differential analysis, verify group labels and replicate structure. Do not describe a site as biologically downregulated solely from an unadjusted percentage difference; report the statistical and coverage criteria used.

## RNA-FM/ReRNAFM

Supported high-level tasks are `embed`, `predict_ss`, `cluster`, `classify`, and `predict_expression`. Determine the chosen task plus its required input and output. Accept direct sequences only when supported; otherwise use a FASTA or the task-specific table/folder.

Prefer GPU for large embedding or training workloads, but do not assume CUDA is present. Inspect hardware and provide a CPU fallback when feasible.

## Transcriptome analysis

Use FLAIR for annotation-guided long-read isoform analysis, quantification, and fusion workflows. Use StringTie when the primary goal is discovering transcripts absent from the supplied annotation. Confirm reference genome, annotation GTF, aligned reads, read type, sample labels, and desired output directory.

Consult current official documentation before generating FLAIR or StringTie commands because their interfaces are not bundled in the parameter JSON files.

## GTEx

Resolve the gene symbol to the correct GENCODE/Ensembl identifier and record the GTEx release. Match tissues carefully. Use isoform TPM and usage proportions as healthy-tissue context. State that GTEx is a population reference and may differ in tissue composition, batch, ancestry, age, and technical protocol from the user's samples.

## Signal analysis

Require a k-mer model, modified-sample POD5 and indexed BAM, canonical/control POD5 and indexed BAM, chromosome/contig, strand, zero-based start, zero-based end, and output plot path. Optional controls include maximum reads and y-axis limits. Confirm that BAM read identifiers correspond to the POD5 data and that coordinate conventions match.

The legacy implementation used Remora plus a custom plotting module. Reuse that implementation only when its Python environment and source files are available; otherwise explain the missing dependency rather than fabricating output.

## Sequence and scientific interpretation

For BAM/SAM, use tools such as samtools for inspection and extraction. For BED, pileup, CSV, and TSV, validate schema and coordinate convention before computing. For sequences, choose nucleotide or protein search appropriately and record database, program, query date, and top-hit criteria.

For plots, use any reproducible library available in the environment; preserve the source table and plotting script. Literature searches should connect each mechanistic claim to a primary source and should distinguish direct evidence from inference.

## Execution environments

Prefer an installed native command when version-compatible. Use a project container when it is provided and approved. On HPC systems, inspect environment modules rather than assuming module names. Bind only required directories into containers and use absolute paths when possible.
