#### Features

# MCP Servers

MCP ([Model Context Protocol](https://modelcontextprotocol.io)) servers expose external tools to Grok. Once configured, their tools are available alongside the built-in ones, namespaced as `<server>__<tool>`.

## Adding a server

The fastest way is the `grok mcp` command:

```bash customLanguage="bash"
# Local stdio server; everything after -- is the server command
grok mcp add filesystem -- npx -y @modelcontextprotocol/server-filesystem /path/to/dir

# Remote server over HTTP (OAuth handled automatically)
grok mcp add --transport http linear https://mcp.linear.app/mcp

# Remote server with a static auth header (--header is repeatable)
grok mcp add --transport http api https://mcp.example.com/mcp --header "Authorization: Bearer ${API_TOKEN}"
```

`grok mcp list` shows configured servers, `grok mcp remove <name>` deletes one, and `grok mcp doctor [name]` diagnoses configuration and connectivity. `list` and `doctor` take `--json` for machine-readable output.

Servers can also be declared directly in `~/.grok/config.toml`:

```toml customLanguage="toml"
[mcp_servers.filesystem]
command = "npx"
args = ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/dir"]
env = { API_KEY = "${MY_API_KEY}" }   # ${VAR} expands at load time
startup_timeout_sec = 30              # default 30
tool_timeout_sec = 6000               # default 6000

[mcp_servers.linear]
url = "https://mcp.linear.app/mcp"
headers = { "x-mcp-session-id" = "{{session_id}}" }
```

Grok expands `${VAR}` (and `${VAR:-default}`) in `url`, `command`, `args`, `env`, and `headers`, so secrets can stay in the environment. Servers that require OAuth trigger a browser flow on first use; tokens are stored under `~/.grok/mcp_credentials.json`.

## Project scope

Pass `--scope project` to `grok mcp add` (it writes `.grok/config.toml` in the current directory) to define servers that ship with the repo. When loading, Grok walks from the current directory up to the git root reading each `.grok/config.toml`, and a project server with the same name as a user one replaces it entirely.

## In the TUI

`/mcps` opens the MCP tab of the extensions modal: toggle a server with `Space`, refresh after config edits with `r`, authenticate OAuth servers with `i`, and add or remove with `a` and `x`.

## Compatibility

Grok also loads MCP configurations from `~/.claude.json`, `.cursor/mcp.json`, and project `.mcp.json` files, merged below `config.toml` in priority. Disable a vendor with `[compat.claude] mcps = false` or `[compat.cursor] mcps = false`. `grok inspect` shows every loaded server and its origin.

## Troubleshooting

`grok mcp doctor` is the first stop. For stdio servers that start but fail to connect, Grok captures stderr to `~/.grok/logs/mcp/<server>.stderr.log`. Cold-start `npx` servers that download packages on first launch may need a higher `startup_timeout_sec`.
