# NanoCortex Setup Guide

This document covers software requirements and installation for running the NanoCortex agent ([wanunulab/NanoCortex](https://github.com/wanunulab/NanoCortex)).

NanoCortex has two layers:

1. **Agent host** — Python + Google ADK (or Cursor / Claude Code / Codex skills) that plans analyses and calls tools.
2. **Scientific tool runtime** — a Singularity image (`bot.sif`) that packages Dorado, Modkit, Remora, FLAIR, StringTie, RNA-FM environments, and common genomics utilities.

---

## 1. Prerequisites

| Requirement | Recommended | Notes |
|-------------|-------------|-------|
| OS | Linux (Ubuntu 22.04+) or HPC login node | Singularity is easiest on Linux/HPC |
| Python | 3.9+ | Host agent environment |
| Conda / Mamba | Miniforge or Anaconda | For the ADK host env |
| Singularity / Apptainer | 3.x+ | Required for tool execution |
| Disk | ≥ 50–100 GB free | `bot.sif` and models are large |
| GPU (optional) | NVIDIA + CUDA-compatible driver | Basecalling / Remora / RNA-FM benefit from GPU |
| Network | Outbound HTTPS | Google API, Hugging Face download, PubMed / BLAST if used |

> **Tip:** Download `bot.sif` on an HPC node or machine with ample storage. Local laptops may be too small for the full image.

---

## 2. Clone the repository

```bash
git clone https://github.com/wanunulab/NanoCortex.git
cd NanoCortex
```

Repository layout (abbreviated):

```
NanoCortex/
├── ont_plus/              # Google ADK agent package (main agent entry)
├── singularity/
│   ├── bot.def            # Singularity definition
│   └── bot.sif            # Pre-built image (download; not in git)
├── Reconstruction_RNAFM/  # RNA-FM helpers used inside the container
├── skills/                # On-shelf skills for Codex / Cursor / Claude Code / Gemini
├── example/               # Small demo inputs
└── readme.md
```

---

## 3. Host agent environment (Google ADK)

Create a dedicated Conda environment for the agent host:

```bash
conda create -n adk_env python=3.9 -y
conda activate adk_env

pip install \
  google-adk==1.22.1 \
  pandas==2.2.3 \
  scipy==1.13.1 \
  python-dotenv \
  pydantic
```

> Pin versions to match your local testing if the paper environment differs. The ADK feedstock is also available via Conda-Forge: [google-adk-feedstock](https://github.com/conda-forge/google-adk-feedstock).

Optional Python packages used by some host-side scripts (install as needed):

```bash
pip install requests biopython pysam
```

---

## 4. Google API key

Several NanoCortex capabilities use Google Gemini via ADK. Keep the key private.

1. Open [Google Cloud Console](https://cloud.google.com/) or [Google AI Studio](https://aistudio.google.com/).
2. Create / select a project and enable the required Gemini / Vertex APIs.
3. Create an API key under [API Credentials](https://console.cloud.google.com/apis/credentials).
4. Put the key in `ont_plus/.env`:

```bash
# ont_plus/.env
GOOGLE_API_KEY=YOUR_KEY_HERE
```

**Never commit `.env` or publish the key.**

Helpful references:

- [Build Your First ADK Agent Workforce](https://cloud.google.com/blog/topics/developers-practitioners/build-your-first-adk-agent-workforce)
- [Google AI Studio](https://aistudio.google.com/)

---

## 5. Singularity scientific runtime (`bot.sif`)

### Option A (recommended): download the pre-built image

1. Download `bot.sif` from Hugging Face:  
   [qinixia/NanoCortex-singularity](https://huggingface.co/qinixia/NanoCortex-singularity/blob/main/singularity/bot.sif)
2. Place it next to the definition file:

```bash
# expected path
NanoCortex/singularity/bot.sif
```

### Option B: build from `bot.def`

Requires Singularity/Apptainer, root or fakeroot privileges (or a compatible build service), and substantial download time:

```bash
cd NanoCortex/singularity
singularity build bot.sif bot.def
```

### Validate the image

```bash
singularity exec singularity/bot.sif dorado --version
singularity exec singularity/bot.sif modkit --help
singularity exec singularity/bot.sif samtools --version
singularity exec singularity/bot.sif stringtie --version
```

If `modkit --help` prints without error, the core container path is working.

---

## 6. Software inside `bot.sif`

Built from `singularity/bot.def` (CUDA 12.1 / Ubuntu 22.04 base):

| Category | Software | Version / notes |
|----------|----------|-----------------|
| Basecalling / mods | Dorado | v1.4.0 |
| Modification toolkit | Modkit | v0.6.1 |
| Alignment / BAM | samtools, minimap2, bedtools | system packages |
| Transcript assembly | StringTie | built from source |
| Signal / Remora | Conda env `remora_env` | Python 3.9 + `ont-remora` + PyTorch CUDA |
| Isoforms / fusions | Conda env `flair` | bioconda `flair` |
| RNA foundation model | Conda env `RNA_FM` | `rna-fm`, PyTorch, scientific Python |
| Plotting / motifs | R + ggplot2, dplyr, ggseqlogo, universalmotif, motifStack | R 4.3+ |

### Typical invocation patterns

```bash
# Dorado / Modkit / StringTie (on PATH in the image)
singularity exec ./singularity/bot.sif dorado ...
singularity exec ./singularity/bot.sif modkit ...
singularity exec ./singularity/bot.sif stringtie ...

# FLAIR
singularity exec ./singularity/bot.sif /opt/conda/envs/flair/bin/flair ...

# Remora / signal plotting (bind host scripts when needed)
singularity exec -B ./ont_plus:/ont_plus ./singularity/bot.sif \
  /opt/conda/envs/remora_env/bin/python /ont_plus/signal_function.py ...

# RNA-FM helpers
singularity exec -B ./Reconstruction_RNAFM:/Reconstruction_RNAFM ./singularity/bot.sif \
  mamba run -n RNA_FM ...
```

Bind (`-B`) any host directories that contain inputs, references, or project scripts.

---

## 7. Launch the Google ADK web agent

From the repository root (with `adk_env` activated and `ont_plus/.env` set):

```bash
cd /path/to/NanoCortex
conda activate adk_env
adk web --host 0.0.0.0 --port 8000
```

Then open [http://localhost:8000](http://localhost:8000) and select the **`ont_plus`** agent folder in the UI.

> Save generated code/scripts into your working folder when prompted by the agent — this reduces repeated generation and token use.

---

## 8. Alternative agent platforms (skills)

On-shelf skill packages live under `skills/`. Install only the platform you use.

| Platform | Skill directory | Install target |
|----------|-----------------|----------------|
| OpenAI Codex | `skills/codex/` | `$CODEX_HOME/skills/nanocortex` |
| Cursor | `skills/cursor/` | `~/.cursor/skills/nanocortex` or `.cursor/skills/nanocortex` |
| Claude Code | `skills/claude-code/` | `~/.claude/skills/nanocortex` or `.claude/skills/nanocortex` |
| Gemini ADK | `skills/gemini/` | set `NANOCORTEX_GEMINI_SKILL_DIR` and load skill/agents context |

Example (Cursor):

```bash
mkdir -p ~/.cursor/skills
cp -R skills/cursor ~/.cursor/skills/nanocortex
```

Verify skill scripts + container:

```bash
python3 ~/.cursor/skills/nanocortex/scripts/query_parameters.py dorado --list
singularity exec singularity/bot.sif dorado --version
```

See `skills/readme.md` and each platform `README.md` for run notes (permissions, Slurm, signal agent routing).

---

## 9. Project-level agent prompt (biological replicates)

During setup, add a **project-level** instruction so the agent always checks whether biological replicates are present before drawing biological conclusions. If replicates are missing, the agent must **flag that findings lack replicate validation** and must not overstate significance.

Recommended prompt text (copy into the project instruction file for your agent platform):

```text
Before interpreting biological findings, check sample metadata for biological replicates.
- If biological replicates are present, state the replicate design briefly and proceed with the analysis.
- If biological replicates are absent (n = 1, technical replicates only, or replicate metadata missing):
  1. Still report the computational results.
  2. Explicitly warn that conclusions lack biological-replicate validation.
  3. Label findings as exploratory / hypothesis-generating, not definitive.
  4. Do not claim statistical significance for differential biological effects without an appropriate replicated design.
If replicate status is unclear, ask the user to clarify before strong biological claims.
```

Install this prompt at project scope (not only in a one-off chat):

| Platform | Where to add the prompt |
|----------|-------------------------|
| Cursor | Project rule, e.g. `.cursor/rules/nanocortex-replicates.mdc`, or `AGENTS.md` at the repo root |
| Claude Code | `CLAUDE.md` at the NanoCortex / analysis project root |
| Codex | Project `AGENTS.md` or the skill instruction block under `skills/codex/` |
| Gemini ADK | Root agent instruction in `ont_plus/agent.py` (or a loaded project instruction file) |

Example (Claude Code / generic project root):

```bash
cat >> CLAUDE.md << 'EOF'

## Biological replicate policy
Before interpreting biological findings, check sample metadata for biological replicates.
If biological replicates are absent, still report computational results but explicitly warn that
conclusions lack biological-replicate validation; treat findings as exploratory only.
EOF
```

Example (Cursor project rule):

```bash
mkdir -p .cursor/rules
cat > .cursor/rules/nanocortex-replicates.mdc << 'EOF'
---
description: Flag missing biological replicates in NanoCortex analyses
alwaysApply: true
---
Before interpreting biological findings, check sample metadata for biological replicates.
If biological replicates are absent, report results but warn that conclusions lack
biological-replicate validation and treat findings as exploratory only.
EOF
```

> This does not invent replicates; it makes the agent **state the limitation** whenever replicate evidence is missing.

---

## 10. Example data (optional quick test)

Small demo files are under `example/data/`:

- `hek293t_unalign_1000.fasta` — unaligned-read / BLAST-style example
- `KO_vs_WT_diff_mod_chr13.bed` — Modkit DMR / motif example

Larger HeLa WT vs TRUB1 KO data: NCBI SRA **PRJNA1459519**.

---

## 11. Installation checklist

- [ ] Clone `wanunulab/NanoCortex`
- [ ] Create `adk_env` and install `google-adk` (+ pandas / scipy / dotenv)
- [ ] Set `GOOGLE_API_KEY` in `ont_plus/.env`
- [ ] Install Singularity / Apptainer
- [ ] Place `singularity/bot.sif` (download or build)
- [ ] `singularity exec singularity/bot.sif modkit --help` succeeds
- [ ] `adk web` launches and `ont_plus` appears in the UI  
  **or** install the matching skill for Cursor / Claude Code / Codex / Gemini
- [ ] Add the **project-level biological-replicate prompt** (`CLAUDE.md` / Cursor rule / ADK instruction)
- [ ] (Optional) GPU visible inside the container for Dorado / Remora / RNA-FM

---

## 12. Troubleshooting

| Issue | What to try |
|-------|-------------|
| `bot.sif` missing | Download from Hugging Face into `singularity/` |
| Singularity build fails on HPC | Prefer the pre-built `.sif`; build on a machine with Docker/fakeroot if needed |
| ADK cannot find API key | Confirm `ont_plus/.env` contains `GOOGLE_API_KEY=...` and is loaded |
| Tool not found in container | Use full env paths (e.g. `/opt/conda/envs/flair/bin/flair`) |
| Host paths invisible in container | Add `-B /host/path:/container/path` |
| Out of disk while downloading | Use HPC scratch; image + models are large |
| R plotting on headless nodes | Prefer host-module R as instructed by the agent, or set non-interactive R options |
| Agent overclaims on n = 1 data | Confirm the project-level replicate prompt is installed and always applied |

---

## 13. Citation and support

Paper: [bioRxiv 10.64898/2026.05.19.726254](https://www.biorxiv.org/content/10.64898/2026.05.19.726254v1)

Issues / software questions: GitHub Issues, or `qinixia77@gmail.com` / `princeyuansql@gmail.com`.

License: MIT — see `LICENSE.txt`.
