#### Features

# Sandbox

The sandbox limits what the agent process and its children can read, write, and reach on the network (Landlock on Linux, Seatbelt on macOS). Off by default. Permissions gate whether a tool call runs; the sandbox limits what an approved call can do — see [Permissions](/build/features/permissions).

## Profiles

| Profile | Filesystem read | Filesystem write | Child network | Use case |
| --- | --- | --- | --- | --- |
| `off` | Unrestricted | Unrestricted | Allowed | No sandbox (default) |
| `workspace` | Everywhere | CWD, `~/.grok/`, temp | Allowed | Normal development |
| `devbox` | Everywhere | Top-level dirs except `/data` | Allowed | Cloud devbox environments |
| `read-only` | Everywhere | `~/.grok/` and temp only | Blocked | Code review, auditing |
| `strict` | CWD and system paths | CWD, `~/.grok/`, temp | Blocked | Untrusted repositories |

| Limitation | Detail |
| --- | --- |
| Child network | Enforced on Linux only; no-op on macOS for `read-only` / `strict` |
| Credentials | Built-ins do not permanently protect paths such as `~/.ssh`; use a custom `deny` list |
| `~/.grok/` | Stays writable under sandboxed profiles so sessions can persist |
| In-process network | Model API and web tools are not blocked by child-network settings |

## Enable a profile

| Mechanism | Example |
| --- | --- |
| CLI | `grok --sandbox workspace` |
| Config | `[sandbox] profile = "workspace"` in `~/.grok/config.toml` |
| Env | `GROK_SANDBOX=workspace` |
| Managed pin | `requirements.toml` (can override CLI) — [Enterprise](/build/enterprise#sandbox) |

## Custom profiles

Define named profiles in `~/.grok/sandbox.toml` or project `.grok/sandbox.toml`:

```text
[profiles.my-profile]
extends = "workspace"
restrict_network = true
deny = ["/secrets", "**/.env", "**/*.pem"]
```

Select with `--sandbox my-profile` or `[sandbox] profile`. Built-in names cannot be redefined for selection. Field details: [Settings Reference](/build/settings/reference).

For untrusted trees, pair a strict profile with narrow [permission](/build/features/permissions) allows (or headless `dontAsk`).
