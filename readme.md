# NanoCortex
**Welcome to NanoCortex!**
**This is the official codebase for NanoCortex: A Unified Agentic System for Nanopore Sequencing Analysis**

We are dedicated to advancing the nanopore sequencing field by building intelligent, agent-driven tools that simplify analysis, improve reproducibility, and accelerate biological discovery.  

NanoCortex aims to bridge fragmented nanopore software ecosystems through automated workflows, adaptive reasoning, and seamless integration with existing community tools. Our goal is to empower researchers to extract deeper insights from nanopore data with minimal manual intervention.

We welcome contributions from the community and hope NanoCortex will serve as a foundation for the next generation of intelligent nanopore analysis.

<img src="./figs/logo_final.svg" alt="fig" width="700px" />


<div align="center">


[![Preprint](https://img.shields.io/badge/Preprint-bioRxiv-orange?logo=googlescholar)](https://www.biorxiv.org/)
[![Documentation](https://img.shields.io/badge/docs-available-brightgreen?logo=readthedocs)](https://your-docs-link)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9-blue.svg?logo=python)](https://www.python.org/downloads/release/python-390/)
[![Agent](https://img.shields.io/badge/Agent-geminiadk-blueviolet?logo=google)](https://ai.google.dev/)

</div>

---

## Overview

**NanoCortex** is a unified autonomous agentic framework designed for end-to-end data processing which ranges from raw signal basecalling to biological interpretation.

### Framework

<div align="center">


<img src="./figs/framework_final.svg" alt="fig" width="1200px" />

</div>

---

## Tool list

The following table summarizes external tools and resources integrated in NanoCortex, their primary functions, their implementation within the framework (`AgentTool` vs `FunctionTool`), and links to their official repositories or resources.

| Tool / Resource      | Primary Function(s) | Implementation   | Resource Link |
|----------------------|---------------------|------------------|--------------|
| Dorado               | Basecalling and modification detection (e.g., m5C, m6A, pseudouridine). | AgentTool | [https://github.com/nanoporetech/dorado](https://github.com/nanoporetech/dorado) |
| Modkit               | Quantitative modification frequency reporting and data manipulation. | AgentTool | [https://github.com/nanoporetech/modkit](https://github.com/nanoporetech/modkit) |
| Remora               | Signal-level analysis and visualization of raw nanopore data. | AgentTool | [https://github.com/nanoporetech/remora](https://github.com/nanoporetech/remora) |
| StringTie2           | *De novo* transcriptome assembly and isoform quantification. | AgentTool | [https://github.com/skovaka/stringtie2](https://github.com/skovaka/stringtie2) |
| FLAIR                | Isoform-level analysis, splicing dynamics, and fusion gene detection. | AgentTool | [https://github.com/flairnlp/flair](https://github.com/flairnlp/flair) |
| RNA-FM               | Large-scale RNA foundation model for secondary structure prediction and embedding generation. Downstream modules include splice site prediction and support fine-tuning for various RNA tasks. | AgentTool | [https://github.com/ml4bio/RNA-FM](https://github.com/ml4bio/RNA-FM) |
| NCBI BLAST           | Sequence similarity searching and iterative reference genome refinement. | FunctionTool | [https://blast.ncbi.nlm.nih.gov/Blast.cgi](https://blast.ncbi.nlm.nih.gov/Blast.cgi) |
| GTEx Database        | Integration of physiological transcriptomic baselines for clinical/biological comparison. | AgentTool | [https://gtexportal.org/home/](https://gtexportal.org/home/) |
| PubMed / PMC         | Automated literature retrieval for context-aware interpretation of results. | AgentTool | [https://pubmed.ncbi.nlm.nih.gov/](https://pubmed.ncbi.nlm.nih.gov/) |
| MODOMICS             | Retrieval of curated RNA modification annotations and biochemical pathways. | AgentTool | [https://genesilico.pl/modomics/](https://genesilico.pl/modomics/) |
| Google Search        | General knowledge discovery and retrieval of web-accessible resources. | AgentTool | [https://www.google.com](https://www.google.com) |
| Custom R/Python Scripts Generation and Execution | Generation of code for bioinformatics tools, including samtools, minimap2, and visualization workflows (e.g., density plots, modification landscapes), enabled by autonomous self-correction, validation, and execution. | FunctionTool | [R: https://www.r-project.org/](https://www.r-project.org/)<br/>[Python: https://www.python.org/](https://www.python.org/)<br/>[samtools: https://github.com/samtools/samtools](https://github.com/samtools/samtools)<br/>[minimap2: https://github.com/lh3/minimap2](https://github.com/lh3/minimap2) <br/>[bedtools: https://github.com/arq5x/bedtools2](https://github.com/arq5x/bedtools2) |

---

## Installation

> **Note:** Detailed installation instructions and binary releases will be made available upon publication.

### Step 1: Set Up Environment

For reproducibility and compatibility, we recommend creating a dedicated Conda environment for NanoCortex and its dependencies. To install the core Google ADK component, please refer to the official Conda-Forge feedstock: [google-adk-feedstock](https://github.com/conda-forge/google-adk-feedstock).

```bash
conda create -n adk_env
conda activate adk_env
conda install google-adk
```

### Step 2: Register for a Google Cloud Account and Obtain an API Key

Certain key functionalities within NanoCortex require authenticated access to Google Cloud. You need to create a Google Cloud account and generate an API key. **Keep your API key strictly confidential—never share it publicly or commit it to version control.**

1. Navigate to [Google Cloud Console](https://cloud.google.com/) and sign in, or create a Google account if you do not already have one.
2. Set up a new project as needed, and enable the relevant services (for example, Vertex AI and ADK).
3. Generate your API key by following the instructions at [Google Cloud Console – API Credentials](https://console.cloud.google.com/apis/credentials).
4. Refer to the official Google tutorial for detailed, step-by-step guidance on agent workforce configuration: [Build Your First ADK Agent Workforce](https://cloud.google.com/blog/topics/developers-practitioners/build-your-first-adk-agent-workforce). Additional helpful documentation can be found at [AISTUDIO](https://aistudio.google.com/).
5. Store your API key securely on your local machine. And please put the API key into nano_plus/.env

> **Critical:** Your API key is private and should be treated as a sensitive credential. Never expose, publish, or upload your key in any public repository or third-party service.


### Step 3: Install Singularity

Follow the [official Singularity documentation](https://sylabs.io/guides/) to install Singularity on your system. *Skip this step if you already have Singularity installed.*

### Step 4: Install NanoCortex Software

To build the NanoCortex Singularity image, first clone the GitHub repository if you have not already done so. Next, navigate to the repository’s `singularity` directory and execute the following command to build the container:

```bash
cd NanoCortex/singularity
singularity build bot.sif bot.def
```

This will generate a `bot.sif` image encompassing all required dependencies and software components as specified in `bot.def`. Once the image is built, you can execute and interact with NanoCortex directly within this container.

**Validation:**  
To confirm that Singularity and the necessary tools have been installed successfully, run the following command:

```bash
singularity exec bot.sif modkit --help
```

If the command returns the Modkit help information without error, your installation is successful and the environment is fully operational.



> **Note:** Ensure you have appropriate permissions and Singularity installed before running the build command. For detailed usage instructions and information on running the container, please refer to the official documentation.

*If additional third-party tools or dependencies not encapsulated in the container are required, you will find comprehensive setup and usage guides in the project documentation and supplementary materials.*


## Quick start

<!-- TODO: Replace with your actual CLI/API entry points and minimal runnable commands. -->

### Quick start

Below are three example use cases for the NanoCortex agent framework (HeLa WT vs. TRUB1 KO context). Prompts are templates—substitute your file paths, region coordinates, and folder names. Expected output is left blank for your own benchmarking.

| Example | Prompt | Notes |
|---------|--------|-------|
| 1 | "Using the HEK 293T WT BAM at `[WT_bam_path]`, investigate unaligned reads: where might they come from? Extract or summarize representative sequences and help interpret them with BLAST (or an equivalent search). Output any files in the current working directory." | WT BAM; unaligned-read provenance; BLAST-oriented follow-up. |
| 2 | "You are given a pileup file for HeLa wild-type (WT) and TRUB1 knockout (KO): `[pileup_path]` which comes from `modkit dmr`. To identify sites downregulated in the KO relative to WT, and produce a sequence logo (9-mer) characterizing the motif at those downregulated KO sites. Output files should be saved to the current working directory." | pileup input; differential sites; 9-mer logo for KO downregulated loci. |
| 3 | "For the motif associated with sites downregulated in TRUB1 KO: what is it, and what are its sequence or context preferences? Search the literature (e.g. Google Scholar) and summarize whether published mechanisms align with TRUB1 KO and RNA modification biology. Output any summary files or results to the current path." | Motif interpretation + literature; cross-check with TRUB1 KO. |


> **Note:** All output files generated by these prompts should be saved to the current working directory. Fill in other columns as you test—this allows flexible benchmarking and detailed record-keeping as you develop or extend NanoCortex.

> **Note:** You can find our example HeLa data in the NCBI Sequence Read Archive under accession PRJNA1459519. And if you want to test our software quickly, we provide unaligned, subsampling, and clean fasta file for HEK293T cell line, which can be found in example/data/hek293t_unalign_1000.fasta (Example1). We also provide the subsampling pileup file in example/data/KO_vs_WT_diff_mod_chr13.bed, whcih comes from HeLa cell line for WT and TRUB1 KO(Example2 & 3). Please see more information in our paper about this data. 
---



## Citation

If you use NanoCortex or any components of this ecosystem in your research, please cite:

BibTeX:

```bibtex
@article{nanocortex2026,
  title   = {[NanoCortex: A Unified Agentic System for Nanopore Sequencing Analysis]},
  author  = {[Qini Xia, Ziyuan Wang, Mina Shokoufandeh, Sara H. Rouhanifard, Meni Wanunu]},
  journal = {[bioarXiv]},
  year    = {2026},
  doi     = {[DOI]}
}
```

_(Replace the bracketed fields with the final bibliographic record.)_

---

---

## License

MIT License — see [LICENSE](LICENSE) for details.

## Contact

<!-- Corresponding author email or issue tracker for software questions. -->

- **Issues:** _[GitHub Issues or contact xia.qini@northeastern.edu or princeyuansql@gmail.com]_  
- **Correspondence:** _[Meini Wanunu & Sara H. Rouhanifard, affiliation, wanunu@neu.edu or s.rouhanifard@northeastern.edu]_
