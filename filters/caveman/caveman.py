"""
title: Caveman Filter
author: irfansofyana
author_url: https://github.com/irfansofyana
funding_url: https://github.com/sponsors/JuliusBrussee
version: 1.1.0
icon_url: https://em-content.zobj.net/source/apple/391/rock_1faa8.png
required_open_webui_version: 0.5.0
license: MIT
description: Terse caveman communication mode for Open WebUI. Cuts response tokens ~65-75% while keeping full technical accuracy.
credits: Inspired by Julius Brussee's caveman skill — https://github.com/JuliusBrussee/caveman
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict


class Filter:
    """
    Injects the caveman communication style into every LLM request via inlet().

    The LLM generates caveman prose natively — no post-processing needed.

    Always-on when enabled. Users toggle per-chat via the UI chip (self.toggle = True).
    Users can switch intensity mid-conversation with: !caveman [lite|full|ultra|wenyan-*]
    Note: ! prefix used because Open WebUI reserves / for prompt presets.
    Intensity override persists per chat_id in memory (resets on server restart).

    Intensity levels:
      lite        — No filler/hedging. Full sentences. Professional but tight.
      full        — Drop articles, fragments OK. Classic caveman. (default)
      ultra       — Abbreviate prose words, arrows for causality, bare fragments.
      wenyan-lite — Semi-classical Chinese register, light compression.
      wenyan-full — Maximum classical terseness. Fully 文言文.
      wenyan-ultra— Extreme classical compression.
    """

    CAVEMAN_PROMPTS: Dict[str, str] = {
        "lite": (
            "Respond terse. No filler, no hedging. Keep articles + full sentences. Professional but tight. "
            "Short synonyms. Technical terms exact. Code blocks unchanged. Errors quoted exact.\n\n"
            "Pattern: [thing] [action] [reason]. [next step].\n\n"
            "Example — 'Why React component re-render?':\n"
            "\"Your component re-renders because you create a new object reference each render. Wrap it in `useMemo`.\"\n\n"
            "Example — 'Explain database connection pooling.':\n"
            "\"Connection pooling reuses open connections instead of creating new ones per request. Avoids repeated handshake overhead.\"\n\n"
            "Boundaries: code blocks, commits, PRs — write normal."
        ),
        "full": (
            "Respond terse like smart caveman. All technical substance stay. Only fluff die.\n\n"
            "Drop: articles (a/an/the), filler (just/really/basically/actually/simply), "
            "pleasantries (sure/certainly/of course/happy to), hedging. "
            "Fragments OK. Short synonyms (big not extensive, fix not 'implement a solution for'). "
            "Technical terms exact. Code blocks unchanged. Errors quoted exact.\n\n"
            "Pattern: [thing] [action] [reason]. [next step].\n\n"
            "Not: 'Sure! I'd be happy to help you with that. The issue you're experiencing is likely caused by...'\n"
            "Yes: 'Bug in auth middleware. Token expiry check use `<` not `<=`. Fix:'\n\n"
            "Example — 'Why React component re-render?':\n"
            "\"New object ref each render. Inline object prop = new ref = re-render. Wrap in `useMemo`.\"\n\n"
            "Example — 'Explain database connection pooling.':\n"
            "\"Pool reuse open DB connections. No new connection per request. Skip handshake overhead.\"\n\n"
            "Boundaries: code blocks, commits, PRs — write normal."
        ),
        "ultra": (
            "Respond ultra-minimal caveman. All technical substance stay. Maximum compression.\n\n"
            "Abbreviate prose words (DB/auth/config/req/res/fn/impl). "
            "Strip conjunctions. Arrows for causality (X → Y). One word when one word enough. "
            "Code symbols, function names, API names, error strings: NEVER abbreviate.\n\n"
            "Pattern: [thing] [action] [reason]. [next step].\n\n"
            "Example — 'Why React component re-render?':\n"
            "\"Inline obj prop → new ref → re-render. `useMemo`.\"\n\n"
            "Example — 'Explain database connection pooling.':\n"
            "\"Pool = reuse DB conn. Skip handshake → fast under load.\"\n\n"
            "Boundaries: code blocks, commits, PRs — write normal."
        ),
        "wenyan-lite": (
            "Respond semi-classical Chinese register. Drop filler/hedging but keep grammar structure. Classical register. "
            "Technical terms exact. Code blocks unchanged.\n\n"
            "Example — 'Why React component re-render?':\n"
            "\"組件頻重繪，以每繪新生對象參照故。以 useMemo 包之。\""
        ),
        "wenyan-full": (
            "Respond maximum classical Chinese terseness. Fully 文言文. "
            "Classical sentence patterns. Verbs precede objects. Subjects often omitted. "
            "Classical particles (之/乃/為/其). 80-90% character reduction. "
            "Technical terms exact. Code blocks unchanged.\n\n"
            "Example — 'Why React component re-render?':\n"
            "\"物出新參照，致重繪。useMemo Wrap之。\"\n\n"
            "Example — 'Explain database connection pooling.':\n"
            "\"池reuse open connection。不每req新開。skip handshake overhead。\""
        ),
        "wenyan-ultra": (
            "Respond extreme classical Chinese compression. Maximum classical terseness. Ultra-compressed. "
            "Technical terms exact. Code blocks unchanged.\n\n"
            "Example — 'Why React component re-render?':\n"
            "\"新參照→重繪。useMemo Wrap。\"\n\n"
            "Example — 'Explain database connection pooling.':\n"
            "\"池reuse conn。skip handshake → fast。\""
        ),
    }

    AUTO_CLARITY_RULES = (
        "Auto-clarity: temporarily drop caveman compression for:\n"
        "- Security warnings\n"
        "- Irreversible action confirmations\n"
        "- Multi-step sequences where fragment order or omitted conjunctions risk misread\n"
        "- Compression itself creates technical ambiguity "
        "(e.g., 'migrate table drop column backup first' — order unclear without conjunctions)\n"
        "- User asks to clarify or repeats question\n"
        "Resume caveman after the clear part is done."
    )

    # ── Admin valves (global defaults) ──────────────────────────────────
    class Valves(BaseModel):
        priority: int = Field(
            default=0,
            description="Filter execution order (lower runs first)."
        )
        enabled: bool = Field(
            default=True,
            description="Enable the caveman filter globally."
        )
        intensity: str = Field(
            default="full",
            description="Default caveman intensity. Options: lite, full, ultra, wenyan-lite, wenyan-full, wenyan-ultra."
        )
        auto_clarity: bool = Field(
            default=True,
            description="Inject auto-clarity rules for security warnings and destructive operations."
        )

    # ── Per-user valves (each user customizes) ───────────────────────────
    class UserValves(BaseModel):
        intensity: str = Field(
            default="",
            description="Your preferred caveman intensity. Leave empty to use admin default. Options: lite, full, ultra, wenyan-lite, wenyan-full, wenyan-ultra."
        )

    def __init__(self):
        self.valves = self.Valves()
        self.toggle = True
        # Per-chat intensity overrides keyed by chat_id.
        # In-memory only — resets on server restart, falls back to user/admin default.
        self._chat_intensities: Dict[str, str] = {}

    def _parse_intensity_command(self, content: str) -> Optional[str]:
        """
        Detect !caveman [level] intensity-switch commands.

        Uses ! prefix (not /) because Open WebUI reserves / for prompt presets.

        Returns the intensity string if a valid command is found, else None.
        Returns "" (empty string sentinel) for bare !caveman → resets to default.
        Does NOT handle on/off toggling — that's managed by self.toggle via the UI.
        """
        text = content.strip().lower()
        if not text.startswith("!caveman"):
            return None
        parts = text.split(None, 1)
        if len(parts) == 1:
            # bare !caveman → reset to default (return empty string as sentinel)
            return ""
        level = parts[1].strip()
        if level in self.CAVEMAN_PROMPTS:
            return level
        if level == "wenyan":
            return "wenyan-full"
        # Unknown level — ignore command
        return None

    def _get_system_prompt(self, intensity: str) -> str:
        """Build the full caveman system prompt for the given intensity level."""
        prompt = self.CAVEMAN_PROMPTS.get(intensity, self.CAVEMAN_PROMPTS["full"])
        if self.valves.auto_clarity:
            prompt = f"{prompt}\n\n{self.AUTO_CLARITY_RULES}"
        return prompt

    def _resolve_intensity(
        self,
        chat_id: Optional[str],
        user_valves_intensity: str,
    ) -> str:
        """
        Intensity priority:
          1. Per-chat override (set via !caveman command)
          2. UserValves preference
          3. Admin Valves default
        """
        if chat_id and chat_id in self._chat_intensities:
            return self._chat_intensities[chat_id]
        if user_valves_intensity and user_valves_intensity in self.CAVEMAN_PROMPTS:
            return user_valves_intensity
        if self.valves.intensity in self.CAVEMAN_PROMPTS:
            return self.valves.intensity
        return "full"

    async def inlet(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __metadata__: Optional[dict] = None,
    ) -> dict:
        """
        Inject caveman system prompt on every request (filter is always-on when enabled).
        Handles !caveman [level] commands to switch intensity per chat.
        """
        if not self.valves.enabled:
            return body

        messages = body.get("messages", [])
        if not messages:
            return body

        # Resolve UserValves intensity — __user__["valves"] is a Pydantic object, use getattr
        valves_obj = __user__.get("valves") if __user__ else None
        user_valves_intensity = getattr(valves_obj, "intensity", "") or ""

        # Get chat_id for per-chat intensity state
        chat_id = (__metadata__ or {}).get("chat_id")

        # Check last user message for intensity command
        last_user_content = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_content = msg.get("content", "")
                if isinstance(last_user_content, list):
                    # Multi-modal content — extract text parts
                    last_user_content = " ".join(
                        p.get("text", "") for p in last_user_content if isinstance(p, dict)
                    )
                break

        command = self._parse_intensity_command(last_user_content)
        if command is not None and chat_id:
            if command == "":
                # bare !caveman → clear per-chat override, revert to user/admin default
                self._chat_intensities.pop(chat_id, None)
            else:
                self._chat_intensities[chat_id] = command

        # Resolve effective intensity
        intensity = self._resolve_intensity(chat_id, user_valves_intensity)

        # Build and inject system prompt
        system_message = {
            "role": "system",
            "content": self._get_system_prompt(intensity),
        }

        # Replace existing caveman system prompt or prepend
        if (
            messages
            and messages[0].get("role") == "system"
            and "caveman" in messages[0].get("content", "").lower()
        ):
            messages[0] = system_message
        else:
            messages.insert(0, system_message)

        body["messages"] = messages
        return body

    async def outlet(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __metadata__: Optional[dict] = None,
    ) -> dict:
        """
        No outlet processing needed — caveman style generated natively by LLM.
        Reserved for future extensions (usage stats, token savings logging).
        """
        return body
