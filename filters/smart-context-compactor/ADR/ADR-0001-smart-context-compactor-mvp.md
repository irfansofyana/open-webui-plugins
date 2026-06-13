# ADR-0001: Build a Lean Smart Context Compactor MVP

## Status

Accepted for implementation planning.

## Date

2026-06-11

## Context

Open WebUI sends the full chat payload to the selected model. Long conversations can exceed the model/provider context window and fail with errors such as `context length exceeded` or `prompt too long`.

Research showed that Open WebUI intentionally does not provide one built-in context management policy. The documented and maintainer-recommended extension point is a **Filter Function** using `inlet()` to modify `body["messages"]` before the model request.

Existing community solutions mostly implement:

- context clipping by message/turn count;
- token-based trimming;
- context/token usage meters;
- sliding-window recent-history filters.

These are useful and proven, but most of them either **drop old context** or only **warn users**. The differentiator we want is continuity: users should be able to continue a long chat and still retain important older preferences, decisions, and context.

An initial broad spec was drafted in `README.md`, then reviewed by subagents from architecture, implementation, and product/UX perspectives. All reviewers agreed the concept is valid but the full spec is too large for a first implementation.

## Decision

We will implement a **lean MVP Filter Function** first.

Positioning:

> Smart trim filter: keeps recent chat raw, optionally summarizes older context, and safely falls back to deterministic trimming.

The MVP will not attempt to be a full Claude/ChatGPT-style persistent compaction system. It will perform **payload-only compaction** per request. The visible stored chat history remains unchanged.

## MVP scope

The first implementation will include:

1. **Open WebUI Filter `inlet()`**
   - Always-on when enabled by admin/model config.
   - No user toggle in MVP.

2. **Budget trigger**
   - Estimate prompt size with a simple heuristic.
   - Trigger compaction when estimated prompt tokens exceed `context_budget_tokens * effective_budget_ratio`.

3. **Preservation policy**
   - Always preserve original system messages.
   - Never mutate the latest user message.
   - Preserve recent N user-led turns, default `12`.
   - Older turns are candidates for summary or trimming.

4. **Optional semantic summary**
   - If `summarizer_base_url`, `summarizer_api_key`, and `summarizer_model` are configured, summarize older dropped turns.
   - Inject the summary as one synthetic `system` message after original system messages.
   - Use one built-in summary prompt for v0.1.0.

5. **Deterministic trim fallback**
   - If summarizer config is missing, summarization fails, or the result still exceeds budget, fall back to trimming older turns.
   - The plugin must still be useful immediately after install as a robust trim filter.

6. **Tool-call boundary repair**
   - Avoid leaving orphan `tool` messages or assistant messages with unresolved `tool_calls`.
   - Prefer dropping old tool-call structures over sending invalid provider payloads.

7. **User notification**
   - Best-effort status toast only when compaction/fallback happens.
   - No always-visible token meter in MVP.

8. **Oversized latest message behavior**
   - If original system messages plus latest user message cannot fit, raise a clear error.
   - Do not silently summarize or truncate the active user request.

## MVP valves

Keep the first valve surface small:

| Valve | Default | Purpose |
|---|---:|---|
| `enabled` | `true` | Global kill switch. |
| `context_budget_tokens` | `8192` | Single context budget for MVP. |
| `effective_budget_ratio` | `0.75` | Prompt budget fraction before reserving headroom. |
| `keep_recent_turns` | `12` | Recent user-led turns to preserve raw. |
| `summarizer_base_url` | `""` | Optional OpenAI-compatible base URL. |
| `summarizer_api_key` | `""` | Optional API key. Required for semantic summary. |
| `summarizer_model` | `""` | Optional model for summary. Empty means semantic summary disabled in MVP. |
| `show_status` | `true` | Emit best-effort status toasts. |

## Explicitly deferred

The following remain in the broader README design draft but are **not v0.1.0 scope**:

- per-model budget JSON mapping;
- summarizer model mapping;
- summary modes (`general`, `technical`, `balanced`);
- custom summary prompt;
- preserving first/head turns separately;
- immediate-follow-up heuristics;
- browser-only/direct-API detection;
- sophisticated image/file placeholder handling;
- summary input cap with start/end slicing;
- persistent summary cache;
- manual Action button;
- always-visible token/context meter;
- detailed logging framework;
- advanced secret redaction beyond simple obvious safeguards;
- Open WebUI internal model invocation;
- rewriting visible stored chat history.

## Consequences

### Positive

- Faster path to a working plugin.
- Learns from proven community clip/token filters by making deterministic trim reliable first.
- Adds a clear differentiator over clip filters when semantic summary is configured.
- Avoids fragile Open WebUI internals.
- Keeps setup understandable.

### Negative

- Not truly Claude/ChatGPT-style persistent compaction yet.
- Visible chat history remains full and unchanged.
- Without semantic summarizer config, behavior is closer to a token trim filter.
- Stateless design may re-compact similar history on later requests.
- Single global context budget is less precise for mixed-model deployments.

## Implementation notes

- Use the existing `filters/caveman/` plugin as local structure/style reference.
- Required Open WebUI target: `>= 0.9.2`.
- Recommend Open WebUI `>= 0.9.6` for better built-in recovery of stored broken tool-call pairs.
- Avoid mandatory third-party dependencies in v0.1.0.
- Summarizer HTTP call should be simple, non-streaming, and timeout-bound.
- Status event emission must be best-effort and must never fail the request.
- Server logs should avoid raw chat content and secrets.

## Validation criteria

MVP is successful when:

1. Short chats under budget pass through unchanged.
2. Long chats over budget continue without provider context errors.
3. With semantic summary configured, an early user preference survives compaction and can be recalled later.
4. With semantic summary missing/failing, deterministic trim still lets the chat continue.
5. Latest user message is never silently altered.
6. Tool-call trimming does not produce provider-invalid orphan tool messages.

## Follow-up

After v0.1.0 is implemented and manually tested in Open WebUI, clean up `README.md` into user-facing install/setup documentation and move broader roadmap material into future ADRs or a roadmap section.
