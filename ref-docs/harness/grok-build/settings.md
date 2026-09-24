# Settings

Grok Build offers a variety of configurations to suit your needs, many of which are made directly available in the TUI under `/settings`.

Settings are persisted under `~/.grok/config.toml` (on Windows, `%USERPROFILE%\.grok\config.toml`). To configure the default home directory, you can set `$GROK_HOME`.

For MCP servers, see [MCP Servers](/build/features/mcp-servers). For marketplaces, skills, and plugins, see [Skills, Plugins, and Marketplaces](/build/features/skills-plugins-marketplaces); for hooks, see [Hooks](/build/features/hooks).

## Scopes

| Scope | Path | Use for |
| --- | --- | --- |
| Environment | `GROK_*` (and related) variables | Session / CI overrides |
| User | `~/.grok/config.toml` (or `$GROK_HOME/config.toml`) | Personal defaults |
| Project | `.grok/config.toml` in the repo | Repo-shared MCP, plugins, and permission rules |
| Managed | `~/.grok/managed_config.toml`, `/etc/grok/managed_config.toml` | Enterprise-served defaults |
| Requirements | `~/.grok/requirements.toml`, `/etc/grok/requirements.toml` | Policy pins |

Project configs are limited to MCP servers, plugins, and permission rules, not full user configs. For scope merge order and managed deployments, see [Enterprise Deployments](/build/enterprise#configuration). Day-to-day [permissions](/build/features/permissions) and [sandbox](/build/features/sandbox) apply to individual use; managed locks and headless modes are under Enterprise.

## Verification

To confirm which configs are picked up by Grok Build, run the following command:

```bash customLanguage="bash"
grok inspect
```

## Example `config.toml`

Copy into `$GROK_HOME/config.toml`, or `~/.grok/config.toml` when `GROK_HOME` is unset. Prefer `/settings` for UI, notifications, and other in-app options.

```toml customLanguage="toml"
[models]
default = "grok-build"                       # recommended for coding / agent sessions
web_search = "grok-4.7"                      # model used by client-side web_search tool

[model."grok-4.7"]
model = "grok-4.7"                           # id sent to the API
base_url = "https://api.x.ai/v1"             # provider endpoint
name = "Grok 4.7"                            # shown in model picker
description = "Grok 4.7 from xAI"
env_key = "XAI_API_KEY"                      # env var holding the API key
api_backend = "responses"                    # chat_completions | responses | messages
temperature = 0.7
top_p = 0.95
max_completion_tokens = 8192
context_window = 500000
extra_headers = { "x-api-key" = "xai-..." }
supports_backend_search = true               # if the endpoint supports Grok-hosted server-side search tools

[mcp_servers.filesystem]
command = "npx"
args = ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/directory"]
enabled = true
startup_timeout_sec = 30
tool_timeout_sec = 6000

[mcp_servers.linear]
url = "https://mcp.linear.app/mcp"
headers = { "Authorization" = "Bearer ${LINEAR_API_KEY}", "x-mcp-session-id" = "{{session_id}}" }

[ui]
compact_mode = false
theme = "auto"
show_thinking_blocks = true
```

## TOML Values

For the full list of `config.toml` keys, see [TOML Values](/build/settings/reference#toml-values).

## Environment variables

For the full list of environment variables, see [Environment variables](/build/settings/reference#environment-variables).
