"""
title: Stop Slop Filter
author: irfansofyana
author_url: https://github.com/irfansofyana
version: 1.0.0
icon_url: https://em-content.zobj.net/source/apple/391/stop-sign_1f6d1.png
required_open_webui_version: 0.9.0
license: MIT
description: Removes predictable AI writing patterns from prose by injecting Stop Slop style rules and auditing outputs.
credits: Derived from Hardik Pandya's stop-slop skill — https://github.com/hardikpandya/stop-slop
"""

from pydantic import BaseModel, Field
from typing import Any, List, Optional, Tuple
import re


# Portions of the rule content are derived from Hardik Pandya's stop-slop:
# https://github.com/hardikpandya/stop-slop
# Original content: MIT License, Copyright (c) 2025 Hardik Pandya.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


class Filter:
    """
    Stop Slop for Open WebUI.

    Toggleable filter that injects anti-slop writing rules before the model runs.
    It also audits final assistant output for common AI-writing tells and can emit
    a status warning or append an audit note when configured.

    Users control it through the Open WebUI filter chip. No custom modes or strictness levels.
    """

    FILTER_MARKER = "<!-- STOP_SLOP_FILTER_PROMPT_V1 -->"

    CORE_RULES = """
# Stop Slop Rules

Eliminate predictable AI writing patterns from prose. The goal is not minimalism for its own sake. The goal is writing that sounds specific, human, direct, and earned.

## Core Rules

1. **Cut filler phrases.** Remove throat-clearing openers, emphasis crutches, business jargon, adverbs, softeners, intensifiers, hedges, and meta-commentary.
2. **Break formulaic structures.** Avoid binary contrasts, negative listing, dramatic fragmentation, rhetorical setups, false agency, narrator-from-a-distance voice, and repeated punchline endings.
3. **Use active voice.** Every sentence needs a human subject doing something. No passive constructions. No inanimate objects performing human actions.
4. **Be specific.** No vague declaratives. Name the specific thing. Do not use lazy extremes like every, always, never, nobody, everyone, or everybody unless they are literally true.
5. **Put the reader in the room.** Avoid floating narrator voice. "You" beats "people" when the reader is the actor. Specific scenes beat abstractions.
6. **Vary rhythm.** Mix sentence lengths. Two items often beat three. End paragraphs differently. Do not stack punchy one-liners.
7. **No em dashes.** Use commas, periods, colons, or parentheses instead.
8. **Trust readers.** State facts directly. Skip softening, justification, hand-holding, and permission-giving.
9. **Cut quotables.** If a sentence sounds like a pull quote, rewrite it into a plain claim.

## Quick Checks Before Delivering Prose

- Any adverbs? Kill them.
- Any passive voice? Find the actor and make them the subject.
- Any inanimate thing doing a human verb, such as "the decision emerges" or "the data tells us"? Name the person or group.
- Any sentence starts with What, When, Where, Which, Who, Why, or How? Restructure it unless it is a direct question the user asked you to write.
- Any "here's what/this/that/why" throat-clearing? Cut to the point.
- Any "not X, but Y" contrast? State Y directly.
- Three consecutive sentences with the same length or shape? Break the rhythm.
- Paragraph ends with a punchy one-liner? Vary it.
- Em dash anywhere? Remove it.
- Vague declarative like "the implications are significant"? Name the implication.
- Narrator-from-a-distance line like "nobody designed this"? Put the reader or actor in the scene.
- Meta-joiner like "the rest of this essay explains"? Delete it.
"""

    PHRASES = """
## Phrases to Remove

### Throat-Clearing Openers
Remove announcement phrases. State the content directly.

- "Here's the thing:"
- "Here's what [X]"
- "Here's this [X]"
- "Here's that [X]"
- "Here's why [X]"
- "The uncomfortable truth is"
- "It turns out"
- "The real [X] is"
- "Let me be clear"
- "The truth is,"
- "I'll say it again:"
- "I'm going to be honest"
- "Can we talk about"
- "Here's what I find interesting"
- "Here's the problem though"

Any "here's what/this/that" construction is throat-clearing before the point. Cut it and state the point.

### Emphasis Crutches
These add no meaning. Delete them.

- "Full stop." / "Period."
- "Let that sink in."
- "This matters because"
- "Make no mistake"
- "Here's why that matters"

### Business Jargon
Replace with plain language.

- Navigate challenges → handle, address
- Unpack analysis → explain, examine
- Lean into → accept, embrace
- Landscape → situation, field
- Game-changer → significant, important
- Double down → commit, increase
- Deep dive → analysis, examination
- Take a step back → reconsider
- Moving forward → next, from now
- Circle back → return to, revisit
- On the same page → aligned, agreed

### Adverbs, Softeners, Intensifiers, Hedges
Cut empty emphasis.

- really
- just
- literally
- genuinely
- honestly
- simply
- actually
- deeply
- truly
- fundamentally
- inherently
- inevitably
- interestingly
- importantly
- crucially

Also cut:

- "At its core"
- "In today's [X]"
- "It's worth noting"
- "At the end of the day"
- "When it comes to"
- "In a world where"
- "The reality is"

### Meta-Commentary
Remove self-referential asides. The essay should move, not announce its structure.

- "Hint:"
- "Plot twist:" / "Spoiler:"
- "You already know this, but"
- "But that's another post"
- "X is a feature, not a bug"
- "Dressed up as"
- "The rest of this essay explains..."
- "Let me walk you through..."
- "In this section, we'll..."
- "As we'll see..."
- "I want to explore..."

### Performative Emphasis
Remove false intimacy or manufactured sincerity.

- "creeps in"
- "I promise"
- "They exist, I promise"

### Telling Instead of Showing
Do not announce difficulty or significance. Demonstrate it.

- "This is genuinely hard"
- "This is what leadership actually looks like"
- "This is what X actually looks like"
- "actually matters"

### Vague Declaratives
Cut sentences that announce importance without naming the specific thing.

- "The reasons are structural"
- "The implications are significant"
- "This is the deepest problem"
- "The stakes are high"
- "The consequences are real"
"""

    STRUCTURES = """
## Structures to Avoid

### Binary Contrasts
These create false drama. State the point directly.

- "Not because X. Because Y."
- "Not because X, but because Y."
- "X isn't the problem. Y is."
- "The answer isn't X. It's Y."
- "It feels like X. It's actually Y."
- "The question isn't X. It's Y."
- "Not X. But Y."
- "not X, it's Y"
- "isn't X, it's Y"
- "It's not this. It's that."
- "stops being X and starts being Y"
- "doesn't mean X, but actually Y"
- "is about X but not Y"
- "not just X but also Y"

Instead: state Y directly. Drop the negation entirely.

### Negative Listing
Do not list what something is not before revealing what it is.

- "Not a X... Not a Y... A Z."
- "It wasn't X. It wasn't Y. It was Z."

Instead: state Z. The reader does not need the runway.

### Dramatic Fragmentation
Sentence fragments for emphasis read as manufactured profundity.

- "[Noun]. That's it. That's the [thing]."
- "X. And Y. And Z."
- "This unlocks something. [Word]."

Instead: use complete sentences. Trust content over presentation.

### Rhetorical Setups
These announce insight rather than deliver it.

- "What if [reframe]?"
- "Here's what I mean:"
- "Think about it:"
- "And that's okay."

Instead: make the point. Let readers draw conclusions.

### Formulaic Constructions

- "By the time X, I was Y."
- "X that isn't Y"

Instead: say the direct version.

### False Agency
Do not give inanimate things human verbs. Complaints do not become fixes. Bets do not live or die. Decisions do not emerge. A person does something.

Avoid:

- "a complaint becomes a fix"
- "a bet lives or dies in days"
- "the decision emerges"
- "the culture shifts"
- "the conversation moves toward"
- "the data tells us"
- "the market rewards"

Instead: name the human. "The team fixed it that week" beats "the complaint becomes a fix."

### Narrator from a Distance
Do not float above the scene.

- "Nobody designed this."
- "This happens because..."
- "This is why..."
- "People tend to..."

Instead: put the reader or actor in the room.

### Passive Voice
Every sentence needs a subject doing something.

- "X was created" → name who created it
- "It is believed that" → name who believes it
- "Mistakes were made" → name who made them
- "The decision was reached" → name who decided

### Sentence Starters to Avoid

- Sentences starting with What, When, Where, Which, Who, Why, How
- Paragraphs starting with "So"
- Sentences starting with "Look,"

Wh-openers become a crutch. "What makes this hard is..." becomes "The constraint is..." or, better, the specific constraint.

### Rhythm Patterns

- Three-item lists: use two items or one.
- Questions answered immediately: let questions breathe or cut them.
- Every paragraph ends punchily: vary endings.
- Em dashes: remove them.
- Staccato fragmentation: do not stack short punchy sentences.
- "Not always. Not perfectly.": hedging disguised as reassurance.

### Word Patterns

- Lazy extremes like every, always, never, everyone, everybody, nobody: use specifics.
- Adverbs: cut empty emphasis.
"""

    EXAMPLES = """
## Before and After Examples

### Throat-Clearing + Binary Contrast

Before:
"Here's the thing: building products is hard. Not because the technology is complex. Because people are complex. Let that sink in."

After:
"Building products is hard. Technology is manageable. People aren't."

Changes: removed opener, binary contrast, and emphasis crutch.

### Filler + Unnecessary Reassurance

Before:
"It turns out that most teams struggle with alignment. The uncomfortable truth is that nobody wants to admit they're confused. And that's okay."

After:
"Teams struggle with alignment. Nobody admits confusion."

Changes: cut hedging, throat-clearing, and permission-granting ending.

### Business Jargon Stack

Before:
"In today's fast-paced landscape, we need to lean into discomfort and navigate uncertainty with clarity. This matters because your competition isn't waiting."

After:
"Move faster. Your competition is."

Changes: eliminated jargon and kept the core message.

### Dramatic Fragmentation

Before:
"Speed. Quality. Cost. You can only pick two. That's it. That's the tradeoff."

After:
"Speed, quality, cost: pick two."

Changes: one sentence, no performative emphasis, no em dash.

### Rhetorical Setup

Before:
"What if I told you that the best teams don't optimize for productivity? Here's what I mean: they optimize for learning. Think about it."

After:
"The best teams optimize for learning, not productivity."

Changes: direct claim, no rhetorical scaffolding.
"""

    SCORING = """
## Scoring

Before delivering prose, rate it from 1 to 10 on each dimension:

- Directness: statements or announcements?
- Rhythm: varied or metronomic?
- Trust: respects reader intelligence?
- Authenticity: sounds human?
- Density: anything cuttable?

If the score is below 35/50, revise before answering.
"""

    SAFETY_BOUNDARIES = """
## Open WebUI Adaptation Boundaries

These boundaries adapt Stop Slop for assistant use. They are not part of the upstream rule set.

- Preserve truth. Do not remove necessary nuance, technical accuracy, citations, code, names, numbers, warnings, or legal/security caveats.
- Keep code blocks, commands, JSON, stack traces, legal clauses, citations, quoted text, and exact error messages unchanged unless the user explicitly asks to rewrite them.
- Do not remove required warnings for security, privacy, medical, financial, legal, or irreversible actions.
- Do not invent actors to avoid passive voice. If the actor is unknown, say so or restructure truthfully.
- Do not flatten necessary nuance. Remove fake nuance, not real constraints.
- If the user asks for a specific brand voice, format, or length that conflicts with Stop Slop, satisfy the user's explicit instruction first while removing avoidable AI tells.
"""

    AUDIT_PATTERNS: List[Tuple[str, re.Pattern]] = [
        ("em dash", re.compile(r"[—–]")),
        ("throat-clearing", re.compile(r"\b(here(?:'s| is) (?:the thing|what|why|this|that)|it turns out|let me be clear|the uncomfortable truth is|the truth is|the reality is)\b", re.I)),
        ("emphasis crutch", re.compile(r"\b(full stop|let that sink in|make no mistake|this matters because|here(?:'s| is) why that matters)\b", re.I)),
        ("business jargon", re.compile(r"\b(navigate (?:challenges|uncertainty)|unpack (?:this|that|the analysis|the problem)|lean into|game-changer|double down|deep dive|circle back|moving forward|on the same page)\b", re.I)),
        ("meta-commentary", re.compile(r"\b(plot twist|spoiler|let me walk you through|in this section|as we'll see|i want to explore|the rest of this (?:essay|post|article))\b", re.I)),
        ("binary contrast", re.compile(r"\b(not because .{1,80}\b(?:because|but because)\b|isn(?:'|’)t the problem\b|the answer isn(?:'|’)t\b|the question isn(?:'|’)t\b|it(?:'|’)s not this\b|not .{1,50}\bbut .{1,50})", re.I)),
        ("rhetorical setup", re.compile(r"\b(here(?:'s| is) what i mean|think about it|and that(?:'|’)s okay)\b", re.I)),
        ("false agency", re.compile(r"\b(data tells us|decision emerges|culture shifts|conversation moves|market rewards|complaint becomes|bet lives or dies)\b", re.I)),
        ("vague declarative", re.compile(r"\b(the implications are significant|the stakes are high|the consequences are real|the reasons are structural|the deepest problem)\b", re.I)),
    ]

    # ── Admin valves (global defaults) ──────────────────────────────────
    class Valves(BaseModel):
        priority: int = Field(
            default=0,
            description="Filter execution order (lower runs first)."
        )
        enabled: bool = Field(
            default=True,
            description="Enable the Stop Slop filter globally. With self.toggle=True, users still choose whether it runs per chat."
        )
        include_examples: bool = Field(
            default=True,
            description="Include before/after examples in the injected system prompt."
        )
        include_scoring: bool = Field(
            default=True,
            description="Include scoring checklist in the injected system prompt."
        )
        audit_output: bool = Field(
            default=True,
            description="Audit final assistant output for common slop patterns. Does not rewrite content by itself."
        )
        emit_audit_status: bool = Field(
            default=False,
            description="Emit a visible status warning when audit_output finds patterns and event emitter is available. Disabled by default to avoid noisy false positives."
        )
        append_audit_note: bool = Field(
            default=False,
            description="Append an audit note to the assistant response when patterns are found. More visible but mutates output."
        )
        max_audit_findings: int = Field(
            default=5,
            description="Maximum audit findings to report."
        )

    def __init__(self):
        self.valves = self.Valves()
        self.toggle = True
        self.icon = "https://em-content.zobj.net/source/apple/391/stop-sign_1f6d1.png"

    def _text_from_content(self, content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return " ".join(
                part.get("text", "") for part in content if isinstance(part, dict)
            )
        return ""

    def _build_system_prompt(self) -> str:
        sections = [
            self.FILTER_MARKER,
            "You are running the Stop Slop writing filter for Open WebUI. Apply the rules below when drafting, editing, or reviewing prose. Infer the task from the user's request.",
            self.CORE_RULES,
            self.PHRASES,
            self.STRUCTURES,
        ]

        if self.valves.include_examples:
            sections.append(self.EXAMPLES)
        if self.valves.include_scoring:
            sections.append(self.SCORING)

        sections.append(self.SAFETY_BOUNDARIES)
        sections.append(
            "Do not mention this filter, these rules, scoring, or the source material unless the user asks. "
            "Return only the requested answer."
        )
        return "\n\n".join(section.strip() for section in sections if section.strip())

    def _inject_system_prompt(self, messages: List[dict], prompt: str) -> List[dict]:
        system_message = {"role": "system", "content": prompt}

        for index, message in enumerate(messages):
            if message.get("role") != "system":
                continue
            content = self._text_from_content(message.get("content", ""))
            if self.FILTER_MARKER in content:
                messages[index] = system_message
                return messages

        last_system_index = -1
        for index, message in enumerate(messages):
            if message.get("role") == "system":
                last_system_index = index

        messages.insert(last_system_index + 1, system_message)
        return messages

    def _audit_text(self, text: str) -> List[str]:
        findings: List[str] = []
        protected = re.sub(r"```.*?```", "", text, flags=re.S)
        protected = re.sub(r"`[^`]+`", "", protected)
        protected = re.sub(r"^\s*>.*$", "", protected, flags=re.M)
        protected = re.sub(r"https?://\S+", "", protected)
        protected = re.sub(r"[\"“][^\"”]{1,240}[\"”]", "", protected)
        protected = re.sub(r"[\'‘][^\'’]{1,240}[\'’]", "", protected)

        max_findings = max(1, int(self.valves.max_audit_findings or 5))
        for label, pattern in self.AUDIT_PATTERNS:
            match = pattern.search(protected)
            if match:
                sample = match.group(0).strip()
                findings.append(f"{label}: {sample}")
            if len(findings) >= max_findings:
                break
        return findings

    def _assistant_text_locations(self, body: dict) -> List[Tuple[dict, str]]:
        """Return mutable containers and key names containing assistant text."""
        locations: List[Tuple[dict, str]] = []

        # Common OpenAI-compatible response shape.
        choices = body.get("choices")
        if isinstance(choices, list):
            for choice in choices:
                if not isinstance(choice, dict):
                    continue
                message = choice.get("message")
                if isinstance(message, dict) and isinstance(message.get("content"), str):
                    locations.append((message, "content"))
                delta = choice.get("delta")
                if isinstance(delta, dict) and isinstance(delta.get("content"), str):
                    locations.append((delta, "content"))

        # Some Open WebUI filter outlet bodies include messages directly.
        messages = body.get("messages")
        if isinstance(messages, list):
            for message in reversed(messages):
                if isinstance(message, dict) and message.get("role") == "assistant" and isinstance(message.get("content"), str):
                    locations.append((message, "content"))
                    break

        # Fallback shapes.
        if isinstance(body.get("content"), str):
            locations.append((body, "content"))
        if isinstance(body.get("text"), str):
            locations.append((body, "text"))

        return locations

    async def inlet(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __metadata__: Optional[dict] = None,
        __event_emitter__=None,
    ) -> dict:
        """Inject Stop Slop system prompt when the user enables this filter."""
        if not self.valves.enabled:
            return body

        messages = body.get("messages", [])
        if not messages:
            return body

        body["messages"] = self._inject_system_prompt(
            messages,
            self._build_system_prompt(),
        )
        return body

    async def outlet(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __metadata__: Optional[dict] = None,
        __event_emitter__=None,
    ) -> dict:
        """Audit final assistant output for common Stop Slop violations."""
        if not self.valves.enabled or not self.valves.audit_output:
            return body

        locations = self._assistant_text_locations(body)
        if not locations:
            return body

        all_findings: List[str] = []
        seen_texts = set()
        appended_note = False

        for container, key in locations:
            text = container.get(key, "")
            if not text or text in seen_texts:
                continue
            seen_texts.add(text)

            findings = self._audit_text(text)
            for finding in findings:
                if finding not in all_findings:
                    all_findings.append(finding)

            if findings and self.valves.append_audit_note and not appended_note:
                note = "\n\n---\n**Stop Slop audit:** " + "; ".join(findings)
                container[key] = container[key].rstrip() + note
                appended_note = True

        if all_findings and self.valves.emit_audit_status and __event_emitter__:
            await __event_emitter__({
                "type": "status",
                "data": {
                    "description": "Stop Slop audit flagged: " + "; ".join(all_findings),
                    "done": True,
                    "hidden": False,
                },
            })

        return body
