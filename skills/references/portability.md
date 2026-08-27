# Backend portability

## Portable contract

NanoCortex requires reasoning plus optional capabilities, not a named model SDK. A backend may use its native equivalents for:

- reading and writing workspace files;
- running terminal commands with user-visible safety controls;
- browsing current documentation and scientific literature;
- retaining confirmed variables during a task;
- returning commands, tables, figures, and cited interpretations.

The skill must not import or call Google ADK, Gemini, OpenAI, Anthropic, or another model API. Provider-specific wrappers may load this skill, but they must remain outside the skill's core workflow.

## Adaptation checklist

1. Place the `nanocortex` directory in the platform's supported skill/instruction location.
2. Preserve `SKILL.md`, `references/`, `scripts/`, and `assets/` together.
3. Map file, shell, search, and approval operations to the platform's native tools.
4. Confirm Python 3 is available for parameter lookup; no third-party Python package is required by the lookup script.
5. Run the same benchmark prompts and scoring rubric on every backend.
6. Record backend, model name/version, date, temperature or reasoning settings when exposed, repetitions, latency, and cost.

## Capability fallbacks

- Without terminal access, generate and validate commands but label them unexecuted.
- Without web access, use bundled parameter data and flag claims that require current documentation or literature verification.
- Without local bioinformatics tools, produce a reproducible plan and dependency list rather than claiming completion.
- Without persistent conversation state, restate confirmed parameters in a compact working record before the next action.
