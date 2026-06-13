# ADR-0002: Adopt Low-Risk Lessons from Fu-Jie Async Context Compression

## Status

Accepted for implementation.

## Date

2026-06-11

## Context

After implementing the lean Smart Context Compactor MVP, we researched Fu-Jie's **Async Context Compression** filter for Open WebUI. Fu-Jie's plugin has similar goals: reduce token consumption in long conversations while preserving coherence through summarization and compression.

Fu-Jie's design is significantly more mature and broader than our MVP. It includes asynchronous `outlet()` summary generation, persistent `chat_summary` database storage, per-chat locks, Open WebUI internal model invocation, per-model thresholds, compression styles, token usage status, i18n, tool output trimming, and detailed debug surfaces.

Those features are valuable, but many depend on Open WebUI internals such as database modules, chat models, user/model APIs, and internal generation helpers. We want to avoid brittle compatibility issues when Open WebUI upgrades.

## Decision

We will adopt only low-risk, payload-local improvements that do **not** require Open WebUI DB access, internal model invocation, stored chat rewriting, or `outlet()` background lifecycle.

This will become the next implementation increment after v0.1.0. Because this adds new non-breaking functionality and valves, the plugin version should move to `0.2.0`.

## Accepted improvements

### 1. Per-model budget mapping

Add a valve allowing admins to map Open WebUI model IDs or prefixes to context budgets.

Example:

```json
{
  "gpt-4o-mini": 128000,
  "llama3.1:8b": 8192,
  "qwen2.5": 32768
}
```

Resolution policy:

1. exact `body["model"]` match;
2. longest prefix match;
3. fallback to `context_budget_tokens`.

Reason: mixed-model Open WebUI deployments are common; one global context budget compacts large-context models too early or small-context models too late.

### 2. Keep-first turns

Add `keep_first_turns`, default `1`.

Final payload shape should be:

```text
original system messages
optional compacted summary of middle
first N turns
recent N turns
```

Older middle turns are summarized or trimmed. Head and recent windows are deduplicated if they overlap.

Reason: early turns often contain durable user preference, role setup, project framing, or initial constraints. Fu-Jie's `keep_first` exists for this reason.

### 3. Stronger built-in summary prompt

Improve the summary prompt with explicit sections for:

- durable user preferences;
- current goal;
- decisions made;
- unresolved questions/blockers;
- key facts/files/errors/tool outcomes;
- facts to preserve verbatim.

Reason: summary quality is the differentiator over pure clipping. Better prompt structure is low-risk and does not require internals.

### 4. Optional `tiktoken`

Attempt to import `tiktoken` if available. If unavailable or encoding fails, keep the existing heuristic fallback.

Reason: Open WebUI deployments often already include `tiktoken`. Optional usage improves budget accuracy without adding a hard dependency.

### 5. Summary input cap

Add a valve to limit how much old middle history is sent to the summarizer.

Default: `summary_input_budget_ratio = 0.50`.

Behavior:

- cap transcript to `model_context_budget * summary_input_budget_ratio` estimated tokens;
- preserve the start and end of the middle transcript when truncation is needed;
- insert an explicit omission marker.

Reason: the summary request itself can exceed the summary model's context window or become too slow/costly on huge chats.

## Explicit non-goals

Still avoid for now:

- Open WebUI DB persistence;
- creating `chat_summary` table;
- importing `Chats`, `Users`, `Models`, or Open WebUI DB internals;
- internal `generate_chat_completion` calls;
- async `outlet()` background summarization;
- per-chat locks;
- frontend debug console events;
- i18n/status translation framework;
- external chat reference injection;
- stored visible chat rewriting;
- full Fu-Jie-style valve surface.

## Consequences

### Positive

- Supports multiple models with different context windows.
- Preserves initial task framing better.
- Improves semantic compaction quality.
- Reduces summary-call failures from enormous middle history.
- Improves token estimates when `tiktoken` is already present.
- Keeps plugin copy-paste friendly and upgrade-safe.

### Negative

- More valves than v0.1.0.
- Still stateless and may re-summarize similar history.
- Still blocks during inline summarization.
- Still less powerful than Fu-Jie's persistent async architecture.
- Prefix budget matching may surprise admins if model IDs overlap; longest-prefix match mitigates this.

## Validation criteria

Implementation is acceptable when local simulations prove:

1. exact model budget mapping is used over global fallback;
2. longest prefix mapping works;
3. missing/invalid mapping falls back safely to `context_budget_tokens`;
4. first turns and recent turns are both preserved when budget allows;
5. overlapping first/recent windows are deduplicated;
6. summary input cap inserts an omission marker when old middle history is too large;
7. optional `tiktoken` failure falls back to heuristic without breaking requests;
8. prior v0.1.0 validations still pass.

Manual Open WebUI validation remains required before claiming operational success.
