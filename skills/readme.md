# NanoCortex On-Shelf Skills

Platform-specific NanoCortex skill packages for agentic frameworks evaluated in the manuscript.

| Directory | Platform | Install target |
|-----------|----------|----------------|
| `codex/` | OpenAI Codex | `$CODEX_HOME/skills/nanocortex` |
| `cursor/` | Cursor | `~/.cursor/skills/nanocortex` |
| `claude-code/` | Claude Code | `~/.claude/skills/nanocortex` |
| `gemini/` | Gemini ADK | ADK instruction context + `agents/` |

Each directory is self-contained. Shared scientific content is duplicated intentionally so every platform receives an adapted install bundle rather than a generic wrapper.

## Shared workflows

- modification analysis
- transcript isoform analysis
- RNA secondary-structure prediction
- regional POD5/BAM signal plotting

## Platform differences

- **Codex**: HPC/Slurm shell execution, `agents/openai.yaml`, Auto-approve permissions
- **Cursor**: explicit `@nanocortex` invocation, workspace-aware paths, `disable-model-invocation: true`
- **Claude Code**: Bash-tool execution, stepwise permission approval
- **Gemini**: ADK agent graph, `agents/signal_agent.py`, Always Allow permissions

See each subdirectory `README.md` for installation and verification steps.
