# NanoCortex Skill — Claude Code

## Install

```bash
# personal
mkdir -p ~/.claude/skills
cp -R claude-code ~/.claude/skills/nanocortex

# or project-local
mkdir -p .claude/skills
cp -R claude-code .claude/skills/nanocortex
```

## Run

1. `cd` to the NanoCortex repository root.
2. Approve Bash and file-access permissions when prompted.
3. Ask Claude Code to use the NanoCortex skill.

## Claude Code-specific notes

- Uses the Bash tool for Singularity execution.
- Requests permissions step by step instead of blanket auto-approve.
- Returns a concise execution log with exit codes and output paths.

## Verify

```bash
python3 ~/.claude/skills/nanocortex/scripts/query_parameters.py dorado --list
singularity exec singularity/bot.sif dorado --version
```
