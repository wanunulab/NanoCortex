# NanoCortex Skill — Cursor

## Install

```bash
# personal
mkdir -p ~/.cursor/skills
cp -R cursor ~/.cursor/skills/nanocortex

# or project-local
mkdir -p .cursor/skills
cp -R cursor .cursor/skills/nanocortex
```

## Run

1. Open the NanoCortex repository in Cursor.
2. Invoke explicitly with `@nanocortex`.
3. Run Singularity commands in the integrated terminal.

## Cursor-specific notes

- `disable-model-invocation: true` — the skill loads only when named.
- Prefer workspace-relative paths when the NanoCortex repo is open.
- Do not recursively search the repository; follow one reference file per task.

## Verify

```bash
python3 ~/.cursor/skills/nanocortex/scripts/query_parameters.py dorado --list
singularity exec singularity/bot.sif dorado --version
```
