# Open WebUI Plugins

> Personal curated collection of [Open WebUI](https://openwebui.com) plugins — filters, tools, pipes, and actions that extend the chat experience.

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Open WebUI](https://img.shields.io/badge/Open%20WebUI-%E2%89%A50.5.0-7c3aed.svg)](https://docs.openwebui.com)

---

## Plugins

### Filters
| Name | Description | Source |
|---|---|---|
| [Caveman](filters/caveman) | Terse caveman communication mode. Cuts response tokens ~65–75% while keeping technical accuracy. 6 intensity levels, auto-clarity safety, per-chat toggle. | [caveman.py](filters/caveman/caveman.py) |

### Tools
*(none yet)*

### Pipes
*(none yet)*

### Actions
*(none yet)*

---

## Plugin types in Open WebUI

| Type | Purpose | Install location |
|---|---|---|
| **Filter** | Mutate request body (`inlet`), stream chunks (`stream`), or response (`outlet`). Cross-cutting concerns: translation, redaction, prompt injection, style. | Workspace → Functions |
| **Pipe** | Custom model. Receives request body, returns a response. Used for proxying external APIs, manifold models, or fully custom logic. | Workspace → Functions |
| **Action** | Adds a button to the chat message toolbar. Click → run custom code with access to the event system. | Workspace → Functions |
| **Tool** | Function the LLM can call. Type hints auto-generate JSON schema. Attached per-model. | Workspace → Tools |

For deeper detail, see the official [Open WebUI plugin docs](https://docs.openwebui.com/features/extensibility/plugin/).

---

## Installation

### Quick install (any plugin in this repo)
1. Open the plugin's `.py` file in this repo, copy the full contents.
2. In Open WebUI, go to **Workspace → Functions** (for filters/pipes/actions) or **Workspace → Tools** (for tools).
3. Click **+ New Function** / **+ New Tool**, paste the code, save.
4. Toggle on. Filters appear as chips in the chat input; tools attach per-model.

### Per-plugin configuration
Every plugin has its own `README.md` covering:
- What it does and when to use it
- Admin valves (global settings)
- User valves (per-user settings)
- Commands / runtime behavior
- Compatibility notes

---

## Repo layout

```
open-webui-plugins/
├── filters/      # inlet/outlet/stream — request & response mutation
│   └── <name>/
│       ├── <name>.py
│       └── README.md
├── tools/        # LLM-callable functions with auto-generated schemas
├── pipes/        # custom models / proxies
├── actions/      # message-toolbar buttons
├── LICENSE
└── README.md
```

Each plugin lives in its own directory: code + README. Self-contained, copy-pasteable.

---

## Conventions

- **One plugin per directory.** Folder name = plugin name (kebab-case).
- **Frontmatter at top of every `.py`** with `title`, `author`, `version`, `required_open_webui_version`, optional `icon_url` / `funding_url`. Open WebUI parses this for the UI.
- **Valves vs UserValves.** Admin-global config in `Valves`, per-user overrides in `UserValves`.
- **`self.toggle = True`** for filters that should show as a user-controllable chip.
- **MIT licensed.** Original work goes under my name (`author: irfansofyana`). When a plugin is inspired by or derived from someone else's work, credit them explicitly in the frontmatter (`credits` field + `funding_url` when applicable) and in the plugin README.

---

## License

[MIT](LICENSE). Individual plugins may carry additional attribution to original authors — see each plugin's frontmatter.
