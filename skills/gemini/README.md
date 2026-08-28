# NanoCortex Skill — Gemini ADK

## Install

```bash
export NANOCORTEX_GEMINI_SKILL_DIR=/path/to/gemini
```

Load `SKILL.md`, `references/`, and `agents/` as the Gemini ADK instruction context.

## Run

1. Deploy on Linux with filesystem and shell access (Always Allow).
2. `cd` to the NanoCortex repository root.
3. Route signal-plot tasks through `agents/signal_agent.py` when using the native ADK graph.

## Gemini-specific notes

- Includes `agents/signal_agent.py` for the original Google ADK workflow.
- `signal_agent.py` requires `google.adk` and the project's ADK execution module.
- For portable execution outside ADK, use `scripts/signal/signal_function.py` through Singularity.

## Verify

```bash
python3 "$NANOCORTEX_GEMINI_SKILL_DIR/scripts/query_parameters.py" dorado --list
singularity exec singularity/bot.sif dorado --version
```
