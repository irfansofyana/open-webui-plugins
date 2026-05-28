# AGENTS.md

Instructions for AI coding agents working in this repository.

This file is the **single source of truth** for project conventions and Open WebUI plugin development guidance. It is intentionally tool-agnostic — it should be readable and actionable by any AI coding agent regardless of the harness it runs in.

---

## 1. About this repo

A personal curated collection of [Open WebUI](https://openwebui.com) plugins — filters, tools, pipes, and actions. Each plugin is self-contained in its own directory with code and a README. The repo is solo-maintained; PRs are not the primary contribution model. Code prioritizes clarity, small surface area, and ease of copy-pasting a single plugin into another user's Open WebUI instance.

---

## 2. Repo layout

```
open-webui-plugins/
├── filters/      # inlet / outlet / stream — request & response mutation
│   └── <name>/
│       ├── <name>.py
│       └── README.md
├── tools/        # LLM-callable functions (auto-generated schema from type hints)
├── pipes/        # custom models / proxies
├── actions/      # chat-message-toolbar buttons
├── AGENTS.md     # this file
├── CLAUDE.md     # thin pointer — imports AGENTS.md
├── README.md     # human-facing, install instructions
└── LICENSE       # MIT
```

**Rule:** one plugin per directory. Folder name = plugin name (kebab-case). The directory contains exactly one `.py` file (named the same as the directory) plus a `README.md`. No `__init__.py`, no test files, no examples dir.

---

## 3. Plugin types

Open WebUI has four extensible plugin types. Each has different install location and class shape.

| Type | Purpose | Reference in this repo | Official spec |
|---|---|---|---|
| **Filter** | Mutate request body (`inlet`), stream chunks (`stream`), or response (`outlet`). Cross-cutting: translation, redaction, style, prompt injection. | [filters/caveman/caveman.py](filters/caveman/caveman.py) | https://docs.openwebui.com/features/extensibility/plugin/functions/filter/ |
| **Pipe** | Custom model. Receives request body, returns response. For proxying external APIs, manifold models, custom logic. | *none yet* | https://docs.openwebui.com/features/extensibility/plugin/functions/pipe/ |
| **Action** | Adds a button to chat-message toolbar. Click → run code with event-system access. | *none yet* | https://docs.openwebui.com/features/extensibility/plugin/functions/action/ |
| **Tool** | Function the LLM can call. Type hints auto-generate JSON schema. Attached per-model. | *none yet* | https://docs.openwebui.com/features/extensibility/plugin/tools/ |

**Pattern when building a new plugin:**
1. Look at the existing reference in this repo for the type if one exists. Match its structure.
2. If no reference exists for the type, fetch the official spec (link above) — do not rely on training memory; Open WebUI APIs change. Always pull fresh docs.
3. Use `Valves` for admin-configurable settings, `UserValves` for per-user overrides. Both are pydantic `BaseModel` nested classes.
4. For filters that should be user-toggleable via the chat UI chip, set `self.toggle = True` in `__init__`.

---

## 4. Frontmatter spec

Open WebUI parses a YAML-style triple-quoted docstring at the top of every plugin file. Some fields are read by the platform; others are informational (read by humans and AI but ignored by the runtime). Both categories are required or recommended for this repo.

| Field | Required | Parsed by Open WebUI | Notes |
|---|---|---|---|
| `title` | ✅ | ✅ | Display name in admin UI. |
| `author` | ✅ | ✅ | `irfansofyana` for original work. |
| `author_url` | ✅ | ✅ | GitHub profile of the author. |
| `version` | ✅ | ✅ | Semantic version (`MAJOR.MINOR.PATCH`). |
| `required_open_webui_version` | ✅ | ✅ | Minimum Open WebUI version tested against. |
| `icon_url` | ⬜ | ✅ | URL for UI icon. Emoji-CDN URLs preferred for portability. |
| `requirements` | ⬜ | ✅ | Comma-separated pip packages; Open WebUI auto-installs them. Omit if no extra deps. |
| `license` | ✅ | ⬜ | Usually `MIT`. Repo default. |
| `description` | ✅ | ⬜ | One-line plain-English summary. |
| `credits` | ⬜ | ⬜ | Upstream attribution when the plugin is derived from or inspired by someone else's work. Include a URL. |
| `funding_url` | ⬜ | ⬜ | Sponsor link, typically for the upstream creator if the plugin is derived. |

**Format example** (drawn from `filters/caveman/caveman.py`):

```python
"""
title: Caveman Filter
author: irfansofyana
author_url: https://github.com/irfansofyana
version: 1.1.0
required_open_webui_version: 0.5.0
icon_url: https://em-content.zobj.net/source/apple/391/rock_1faa8.png
license: MIT
description: Terse caveman communication mode for Open WebUI. Cuts response tokens ~65-75% while keeping technical accuracy.
credits: Inspired by Julius Brussee's caveman skill — https://github.com/JuliusBrussee/caveman
funding_url: https://github.com/sponsors/JuliusBrussee
"""
```

**Do not use a `__meta__` dict.** Open WebUI does not parse it. Everything goes in the docstring.

---

## 5. Conventions

### Naming

- Plugin directory: kebab-case (`caveman`, `email-composer`, `inline-visualizer`).
- Plugin filename: matches directory name (`caveman/caveman.py`).
- Class name: as required by Open WebUI per type — `Filter`, `Pipe`, `Action`, `Tools`. Do not rename.
- Versioning: semver. Bump `PATCH` for bugfix, `MINOR` for new feature without breaking valves, `MAJOR` when valve shape or external behavior changes incompatibly.

### Attribution

- Original work authored in this repo: `author: irfansofyana`, `author_url: https://github.com/irfansofyana`.
- When a plugin is derived from or inspired by upstream work:
  - Keep `author` = the person who wrote *this* implementation (you).
  - Add a `credits:` line in the frontmatter pointing to the upstream source.
  - Add a "Credits" callout in the plugin's `README.md` naming the upstream creator and linking to their repo or sponsor page.
  - If upstream has a sponsor link, include `funding_url:` directing to *their* sponsor page (not yours) — recognise the source of the idea financially.

### Per-plugin README

Every plugin directory ships a `README.md`. Required sections (in order):
1. Title + one-line tagline.
2. Metadata block: Type, Author, Version, License, Required Open WebUI version, Source link.
3. Credits callout (if derived).
4. What it does.
5. Install steps (Workspace → Functions or Workspace → Tools, paste code).
6. Usage / commands / runtime behavior.
7. Configuration: admin valves table + user valves table.
8. Notes / caveats.

Look at [filters/caveman/README.md](filters/caveman/README.md) as the canonical example.

### Testing

There is no automated test harness — Open WebUI plugins require a running Open WebUI instance to validate. **AI agents must explicitly ask the user to load the plugin into their Open WebUI instance and confirm behavior before any change is marked "done."** Do not claim a plugin "works" based on code review alone.

---

## 6. Open WebUI references

Always fetch fresh content from these canonical sources — Open WebUI evolves and training-data memory is unreliable.

- **Plugin overview** — https://docs.openwebui.com/features/extensibility/plugin/
- **Functions (filter/pipe/action) overview** — https://docs.openwebui.com/features/extensibility/plugin/functions/
- **Filter spec** — https://docs.openwebui.com/features/extensibility/plugin/functions/filter/
- **Pipe spec** — https://docs.openwebui.com/features/extensibility/plugin/functions/pipe/
- **Action spec** — https://docs.openwebui.com/features/extensibility/plugin/functions/action/
- **Tool spec** — https://docs.openwebui.com/features/extensibility/plugin/tools/
- **Pipelines (advanced — separate from Functions)** — https://docs.openwebui.com/features/extensibility/pipelines/
- **Source of truth (Open WebUI repo)** — https://github.com/open-webui/open-webui
- **Community plugin search (prior art)** — https://openwebui.com/search

Before building a new plugin type that has no reference in this repo, the agent should fetch the spec URL above and read it, rather than guessing the class shape from memory.
