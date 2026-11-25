/ ─────────────────────────────────────────────────────────────────────────────
// SLURM + Nanopore Script Explainer Workflow
//
// What it does:
// Phase 1 "Analyse" — reads the script and produces structured findings
// (SLURM settings, tool flags, RNA/DNA errors, etc.)
// Phase 2 "Report" — takes those findings and renders them as either
// a styled HTML page (Artifact) or PDF-ready markdown
//
// How to run it (the skill does this automatically):
// args = {
// script : "<full text of the SLURM script>",
// format : "html" // or "pdf"
// }
// ─────────────────────────────────────────────────────────────────────────────
export const meta = {
name: 'slurm-explainer',
description: 'Validate a Nanopore/SLURM script and output a styled HTML or PDF-ready report for new analysts',
phases: [
{ title: 'Analyse', detail: 'Validate SLURM resources, Dorado model, RNA/DNA settings, modkit, samtools' },
{ title: 'Report', detail: 'Render findings as HTML artifact or PDF-ready markdown' },
],
}
// ─── Input ───────────────────────────────────────────────────────────────────
const script = args?.script || ''
const format = args?.format || 'html' // 'html' or 'pdf'
if (!script.trim()) {
log('No script provided — pass the SLURM script text as args.script')
return { error: 'No script provided.' }
}
log(`Analysing script · output format: ${format.toUpperCase()}`)
// ─── Schema for Phase 1 output ───────────────────────────────────────────────
// Using a strict schema forces the agent to return clean JSON that Phase 2
// can render reliably, without needing to parse free-form text.
const ANALYSIS_SCHEMA = {
type: 'object',
required: ['summary', 'dataType', 'slurmResources', 'tools', 'findings', 'correctedScript'],
properties: {
// Plain-English job summary (2-3 sentences)
summary: { type: 'string' },
// Whether this is a DNA or RNA job — critical for validation
dataType: { type: 'string', enum: ['DNA', 'RNA', 'unknown'] },
// Key SLURM directives only (time, mem, cpus, gpu, partition)
slurmResources: {
type: 'array',
items: {
type: 'object',
required: ['directive', 'value', 'meaning'],
properties: {
directive: { type: 'string' },
value: { type: 'string' },
meaning: { type: 'string' },
},
},
},
// Every tool found in the script (dorado, modkit, minimap2, samtools, etc.)
tools: {
type: 'array',
items: {
type: 'object',
required: ['toolName', 'subcommand', 'whatItDoes', 'flags'],
properties: {
toolName: { type: 'string' },
subcommand: { type: 'string' },
whatItDoes: { type: 'string' },
flags: {
type: 'array',
items: {
type: 'object',
required: ['flag', 'value', 'meaning'],
properties: {
flag: { type: 'string' },
value: { type: 'string' },
meaning: { type: 'string' },
},
},
},
},
},
},
// Validation findings — ERRORs first, then WARNINGs, then INFO
findings: {
type: 'array',
items: {
type: 'object',
required: ['severity', 'location', 'title', 'explanation', 'fix'],
properties: {
severity: { type: 'string', enum: ['ERROR', 'WARNING', 'INFO'] },
location: { type: 'string' }, // e.g. "line 12" or "general"
title: { type: 'string' },
explanation: { type: 'string' },
fix: { type: 'string' }, // how to fix it
},
},
},
// Full corrected script with # CHANGED / # ADDED comments.
// Empty string if the script is already clean.
correctedScript: { type: 'string' },
},
}
// ─── Phase 1: Analyse ────────────────────────────────────────────────────────
phase('Analyse')
const analysis = await agent(
`You are a bioinformatics HPC mentor specialising in Oxford Nanopore Technology (ONT).
Analyse the SLURM batch script below for a new analyst who knows biology but is new to HPC.
CHECK THESE IN ORDER (most critical first):
	1	RNA vs DNA correctness
	◦	DNA model (name starts with "dna_") used on RNA data → ERROR
	◦	RNA model (name starts with "rna_") used on DNA data → ERROR
	◦	dorado duplex on RNA data → ERROR (duplex is DNA-only)
	◦	minimap2 -ax map-ont on direct RNA reads → ERROR (must be -ax splice -uf -k14)
	◦	--modified-bases 5mCG/5hmCG on RNA → ERROR (RNA needs m6A or m6A_DRACH)
	◦	-uf missing from direct RNA minimap2 command → WARNING
	2	Dorado model selection
	◦	Valid patterns: dna_r10.4.1_e8.2_400bps_{fast,hac,sup}@v{ver} rna002_70bps_{fast,hac,sup}@v{ver}  rna004_130bps_{fast,hac,sup}@v{ver} 
	◦	"fast" accuracy → WARNING (hac or sup recommended)
	◦	version not pinned (@v...) → WARNING
	3	modkit checks
	◦	modkit pileup on BAM without --modified-bases in Dorado → ERROR (no MM/ML tags)
	◦	--combine-strands on RNA → ERROR (m6A is not strand-symmetric)
	◦	--ref missing from modkit pileup → WARNING
	◦	--mod-thresholds not set → WARNING
	◦	--cpg filter on RNA data → INFO
	4	SLURM resources
	◦	Dorado present but --gres=gpu absent → ERROR
	◦	--mem not set → WARNING
	◦	set -euo pipefail missing → WARNING
	◦	module load without pinned version → WARNING
	◦	--cpus-per-task not passed to samtools sort -@ → INFO
For the correctedScript: if any ERROR or WARNING found, return the full fixed script
with a # CHANGED: or # ADDED: comment on every modified line. If clean, return "".
Script to analyse:
```bash
${script}
````,
{
label: 'analyse:script',
phase: 'Analyse',
schema: ANALYSIS_SCHEMA,
}
)
if (!analysis) {
log('Analysis agent returned no result — aborting')
return { error: 'Analysis failed.' }
}
// Quick summary log so the user can see findings while Phase 2 starts
const errorCount = analysis.findings.filter(f => f.severity === 'ERROR').length
const warningCount = analysis.findings.filter(f => f.severity === 'WARNING').length
const infoCount = analysis.findings.filter(f => f.severity === 'INFO').length
log(`Found ${errorCount} error(s), ${warningCount} warning(s), ${infoCount} info item(s) · data type: ${analysis.dataType}`)
// ─── Phase 2: Report ─────────────────────────────────────────────────────────
phase('Report')
if (format === 'html') {
// HTML path — publish a styled Artifact the user can share
await agent(
`You are creating a professional HTML report for a new bioinformatics analyst.
Publish an HTML Artifact using the Artifact tool. Design rules:
	◦	Clean white background, readable sans-serif font, max-width 900px centred
	◦	Severity badges: ERROR = solid red, WARNING = solid orange, INFO = solid blue (white text)
	◦	Summary banner at the top: data type pill (green=DNA, purple=RNA), error/warning/info counts
	◦	SLURM resources in a compact two-column table
	◦	Each tool in its own card with a grey header; flags in a striped table
	◦	Findings sorted ERROR → WARNING → INFO; each finding shows badge, title, explanation, and fix
	◦	If correctedScript is non-empty, show it in a <pre> block with lines containing "# CHANGED:" or "# ADDED:" highlighted in pale yellow 
	◦	Fully responsive (works on mobile); no external libraries — inline CSS and vanilla JS only
	◦	Page <title> should be "Script Report — [job name if found, else SLURM Analysis]"
Here is the analysis data (JSON):
${JSON.stringify(analysis, null, 2)}
Publish this as an HTML Artifact now.`,
{ label: 'render:html', phase: 'Report' }
)
} else {
// PDF path — output clean markdown the user can export with pandoc or print
await agent(
`You are creating a PDF-ready report for a new bioinformatics analyst.
Output the full report as clean Markdown (no HTML tags).
Use this exact structure:
---
title: "SLURM Script Analysis Report"
date: "[today's date]"
---
## Summary
Data type: DNA / RNA Errors: N Warnings: N Info: N
[2-3 sentence plain-English summary of what the job does]
## SLURM Resources
| Directive | Value | What it means |
|-----------|-------|---------------|
[one row per SLURM directive]
## Tool Breakdown
[For each tool:]
### tool subcommand
[one sentence: what this step does]
| Flag | Value | What it does |
|------|-------|--------------|
## Validation Findings
### Errors
[For each ERROR:]
[ERROR] location — title
> explanation
> Fix: how to fix it
### Warnings
[same format]
### Info
[same format]
## Corrected Script
[Only include this section if correctedScript is non-empty]
```bash
[correctedScript]
```
Keep language plain — define any technical term the first time it appears.
Analysis data:
${JSON.stringify(analysis, null, 2)}`,
{ label: 'render:pdf-markdown', phase: 'Report' }
)
}
// ─── Return summary ───────────────────────────────────────────────────────────
return {
format,
dataType: analysis.dataType,
errors: errorCount,
warnings: warningCount,
info: infoCount,
clean: errorCount === 0 && warningCount === 0,
}
