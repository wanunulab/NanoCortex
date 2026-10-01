# NanoCortex: LLM API costs

## Expenditure for the original study

During the study period, we used Google’s LLM services on a **pay-as-you-go basis**. Although the resulting expenditure may not directly reflect costs under current pricing or alternative billing arrangements, we report it here as a historical reference.

Approximately **US$300** was spent on Google-provided LLM services accessed through the Gemini ADK-based framework between **December 2025 and June 2026**. This covered platform development, setup and testing, the benchmarks and analyses presented in the original manuscript, and the generation of code and figures. Additional analyses conducted in response to reviewer comments are excluded.

This total represents study-wide development and analysis expenditure, not the cost of an individual workflow. Per-task token usage and costs are not reported here. Gemini ADK is the framework used to access the services; the expenditure refers to LLM service usage.

## API pricing reference

**Pricing reference date: 30 September 2026.** All prices below are in **USD per million tokens**.

**Verification status:** Model names, rate qualifiers and prices in this table were supplied by the authors and have not yet been independently checked against dated official pricing sources. This table is a draft pending that verification.

| Provider / platform (as supplied) | Model | Input | Output |
| --- | --- | ---: | ---: |
| Claude | Haiku 4.5 | 1.00 | 5.00 |
| Claude | Sonnet 5 / 5.5 | 2.00 | 10.00 |
| Claude | Opus 5.5 | 4.00 | 20.00 |
| Claude | Fable 5.1 | 10.00 | 50.00 |
| Gemini | 3.8 Flash (intro) | 0.75 | 3.75 |
| Gemini | 3.1 Pro (≤200k) | 2.00 | 12.00 |
| Grok | 4.6 (<200k) | 2.00 | 6.00 |
| Grok | 4.3 (<200k) | 1.25 | 2.50 |
| Grok | build-0.1 | 1.00 | 2.00 |
| Codex | gpt-5-codex | 1.25 | 10.00 |
| Codex | gpt-5.3-codex | 1.75 | 14.00 |

These rates are a dated pricing reference and were not used to reconstruct the December 2025–June 2026 expenditure. Actual charges depend on the provider, model, usage date, token volume and applicable pricing conditions, including caching, batch discounts and additional service charges.

For standard input/output token billing, an approximate cost is:

```text
Cost (USD) = (input tokens × input price + output tokens × output price) / 1,000,000
```

Apply the appropriate rates separately where providers use additional billing categories. Refer to provider billing records for actual expenditure.

This page is intended to be updated as model availability and pricing change. Each update should retain an explicit pricing reference date and record the official sources used for verification.
