# NanoCortex Skill — OpenAI Codex

## Install

```bash
mkdir -p "$CODEX_HOME/skills"
cp -R codex "$CODEX_HOME/skills/nanocortex"
```

## Run

1. `cd` to the NanoCortex repository root.
2. Enable shell and filesystem access (Auto-approve).
3. Invoke with the default prompt from `agents/openai.yaml` or ask Codex to use the NanoCortex skill.

## Codex-specific notes

- Designed for Slurm-managed HPC with Singularity.
- Uses absolute paths for `SKILL_DIR`, `BOT_SIF`, and data files.
- Records command, exit code, stderr, and validation evidence for each step.

## Verify

```bash
python3 "$CODEX_HOME/skills/nanocortex/scripts/query_parameters.py" dorado --list
singularity exec singularity/bot.sif dorado --version
```
