# Caveman Filter

> Terse caveman communication mode for Open WebUI. Cuts response tokens ~65–75% while keeping full technical accuracy.

**Type:** Filter Function
**Author:** [@irfansofyana](https://github.com/irfansofyana)
**Version:** 1.1.0
**License:** MIT
**Required Open WebUI:** `>= 0.5.0`
**Source:** [caveman.py](caveman.py)

> **Credits:** Concept, prompt design, and intensity levels inspired by Julius Brussee's [caveman skill](https://github.com/JuliusBrussee/caveman). This filter is an original Open WebUI implementation by [@irfansofyana](https://github.com/irfansofyana) — consider [sponsoring Julius](https://github.com/sponsors/JuliusBrussee) for the underlying idea.

---

## What it does

Injects a system prompt on every request that instructs the LLM to drop articles, hedging, and pleasantries while preserving all technical content. The model generates terse output natively — no post-processing, no extra latency.

Result: a smart-caveman style.

> "Bug in auth middleware. Token expiry check use `<` not `<=`. Fix:"

Instead of:

> "Sure! I'd be happy to help you with that. The issue you're experiencing is likely caused by..."

---

## Intensity levels

| Level | Style |
|---|---|
| `lite` | No filler/hedging. Full sentences. Professional but tight. |
| `full` *(default)* | Drop articles, fragments OK. Classic caveman. |
| `ultra` | Abbreviated prose, arrows for causality, bare fragments. |
| `wenyan-lite` | Semi-classical Chinese register, light compression. |
| `wenyan-full` | Maximum classical Chinese terseness. Fully 文言文. |
| `wenyan-ultra` | Extreme classical Chinese compression. |

Code blocks, commit messages, and PR bodies always render in normal prose regardless of level.

---

## Install

1. Open WebUI → **Workspace** → **Functions** → **+ New Function**
2. Paste the contents of [caveman.py](caveman.py)
3. Save. The filter shows up as a toggle chip in the chat input.
4. (Optional) Admin Panel → **Functions** to enable globally or attach to specific models.

---

## Usage

### Toggle per chat
Click the **🪨 Caveman** chip in the chat input to enable/disable for the active conversation.

### Switch intensity mid-chat
Send a message that starts with `!caveman <level>`:

```
!caveman ultra
!caveman wenyan-full
!caveman          ← bare command resets to admin/user default
```

> `!` prefix (not `/`) because Open WebUI reserves `/` for prompt presets.

Per-chat overrides live in memory and reset on server restart.

### Auto-clarity (safety guard)
The filter temporarily drops compression for:
- Security warnings
- Irreversible action confirmations
- Multi-step sequences where fragment order risks misread
- Cases where compression would create technical ambiguity
- When the user asks to clarify or repeats a question

Disable in admin valves if not wanted.

---

## Configuration

### Admin valves (global)

| Field | Default | Description |
|---|---|---|
| `priority` | `0` | Filter execution order (lower runs first). |
| `enabled` | `true` | Global kill switch. |
| `intensity` | `full` | Default intensity if user has no override. |
| `auto_clarity` | `true` | Inject auto-clarity rules for safety. |

### User valves (per-user)

| Field | Default | Description |
|---|---|---|
| `intensity` | `""` | User-preferred intensity. Empty = use admin default. |

### Intensity resolution priority
1. Per-chat override (set via `!caveman <level>`)
2. User valves preference
3. Admin valves default
4. Fallback to `full`

---

## Notes

- LLM-native generation — no post-processing, no detection heuristics, no regex hacks.
- Stateless across server restarts (per-chat overrides only).
- Works with any model: behavior is prompt-driven.
