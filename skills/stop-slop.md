---
name: stop-slop
description: Remove predictable AI writing patterns from prose. Use when drafting, editing, or reviewing text to eliminate AI tells.
---

# Stop Slop

Eliminate predictable AI writing patterns from prose. The goal is not minimalism for its own sake. The goal is writing that sounds specific, human, direct, and earned.

> Derived from Hardik Pandya's [stop-slop](https://github.com/hardikpandya/stop-slop), MIT License, Copyright (c) 2025 Hardik Pandya.

## Open WebUI Skill Packaging

Open WebUI Skills are imported as a single Markdown file. This file intentionally includes the merged rules, examples, scoring checklist, Open WebUI adaptation boundaries, and license notice inline so it works without external references.

For users/admins: this Skill provides instruction-only behavior. It does not audit outputs, emit status warnings, expose admin valves, or mutate responses. Use the Filter version if you want a chat chip plus output audit controls.

Do not enable both the Skill and Filter for the same chat/model unless you intentionally want duplicate Stop Slop instructions.

## How to Use This Skill

Use this skill when drafting, editing, or reviewing prose. Apply the rules silently unless the user asks for a review. Return the requested content directly.

If the user asks you to review text, identify concrete problems first, then provide a cleaner rewrite.

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

| Avoid | Use instead |
|---|---|
| Navigate challenges | Handle, address |
| Unpack analysis | Explain, examine |
| Lean into | Accept, embrace |
| Landscape | Situation, field |
| Game-changer | Significant, important |
| Double down | Commit, increase |
| Deep dive | Analysis, examination |
| Take a step back | Reconsider |
| Moving forward | Next, from now |
| Circle back | Return to, revisit |
| On the same page | Aligned, agreed |

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

| Pattern | Fix |
|---|---|
| "X was created" | Name who created it |
| "It is believed that" | Name who believes it |
| "Mistakes were made" | Name who made them |
| "The decision was reached" | Name who decided |

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

## Before and After Examples

### Throat-Clearing + Binary Contrast

Before:

> "Here's the thing: building products is hard. Not because the technology is complex. Because people are complex. Let that sink in."

After:

> "Building products is hard. Technology is manageable. People aren't."

Changes: removed opener, binary contrast, and emphasis crutch.

### Filler + Unnecessary Reassurance

Before:

> "It turns out that most teams struggle with alignment. The uncomfortable truth is that nobody wants to admit they're confused. And that's okay."

After:

> "Teams struggle with alignment. Nobody admits confusion."

Changes: cut hedging, throat-clearing, and permission-granting ending.

### Business Jargon Stack

Before:

> "In today's fast-paced landscape, we need to lean into discomfort and navigate uncertainty with clarity. This matters because your competition isn't waiting."

After:

> "Move faster. Your competition is."

Changes: eliminated jargon and kept the core message.

### Dramatic Fragmentation

Before:

> "Speed. Quality. Cost. You can only pick two. That's it. That's the tradeoff."

After:

> "Speed, quality, cost: pick two."

Changes: one sentence, no performative emphasis, no em dash.

### Rhetorical Setup

Before:

> "What if I told you that the best teams don't optimize for productivity? Here's what I mean: they optimize for learning. Think about it."

After:

> "The best teams optimize for learning, not productivity."

Changes: direct claim, no rhetorical scaffolding.

## Scoring

Before delivering prose, rate it from 1 to 10 on each dimension:

| Dimension | Question |
|---|---|
| Directness | Statements or announcements? |
| Rhythm | Varied or metronomic? |
| Trust | Respects reader intelligence? |
| Authenticity | Sounds human? |
| Density | Anything cuttable? |

Below 35/50: revise before answering.

## Open WebUI Adaptation Boundaries

These boundaries adapt Stop Slop for assistant use. They are not part of the upstream rule set.

- Preserve truth. Do not remove necessary nuance, technical accuracy, citations, code, names, numbers, warnings, or legal/security caveats.
- Keep code blocks, commands, JSON, stack traces, legal clauses, citations, quoted text, and exact error messages unchanged unless the user explicitly asks to rewrite them.
- Do not remove required warnings for security, privacy, medical, financial, legal, or irreversible actions.
- Do not invent actors to avoid passive voice. If the actor is unknown, say so or restructure truthfully.
- Do not flatten necessary nuance. Remove fake nuance, not real constraints.
- If the user asks for a specific brand voice, format, or length that conflicts with Stop Slop, satisfy the user's explicit instruction first while removing avoidable AI tells.

## License

This merged Open WebUI Skill is derived from Hardik Pandya's [stop-slop](https://github.com/hardikpandya/stop-slop), MIT License, Copyright (c) 2025 Hardik Pandya.

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
