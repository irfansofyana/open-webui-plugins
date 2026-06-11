"""
title: Smart Context Compactor
author: irfansofyana
author_url: https://github.com/irfansofyana
version: 0.2.0
required_open_webui_version: 0.9.2
license: MIT
description: Keeps long Open WebUI chats usable by trimming or summarizing older context before model requests exceed the context window.
"""

import asyncio
import json
import re
import time
import urllib.error
import urllib.request
from copy import deepcopy
from typing import Any, Callable, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

try:
    import tiktoken
except Exception:  # pragma: no cover - optional dependency inside Open WebUI
    tiktoken = None


class Filter:
    """
    Smart trim filter for Open WebUI.

    MVP behavior:
    - Estimate request size before the model call.
    - If over budget, preserve system messages + recent turns + latest user message.
    - Optionally summarize older dropped turns with a configured OpenAI-compatible endpoint.
    - If summarization is unavailable or fails, fall back to deterministic trimming.
    - Repair obvious tool-call boundary issues before returning the payload.

    This is payload-only compaction: visible stored chat history is not rewritten.
    """

    COMPACTION_MARKER = "[Smart Context Compactor]"

    SUMMARY_SYSTEM_PROMPT = """You compact older chat history so the current conversation can continue.

Preserve only information that matters for future continuity. Use concise structured Markdown with these sections when applicable:
- Durable user preferences
- Current goal or task
- Decisions made
- Unresolved questions, blockers, or next steps
- Key facts, files, errors, tool outcomes, names, dates, and constraints
- Facts that must be recalled verbatim

Rules:
- Do not invent facts.
- Do not include greetings or filler.
- Prefer durable context over transient chatter.
- Preserve short critical excerpts from code/logs/errors, not full long blocks.
- Redact raw secrets, API keys, passwords, tokens, and credentials as [REDACTED_SECRET].
- Use the dominant language of the conversation.
- If older context conflicts with preserved recent messages, the recent messages win.
"""

    class Valves(BaseModel):
        enabled: bool = Field(
            default=True,
            description="Enable automatic context compaction.",
        )
        context_budget_tokens: int = Field(
            default=8192,
            description="Fallback context budget when model_budgets_json has no match.",
        )
        model_budgets_json: str = Field(
            default="{}",
            description="JSON mapping of Open WebUI model IDs or prefixes to context budgets. Longest prefix wins after exact match.",
        )
        effective_budget_ratio: float = Field(
            default=0.75,
            description="Fraction of context budget allowed for the prompt before reserving response/headroom.",
        )
        keep_first_turns: int = Field(
            default=1,
            description="Initial user-led turns to preserve verbatim when compaction triggers.",
        )
        keep_recent_turns: int = Field(
            default=12,
            description="Recent user-led turns to preserve verbatim when compaction triggers.",
        )
        summary_input_budget_ratio: float = Field(
            default=0.50,
            description="Maximum summarizer transcript size as a ratio of the resolved model context budget.",
        )
        summarizer_base_url: str = Field(
            default="",
            description="Optional OpenAI-compatible base URL, e.g. https://api.openai.com/v1. Empty disables semantic summary.",
        )
        summarizer_api_key: str = Field(
            default="",
            description="API key for the summarizer endpoint. Required for semantic summary.",
        )
        summarizer_model: str = Field(
            default="",
            description="Model ID for semantic summaries. Empty disables semantic summary in v0.1.",
        )
        show_status: bool = Field(
            default=True,
            description="Emit best-effort status toasts when compaction happens.",
        )

    def __init__(self):
        self.valves = self.Valves()
        self._encoder = None
        if tiktoken is not None:
            try:
                self._encoder = tiktoken.get_encoding("cl100k_base")
            except Exception:
                self._encoder = None

    # ── Token estimation ────────────────────────────────────────────────

    def _context_budget_for_model(self, model_id: str = "") -> int:
        fallback = max(1, int(self.valves.context_budget_tokens or 8192))
        try:
            budgets = json.loads(self.valves.model_budgets_json or "{}")
            if not isinstance(budgets, dict):
                return fallback
        except Exception:
            return fallback

        model_id = model_id or ""
        if model_id in budgets:
            try:
                return max(1, int(budgets[model_id]))
            except Exception:
                return fallback

        if "default" in budgets:
            try:
                fallback = max(1, int(budgets["default"]))
            except Exception:
                pass

        best_key = ""
        best_value = None
        for key, value in budgets.items():
            if not isinstance(key, str):
                continue
            if model_id.startswith(key) and len(key) > len(best_key):
                best_key = key
                best_value = value

        if best_value is not None:
            try:
                return max(1, int(best_value))
            except Exception:
                return fallback
        return fallback

    def _effective_budget(self, model_id: str = "") -> int:
        ratio = min(max(float(self.valves.effective_budget_ratio), 0.1), 1.0)
        return max(1, int(self._context_budget_for_model(model_id) * ratio))

    def _estimate_text_tokens(self, text: str) -> int:
        if not text:
            return 0
        if self._encoder is not None:
            try:
                return len(self._encoder.encode(text, disallowed_special=()))
            except Exception:
                pass
        # Dependency-free heuristic fallback. Slightly conservative floor.
        return max(1, (len(text) + 3) // 4)

    def _estimate_content_tokens(self, content: Any) -> int:
        if content is None:
            return 0
        if isinstance(content, str):
            return self._estimate_text_tokens(content)
        if isinstance(content, list):
            total = 0
            for part in content:
                if isinstance(part, dict):
                    if "text" in part:
                        total += self._estimate_text_tokens(str(part.get("text") or ""))
                    elif part.get("type") == "image_url" or "image_url" in part:
                        # MVP only needs rough accounting for multimodal payloads.
                        total += 256
                    else:
                        total += self._estimate_text_tokens(json.dumps(part, ensure_ascii=False))
                else:
                    total += self._estimate_text_tokens(str(part))
            return total
        return self._estimate_text_tokens(str(content))

    def _message_tokens(self, message: Dict[str, Any]) -> int:
        tokens = 4  # small role/format overhead
        tokens += self._estimate_content_tokens(message.get("content"))
        if message.get("tool_calls"):
            tokens += self._estimate_text_tokens(
                json.dumps(message.get("tool_calls"), ensure_ascii=False)
            )
        if message.get("function_call"):
            tokens += self._estimate_text_tokens(
                json.dumps(message.get("function_call"), ensure_ascii=False)
            )
        if message.get("tool_call_id"):
            tokens += self._estimate_text_tokens(str(message.get("tool_call_id")))
        return tokens

    def _messages_tokens(self, messages: List[Dict[str, Any]]) -> int:
        return sum(self._message_tokens(message) for message in messages)

    # ── Message/turn helpers ────────────────────────────────────────────

    def _latest_user_message(self, messages: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        for message in reversed(messages):
            if message.get("role") == "user":
                return message
        return None

    def _split_system_messages(
        self, messages: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        system_messages = [m for m in messages if m.get("role") == "system"]
        other_messages = [m for m in messages if m.get("role") != "system"]
        return system_messages, other_messages

    def _build_turns(self, messages: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        turns: List[List[Dict[str, Any]]] = []
        current: List[Dict[str, Any]] = []

        for message in messages:
            if message.get("role") == "user" and current:
                turns.append(current)
                current = [message]
            else:
                current.append(message)

        if current:
            turns.append(current)
        return turns

    def _flatten_turns(self, turns: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        return [message for turn in turns for message in turn]

    def _is_compactor_message(self, message: Dict[str, Any]) -> bool:
        return (
            message.get("role") == "system"
            and isinstance(message.get("content"), str)
            and self.COMPACTION_MARKER in message.get("content", "")
        )

    # ── Serialization / redaction ───────────────────────────────────────

    def _redact_obvious_secrets(self, text: str) -> str:
        patterns = [
            r"(?i)(api[_-]?key|token|secret|password|passwd|pwd)\s*[:=]\s*['\"]?[^\s'\"]{8,}",
            r"sk-[A-Za-z0-9_-]{16,}",
            r"(?i)bearer\s+[A-Za-z0-9._~+/=-]{16,}",
        ]
        redacted = text
        for pattern in patterns:
            redacted = re.sub(pattern, "[REDACTED_SECRET]", redacted)
        return redacted

    def _content_to_text(self, content: Any) -> str:
        if content is None:
            return ""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: List[str] = []
            for part in content:
                if isinstance(part, dict):
                    if "text" in part:
                        parts.append(str(part.get("text") or ""))
                    elif part.get("type") == "image_url" or "image_url" in part:
                        parts.append("[image omitted]")
                    else:
                        parts.append(json.dumps(part, ensure_ascii=False))
                else:
                    parts.append(str(part))
            return "\n".join(p for p in parts if p)
        return str(content)

    def _message_to_transcript_line(self, message: Dict[str, Any]) -> str:
        role = message.get("role", "unknown")
        content = self._redact_obvious_secrets(self._content_to_text(message.get("content")))

        extras: List[str] = []
        if message.get("tool_calls"):
            extras.append(
                "tool_calls="
                + self._redact_obvious_secrets(
                    json.dumps(message.get("tool_calls"), ensure_ascii=False)
                )
            )
        if message.get("function_call"):
            extras.append(
                "function_call="
                + self._redact_obvious_secrets(
                    json.dumps(message.get("function_call"), ensure_ascii=False)
                )
            )
        if message.get("tool_call_id"):
            extras.append(f"tool_call_id={message.get('tool_call_id')}")

        suffix = f"\n  ({'; '.join(extras)})" if extras else ""
        return f"{role}: {content}{suffix}".strip()

    def _messages_to_transcript(self, messages: List[Dict[str, Any]]) -> str:
        lines = []
        for message in messages:
            if self._is_compactor_message(message):
                continue
            lines.append(self._message_to_transcript_line(message))
        return "\n\n".join(lines)

    def _cap_transcript_for_summary(self, transcript: str, context_budget: int) -> str:
        ratio = min(max(float(self.valves.summary_input_budget_ratio), 0.1), 1.0)
        token_budget = max(1, int(context_budget * ratio))
        if self._estimate_text_tokens(transcript) <= token_budget:
            return transcript

        # Keep start and end of the old middle history. This preserves durable
        # setup plus the latest pre-window context without complex chunking.
        char_budget = max(200, token_budget * 4)
        half = max(100, char_budget // 2)
        omitted_tokens = self._estimate_text_tokens(transcript[half:-half]) if len(transcript) > half * 2 else 0
        marker = (
            "\n\n[... older middle history omitted before summarization "
            f"to stay within the summary input cap; approximately {omitted_tokens} tokens omitted ...]\n\n"
        )
        return transcript[:half].rstrip() + marker + transcript[-half:].lstrip()

    # ── Status / errors ─────────────────────────────────────────────────

    async def _emit_status(
        self,
        event_emitter: Optional[Callable],
        description: str,
        done: bool = True,
    ) -> None:
        if not self.valves.show_status or event_emitter is None:
            return
        try:
            await event_emitter(
                {
                    "type": "status",
                    "data": {"description": description, "done": done, "hidden": False},
                }
            )
        except Exception:
            # Status must never break the request.
            return

    def _raise_latest_too_large(self, tokens: int, budget: int) -> None:
        raise ValueError(
            "Smart Context Compactor: latest user message plus system prompt is too large "
            f"for the configured effective budget (~{tokens} > {budget} tokens). "
            "Please split the message, shorten it, or upload large content as a document."
        )

    # ── Summarizer ──────────────────────────────────────────────────────

    def _semantic_summary_enabled(self) -> bool:
        return bool(
            self.valves.summarizer_base_url.strip()
            and self.valves.summarizer_api_key.strip()
            and self.valves.summarizer_model.strip()
        )

    def _summarizer_url(self) -> str:
        base_url = self.valves.summarizer_base_url.strip().rstrip("/")
        return f"{base_url}/chat/completions"

    def _post_summary_request_sync(self, transcript: str) -> str:
        payload = {
            "model": self.valves.summarizer_model.strip(),
            "stream": False,
            "temperature": 0,
            "max_tokens": 1200,
            "messages": [
                {"role": "system", "content": self.SUMMARY_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "Summarize this older chat history for future continuity.\n\n"
                        f"{transcript}"
                    ),
                },
            ],
        }
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self._summarizer_url(),
            data=data,
            headers={
                "Authorization": f"Bearer {self.valves.summarizer_api_key.strip()}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            body = json.loads(response.read().decode("utf-8"))

        choices = body.get("choices") or []
        if not choices:
            raise ValueError("summarizer returned no choices")
        message = choices[0].get("message") or {}
        content = message.get("content")
        if not content:
            raise ValueError("summarizer returned empty content")
        return str(content).strip()

    async def _summarize(self, messages: List[Dict[str, Any]], context_budget: int) -> str:
        transcript = self._messages_to_transcript(messages)
        transcript = self._cap_transcript_for_summary(transcript, context_budget)
        if not transcript.strip():
            raise ValueError("nothing to summarize")
        return await asyncio.to_thread(self._post_summary_request_sync, transcript)

    def _summary_system_message(self, summary: str) -> Dict[str, str]:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        content = (
            f"{self.COMPACTION_MARKER}\n"
            f"Auto-compacted older conversation context at {timestamp}.\n"
            "Use this as compressed memory for older context. If it conflicts with preserved recent messages, prefer the recent messages.\n\n"
            f"{summary.strip()}"
        )
        return {"role": "system", "content": content}

    # ── Tool-call repair ────────────────────────────────────────────────

    def _assistant_tool_call_ids(self, message: Dict[str, Any]) -> List[str]:
        ids: List[str] = []
        for call in message.get("tool_calls") or []:
            if isinstance(call, dict) and call.get("id"):
                ids.append(str(call.get("id")))
        return ids

    def _repair_tool_boundaries(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Keep only provider-valid assistant tool-call clusters.

        Safe MVP rule: an assistant message with tool_calls is kept only when its
        matching tool results immediately follow it. Orphan tool messages are
        dropped. This may discard old tool detail, but avoids provider 400s.
        """
        repaired: List[Dict[str, Any]] = []
        i = 0
        while i < len(messages):
            message = messages[i]
            role = message.get("role")

            if role == "tool":
                # Orphan tool result, or a result separated from its assistant call.
                i += 1
                continue

            ids = self._assistant_tool_call_ids(message) if role == "assistant" else []
            if ids:
                cluster = [message]
                seen: List[str] = []
                j = i + 1

                while j < len(messages) and messages[j].get("role") == "tool":
                    tool_call_id = messages[j].get("tool_call_id")
                    if tool_call_id is not None:
                        tool_call_id = str(tool_call_id)
                    if tool_call_id in ids and tool_call_id not in seen:
                        cluster.append(messages[j])
                        seen.append(tool_call_id)
                    j += 1

                if set(ids).issubset(set(seen)):
                    repaired.extend(cluster)
                # Whether valid or invalid, consume immediately following tool
                # messages so partial clusters do not leak as orphans.
                i = j
                continue

            # Malformed assistant tool_calls with no usable IDs are safer to drop.
            if role == "assistant" and message.get("tool_calls"):
                i += 1
                continue

            repaired.append(message)
            i += 1

        return repaired

    # ── Final budget fitting ────────────────────────────────────────────

    def _fit_to_budget(
        self,
        system_messages: List[Dict[str, Any]],
        summary_message: Optional[Dict[str, Any]],
        first_turns: List[List[Dict[str, Any]]],
        recent_turns: List[List[Dict[str, Any]]],
        budget: int,
    ) -> Tuple[List[Dict[str, Any]], bool]:
        summary_dropped = False

        def assemble(
            summary: Optional[Dict[str, Any]],
            head: List[List[Dict[str, Any]]],
            tail: List[List[Dict[str, Any]]],
        ) -> List[Dict[str, Any]]:
            payload = list(system_messages)
            if summary is not None:
                payload.append(summary)
            payload.extend(self._flatten_turns(head))
            payload.extend(self._flatten_turns(tail))
            return self._repair_tool_boundaries(payload)

        head = list(first_turns)
        tail = list(recent_turns)
        payload = assemble(summary_message, head, tail)

        if self._messages_tokens(payload) <= budget:
            return payload, summary_dropped

        # Recent raw turns are more trustworthy than a generated summary. If the
        # summarized payload is still too large, drop the summary before trimming
        # raw context.
        if summary_message is not None:
            summary_dropped = True
            payload = assemble(None, head, tail)

        # Drop preserved head turns before recent turns; recent context matters
        # most for the active request.
        while self._messages_tokens(payload) > budget and head:
            head.pop()
            payload = assemble(None, head, tail)

        while self._messages_tokens(payload) > budget and len(tail) > 1:
            tail.pop(0)
            payload = assemble(None, head, tail)

        return payload, summary_dropped

    # ── Main inlet ──────────────────────────────────────────────────────

    async def inlet(
        self,
        body: dict,
        __event_emitter__: Optional[Callable] = None,
        __user__: Optional[dict] = None,
        __metadata__: Optional[dict] = None,
    ) -> dict:
        if not self.valves.enabled:
            return body

        messages = body.get("messages") or []
        if not isinstance(messages, list) or not messages:
            return body

        # Work on copies so the latest user message is never mutated by accident.
        messages = deepcopy(messages)
        model_id = str(body.get("model") or "")
        context_budget = self._context_budget_for_model(model_id)
        budget = self._effective_budget(model_id)
        before_tokens = self._messages_tokens(messages)

        if before_tokens <= budget:
            return body

        system_messages, other_messages = self._split_system_messages(messages)
        # Avoid reusing any previous synthetic compaction messages if the payload contains them.
        system_messages = [m for m in system_messages if not self._is_compactor_message(m)]
        other_messages = [m for m in other_messages if not self._is_compactor_message(m)]

        latest_user = self._latest_user_message(other_messages)
        if latest_user is None:
            return body

        min_tokens = self._messages_tokens(system_messages + [latest_user])
        if min_tokens > budget:
            self._raise_latest_too_large(min_tokens, budget)

        await self._emit_status(__event_emitter__, "Compacting chat context…", done=False)

        turns = self._build_turns(other_messages)
        keep_first_count = max(0, int(self.valves.keep_first_turns))
        keep_recent_count = max(1, int(self.valves.keep_recent_turns))

        first_indices = set(range(min(keep_first_count, len(turns))))
        recent_start = max(0, len(turns) - keep_recent_count)
        recent_indices = set(range(recent_start, len(turns)))

        # If head/recent windows overlap, assign overlapping turns to the recent
        # window so the latest user turn is protected from head trimming.
        first_turns = [
            turns[i]
            for i in range(len(turns))
            if i in first_indices and i not in recent_indices
        ]
        recent_turns = [turns[i] for i in range(len(turns)) if i in recent_indices]
        middle_turns = [
            turns[i]
            for i in range(len(turns))
            if i not in first_indices and i not in recent_indices
        ]
        older_messages = self._flatten_turns(middle_turns)

        summary_message: Optional[Dict[str, Any]] = None
        summary_failed = False
        semantic_disabled = False

        if older_messages and self._semantic_summary_enabled():
            try:
                summary = await self._summarize(older_messages, context_budget)
                if summary:
                    summary_message = self._summary_system_message(summary)
            except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError, Exception):
                summary_failed = True
                summary_message = None
        elif older_messages:
            semantic_disabled = True

        compacted_messages, summary_dropped = self._fit_to_budget(
            system_messages=system_messages,
            summary_message=summary_message,
            first_turns=first_turns,
            recent_turns=recent_turns,
            budget=budget,
        )

        after_tokens = self._messages_tokens(compacted_messages)
        if after_tokens > budget:
            # This should only happen when one recent turn is still too large but latest user itself fits.
            # Keep the latest user and system messages as the final safe fallback.
            compacted_messages = self._repair_tool_boundaries(system_messages + [latest_user])
            after_tokens = self._messages_tokens(compacted_messages)
            if after_tokens > budget:
                self._raise_latest_too_large(after_tokens, budget)

        body["messages"] = compacted_messages

        if summary_failed:
            await self._emit_status(
                __event_emitter__,
                f"Summary failed; trimmed older context instead (~{before_tokens} → ~{after_tokens} tokens).",
                done=True,
            )
        elif semantic_disabled:
            await self._emit_status(
                __event_emitter__,
                f"Semantic summary not configured; trimmed older context (~{before_tokens} → ~{after_tokens} tokens).",
                done=True,
            )
        elif summary_dropped:
            await self._emit_status(
                __event_emitter__,
                f"Compacted chat context, then dropped summary to fit budget (~{before_tokens} → ~{after_tokens} tokens).",
                done=True,
            )
        else:
            await self._emit_status(
                __event_emitter__,
                f"Compacted chat context: ~{before_tokens} → ~{after_tokens} tokens.",
                done=True,
            )

        return body
