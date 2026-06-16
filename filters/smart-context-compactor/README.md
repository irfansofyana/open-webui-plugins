# Smart Context Compactor Filter

> Keeps long Open WebUI chats usable by trimming older context — and, when configured, summarizing older turns before they are dropped.

**Type:** Filter Function  
**Author:** [@irfansofyana](https://github.com/irfansofyana)  
**Version:** 0.2.0  
**License:** MIT  
**Required Open WebUI:** `>= 0.9.2`  
**Recommended Open WebUI:** `>= 0.9.6` for stronger built-in tool-call recovery  
**Source:** [smart-context-compactor.py](smart-context-compactor.py)  
**ADRs:** [ADR-0001](ADR/ADR-0001-smart-context-compactor-mvp.md), [ADR-0002](ADR/ADR-0002-low-risk-fujie-lessons.md)

---

## What it does

Open WebUI sends chat history to the selected model on every request. Long chats can eventually exceed the model/provider context window and fail with errors like `context length exceeded`, `prompt too long`, or `input is too long`.

This filter runs in `inlet()` before the model request. When the estimated prompt exceeds the configured budget, it:

1. resolves the model's context budget using `model_budgets_json` or fallback `context_budget_tokens`;
2. preserves system messages;
3. preserves the latest user message unchanged;
4. preserves the first user-led turns and most recent user-led turns;
5. optionally summarizes older middle turns using a configured OpenAI-compatible endpoint;
6. otherwise trims older middle turns deterministically;
7. repairs obvious tool-call boundary issues;
8. emits a status toast so the user knows compaction happened.

This is **payload-only compaction**. It changes what is sent to the model, not the visible stored chat history.

---

## Prior art

Most existing Open WebUI context-management filters are context clippers, token trimmers, sliding-window filters, token meters, or full persistent context systems such as Fu-Jie's Async Context Compression.

Smart Context Compactor intentionally stays lightweight and avoids Open WebUI internals like DB tables or internal model calls. It keeps reliable trim behavior as fallback, then adds optional semantic summary so important older preferences, facts, decisions, and unresolved threads can survive compaction better than plain clipping.

---

## Install

1. Open WebUI → **Workspace** → **Functions** → **+ New Function**.
2. Paste the contents of [smart-context-compactor.py](smart-context-compactor.py).
3. Save the function.
4. Enable it globally or attach it to specific models in **Admin Panel → Functions / Model Settings**.

The filter is always-on when enabled by admin/model config. It does not create a user toggle chip in v0.2.0.

---

## Usage

### Default: trim mode

The filter works immediately after install with no external summarizer configured.

When a chat exceeds the effective budget, older middle turns are trimmed and the user sees a status like:

> Semantic summary not configured; trimmed older context (~42000 → ~13000 tokens).

This mode behaves like a robust token/turn clip filter, while still preserving first and recent turns when the budget allows.

### Optional: semantic summary mode

To preserve older context better, configure all three summarizer valves:

- `summarizer_base_url`
- `summarizer_api_key`
- `summarizer_model`

The endpoint must be OpenAI-compatible and support `POST /chat/completions`.

Example:

| Valve | Example |
|---|---|
| `summarizer_base_url` | `https://api.openai.com/v1` |
| `summarizer_api_key` | `sk-...` |
| `summarizer_model` | `gpt-4o-mini` |

When semantic summary succeeds, the user sees:

> Compacted chat context: ~42000 → ~13000 tokens.

If the summarizer call fails or times out, the filter falls back to trimming and notifies the user.

---

## How compaction works

```text
Incoming Open WebUI request
        ↓
Resolve model-specific context budget
        ↓
Estimate body["messages"] tokens
        ↓
If under budget: return unchanged
        ↓
Preserve system + latest user + first turns + recent turns
        ↓
If summarizer configured: summarize middle turns, capped by summary_input_budget_ratio
If not configured/fails: trim middle turns
        ↓
Inject optional summary as system message
        ↓
Repair tool-call boundaries
        ↓
Final fit pass
        ↓
Return compacted request body
```

A **turn** means a user message plus following assistant/tool messages until the next user message.

---

## Configuration

### Admin valves

| Field | Default | Description |
|---|---:|---|
| `enabled` | `true` | Global kill switch. |
| `context_budget_tokens` | `8192` | Fallback context budget when no model mapping matches. |
| `model_budgets_json` | `{}` | JSON mapping of Open WebUI model IDs or prefixes to context budgets. Exact match wins, then longest prefix, then `default`, then fallback budget. |
| `effective_budget_ratio` | `0.75` | Fraction of resolved context budget allowed for prompt before reserving response/headroom. |
| `keep_first_turns` | `1` | Initial user-led turns to preserve verbatim when compaction triggers. Set `0` to disable. |
| `keep_recent_turns` | `12` | Recent user-led turns to preserve verbatim when compaction triggers. |
| `summary_input_budget_ratio` | `0.50` | Maximum summarizer transcript size as a ratio of the resolved model context budget. |
| `summarizer_base_url` | `""` | Optional OpenAI-compatible base URL, e.g. `https://api.openai.com/v1`. Empty disables semantic summary. |
| `summarizer_api_key` | `""` | API key for summarizer endpoint. Required for semantic summary. |
| `summarizer_model` | `""` | Model ID for semantic summaries. Empty disables semantic summary. |
| `show_status` | `true` | Emit best-effort status toasts when compaction happens. |

### User valves

None in v0.2.0.

---

## Model budgets

Use `model_budgets_json` when your Open WebUI instance has multiple models with different context windows.

Example:

```json
{
  "default": 8192,
  "gpt-4o-mini": 128000,
  "openai.gpt-4o": 128000,
  "ollama.llama3.1:8b": 8192,
  "qwen2.5": 32768
}
```

Resolution order:

1. exact `body["model"]` match;
2. longest prefix match;
3. `default` entry;
4. `context_budget_tokens`.

Effective prompt budget:

```text
resolved_context_budget × effective_budget_ratio
```

With defaults:

```text
8192 × 0.75 = ~6144 prompt tokens
```

The remaining budget is intentionally reserved for model response, RAG additions, tool definitions, and provider/tokenizer estimation error.

---

## Token estimation

The filter uses `tiktoken` if it is already available in the Open WebUI environment. If `tiktoken` is missing or fails to load, it falls back to a simple character-based heuristic.

`tiktoken` is optional; this plugin does not require extra dependencies.

---

## Summary input cap

Very long chats can make the summary request itself too large. Before calling the summarizer, the filter caps the old middle-history transcript using:

```text
resolved_context_budget × summary_input_budget_ratio
```

If the transcript exceeds that cap, the filter keeps the start and end of the middle history and inserts an omission marker before summarization.

---

## Safety behavior

### Latest user message is never silently changed

If the latest user message plus system prompt is too large to fit the effective budget, the filter raises a clear error instead of summarizing or truncating the active request.

### Tool-call repair

The filter drops obvious invalid tool-call fragments before sending the compacted payload, including:

- orphan `tool` messages;
- assistant messages with `tool_calls` whose matching tool results are missing;
- malformed assistant tool-call structures.

This favors provider-valid payloads over preserving old tool details.

### Summarizer privacy

If semantic summary is configured, older chat content is sent to the configured summarizer endpoint. Use a trusted/local endpoint for sensitive chats.

The built-in summary prompt asks the summarizer to redact obvious secrets as `[REDACTED_SECRET]`, but this is not a substitute for a dedicated PII/secrets redaction filter.

---

## Notes and caveats

- Payload-only: visible chat history is not rewritten.
- Stateless: the filter may compact similar history again on later requests.
- No summary modes/custom prompts yet.
- No persistent cache yet.
- No manual “Compact now” action yet.
- No always-visible token meter.
- No required third-party dependencies.
- Semantic summary uses a non-streaming HTTP request with a fixed 15-second timeout.
- Recommended Open WebUI `>= 0.9.6` for stronger built-in recovery of already-broken stored tool-call pairs.

---

## Manual validation

Open WebUI plugins require testing in a running Open WebUI instance. Local syntax checks are not enough to claim the plugin works operationally.

Please validate:

1. **No-op under budget** — short chats pass through normally.
2. **Model budget mapping** — the same test chat compacts differently for small vs large mapped model budgets.
3. **Trim fallback** — leave summarizer valves empty, exceed budget, confirm older context is trimmed and status appears.
4. **First-turn preservation** — set `keep_first_turns=1`, exceed budget, confirm initial preference/framing survives when budget allows.
5. **Semantic summary** — configure summarizer valves, exceed budget, confirm a later question can recall an early preference/decision.
6. **Summarizer failure** — configure an invalid endpoint/key and confirm fallback trim still lets chat continue.
7. **Huge latest message** — send a latest message too large for budget and confirm a clear error is shown.
8. **Tool-heavy chat** — confirm compaction does not produce provider errors from orphan tool calls/results.

---

## Roadmap

Deferred:

- summarizer model mapping;
- summary modes (`general`, `technical`, `balanced`);
- custom summary prompt;
- persistent summary cache;
- async `outlet()` background summarization;
- manual toolbar Action;
- visible token meter;
- stored-chat rewriting / true persistent compaction.
