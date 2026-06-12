# Stop Slop Filter

> Removes predictable AI writing patterns from prose in Open WebUI.

**Type:** Filter Function
**Author:** [@irfansofyana](https://github.com/irfansofyana)
**Version:** 1.0.0
**License:** MIT
**Required Open WebUI:** `>= 0.9.0`
**Source:** [stop-slop.py](stop-slop.py)

> **Credits:** Derived from Hardik Pandya's [stop-slop](https://github.com/hardikpandya/stop-slop), originally released under the MIT License. This Open WebUI filter ports the upstream Stop Slop rule set into a self-contained Function, with small assistant-safety adaptations and optional Open WebUI output audit.

---

## Skill or Filter?

Use the **Skill** when you want a plain Markdown instruction set that users can invoke with `$`, enable from **+ → Skills**, or attach to a model. It is passive: no output audit, no event status, no admin valves.

Use this **Filter** when you want Open WebUI Function behavior: per-chat chip visibility, admin valves, prompt injection, and optional output audit/status.

Do not enable both for the same chat/model unless you intentionally want duplicate Stop Slop instructions.

---

## What it does

Injects Stop Slop writing rules into the model request so the LLM avoids common AI-writing tells:

- throat-clearing openers like “Here’s the thing”;
- emphasis crutches like “Let that sink in”;
- business jargon like “navigate”, “unpack”, “lean into”;
- adverbs, softeners, and vague declaratives;
- binary contrast formulas like “Not X. But Y.”;
- passive voice and false agency;
- punchy one-liners, em dashes, and formulaic rhythm.

The filter can also audit final assistant output for obvious slop patterns. By default, it **does not rewrite** the final answer and **does not emit visible audit warnings**; enable `emit_audit_status` or `append_audit_note` if you want visible audit feedback.

---

## Install

1. Open WebUI → **Workspace** → **Functions** → **+ New Function**.
2. Paste the contents of [stop-slop.py](stop-slop.py).
3. Save the function.
4. In Function settings, enable the Function and either:
   - make it globally available, or
   - attach it only to selected models.
5. This filter sets `self.toggle = True`, so Open WebUI exposes a **Stop Slop** chip / Integrations entry. Users enable that chip per chat when they want the filter to run.

---

## Usage

### Toggle per chat

Click the **Stop Slop** chip in the chat input, or enable it from **+ → Integrations**.

The model infers whether to draft, edit, or review from the user's request. There are no custom filter commands, modes, or strictness levels.

---

## Configuration

### Admin valves

| Field | Default | Description |
|---|---:|---|
| `priority` | `0` | Filter execution order. Lower runs first. |
| `enabled` | `true` | Internal kill switch for this filter. Separate from Open WebUI's Function enabled/global/model attachment settings. |
| `include_examples` | `true` | Include before/after examples in the injected prompt. |
| `include_scoring` | `true` | Include the 50-point scoring checklist. |
| `audit_output` | `true` | Scan final assistant output for common slop patterns. Does not rewrite content by itself. |
| `emit_audit_status` | `false` | Emit visible status warning when audit finds patterns. Disabled by default to avoid noisy false positives. |
| `append_audit_note` | `false` | Append audit findings to the assistant response. Mutates output. |
| `max_audit_findings` | `5` | Maximum findings reported by the audit. |

No user valves are defined. Users control the filter with the Open WebUI chip / Integrations menu.

---

## Notes / caveats

- This is a prompt-driven filter. The model still has to follow the instruction.
- The outlet audit is heuristic. It catches obvious patterns but cannot prove prose is human.
- `outlet()` audit behavior is mainly for Open WebUI chat/completed flows. Direct `/api/chat/completions` callers may not see audit status or appended notes unless they also trigger Open WebUI's completion hooks.
- `append_audit_note = false` by default because mutating final answers can be intrusive.
- Keep `self.toggle = True` for visibility. If you remove it, the filter runs whenever it is globally enabled or attached to a model.
- Open WebUI Skills are a better fit when users want plain-text instructions. This filter is better when users want Caveman-like chat-chip control and optional audit behavior.
- The “Open WebUI Adaptation Boundaries” section in the injected prompt is local adaptation, not upstream Stop Slop source text.

---

## License and attribution

This implementation is MIT licensed as part of this repository.

It includes substantial rule content derived from Hardik Pandya's [stop-slop](https://github.com/hardikpandya/stop-slop), MIT License, Copyright (c) 2025 Hardik Pandya.

Original upstream MIT notice:

```text
MIT License
Copyright (c) 2025 Hardik Pandya

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
