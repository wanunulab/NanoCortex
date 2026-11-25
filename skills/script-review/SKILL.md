---
name: slurm-explainer
description: Validate a Nanopore/SLURM script for new bioinformatics analysts. Asks whether to output HTML or PDF, then runs a 2-phase workflow that explains every tool and flags RNA/DNA mistakes.
triggers:
  - "explain this slurm"
  - "validate slurm"
  - "slurm script"
  - "sbatch script"
  - "explain my job script"
  - "dorado script"
  - "remora"
  - "nanopore script"
  - "modkit"
---

# SLURM Explainer Skill

This skill validates and explains a SLURM batch script containing Nanopore tools.
It runs as a **2-phase workflow** (Analyse → Report) and outputs either a styled
HTML page or clean PDF-ready markdown.

---

## Step 1 — Ask the user for the output format

Use the AskUserQuestion tool with this exact question:

**Question:** "What format would you like for the report?"
**Options:**
- HTML report — opens as a styled web page you can share or bookmark
- PDF-ready markdown — clean text you can print or export with pandoc

Wait for the answer before proceeding.

---

## Step 2 — Get the SLURM script

If the user has not already pasted their script, ask them to paste it now:

> "Please paste your SLURM batch script and I'll analyse it."

---

## Step 3 — Launch the workflow

Call the **Workflow tool** with:
- `name`: `"slurm-explainer"`
- `args`: a JSON object with two fields:
  - `script`: the full text of the SLURM script the user pasted
  - `format`: `"html"` if they chose HTML, or `"pdf"` if they chose PDF-ready markdown

Example:
```json
{
  "script": "#!/bin/bash\n#SBATCH --job-name=basecall\n...",
  "format": "html"
}
```

The workflow runs two phases automatically:

| Phase | What happens |
|-------|--------------|
| **Analyse** | Reads the script; validates RNA/DNA settings, Dorado model, modkit flags, SLURM GPU requirement; produces structured findings |
| **Report** | Formats the findings — HTML = styled Artifact with colour-coded badges; PDF = clean markdown with tables |

---

## What the workflow checks (reference)

The workflow validates these things in priority order:

### RNA vs DNA (most critical)
| Check | Severity |
|-------|----------|
| DNA model (`dna_*`) used on RNA data or RNA model (`rna_*`) on DNA data | ERROR |
| `dorado duplex` called on RNA data (duplex = DNA only) | ERROR |
| `minimap2 -ax map-ont` on direct RNA reads (must be `-ax splice -uf -k14`) | ERROR |
| `--modified-bases 5mCG` on RNA data (should be `m6A_DRACH`) | ERROR |
| Kit name does not match model data type | WARNING |
| `-uf` missing from RNA minimap2 command | WARNING |

### Dorado model
| Check | Severity |
|-------|----------|
| Model name does not match a valid pattern | ERROR |
| `fast` accuracy tier used (hac/sup recommended) | WARNING |
| Version not pinned (`@v...` missing) | WARNING |

### modkit
| Check | Severity |
|-------|----------|
| `modkit pileup` on BAM with no MM/ML tags (Dorado run without `--modified-bases`) | ERROR |
| `--combine-strands` on RNA data (m6A is not strand-symmetric) | ERROR |
| `--ref` missing from `modkit pileup` | WARNING |
| `--mod-thresholds` not set | WARNING |
| `--cpg` filter used on RNA data | INFO |

### SLURM resources
| Check | Severity |
|-------|----------|
| Dorado present but `--gres=gpu` missing | ERROR |
| `--mem` not set | WARNING |
| `set -euo pipefail` missing | WARNING |
| `module load` without pinned version | WARNING |
| `--cpus-per-task` not forwarded to samtools | INFO |

---

## Output formats explained

**HTML** — a full web page published as a Claude Artifact:
- Colour-coded severity badges (red/orange/blue)
- Summary banner showing data type (DNA/RNA) and finding counts
- Each tool in its own card with a flag table
- Corrected script with changed lines highlighted in yellow

**PDF-ready markdown** — a clean text document:
- Pandoc-compatible YAML frontmatter (`title`, `date`)
- Tables for SLURM resources and tool flags
- Findings as blockquote callouts grouped by severity
- Corrected script in a fenced code block

---

## Tone and language rules

- Keep SLURM explanations to one sentence per directive.
- Explain every Dorado / modkit flag in plain language.
- Define jargon on first use (e.g. "HAC — High Accuracy, the mid-tier basecalling model").
- RNA/DNA mismatches produce silently wrong results — flag them clearly and urgently.
- Assume the reader knows biology but is new to the command line.


