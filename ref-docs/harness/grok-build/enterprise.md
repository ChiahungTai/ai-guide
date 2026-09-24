# Enterprise Deployments

This page covers everything needed to deploy Grok Build in enterprise environments, including network requirements, configuration management, authentication options, security controls, and the data lifecycle.

## Network requirements

All connections use HTTPS (port 443).

### Required

These hosts are needed for core functionality:

| Host | Purpose |
| --- | --- |
| `cli-chat-proxy.grok.com` | Inference proxy, settings |
| `auth.x.ai` | OAuth2/OIDC authentication |

If using enterprise OIDC, also allow your IdP's domain (e.g., `login.microsoftonline.com`).

### Additional

These hosts support additional features and can be blocked without affecting core authentication and inference:

| Host | Purpose | Impact if blocked |
| --- | --- | --- |
| `api.x.ai` | xAI API (direct API-key path) | Only needed when using `api_key` auth instead of the inference proxy |
| `code.grok.com` | Remote session sync, sharing, WebSocket relay | Sessions stay local-only; share links unavailable |
| `assets.grok.com` | Profile images, UI assets | User avatars won't load; no functional impact |
| `x.ai` | CLI binary downloads via `curl \| bash` install script | Use `npm install -g @xai-official/grok` as an alternative that doesn't require this host |
| `storage.googleapis.com` | Fallback CDN for CLI binaries | Only needed if `x.ai` is unreachable during `curl \| bash` install |

The `x.ai` and `storage.googleapis.com` hosts are only needed for the shell-script installer and in-app `grok update`. If your environment uses npm for distribution (`npm install -g @xai-official/grok`), neither host is required.

### TLS

All connections use TLS 1.2 or TLS 1.3, enforced by `rustls` (no OpenSSL dependency). Root certificates are loaded from the OS trust store. There is no option to disable TLS. For TLS-inspecting proxies, install the proxy's CA certificate into the OS trust store.

### Proxy support

The CLI honors standard proxy environment variables (`HTTPS_PROXY`, `HTTP_PROXY`, `NO_PROXY`). The HTTP connection pool keeps idle connections open for 90 seconds by default (`GROK_POOL_IDLE_TIMEOUT_SECS`), and inference requests use SSE streaming where the per-chunk idle timeout defaults to 600 seconds. Set proxy idle timeouts to at least 10 minutes to avoid premature disconnects during long model responses.

## Configuration

Grok loads configuration from five layers, lowest to highest priority:

| Priority | Source | Purpose |
| --- | --- | --- |
| 1 (lowest) | `/etc/grok/managed_config.toml` | System-wide managed config |
| 2 | `~/.grok/managed_config.toml` | Per-user managed config |
| 3 | `~/.grok/config.toml` | User preferences |
| 4 | `~/.grok/requirements.toml` | User-level pinned settings |
| 5 (highest) | `/etc/grok/requirements.toml` | System-level pinned settings |

Settings in `requirements.toml` cannot be overridden by lower layers, remote settings, or user config — use it for compliance-critical policies. All layers support `[[version_overrides]]` for version-conditional patches and `$VAR` expansion.

### System-level policy for MDM and managed deployments

The highest-priority configuration layer is `/etc/grok/requirements.toml`. This is the recommended mechanism for organizations managing Grok at scale via Mobile Device Management (MDM), golden images, configuration management tools, or onboarding scripts.

**Common deployment patterns:**

* **MDM / endpoint management** — Push the TOML files directly into `/etc/grok/` on managed workstations.
* **Golden images / AMIs** — Bake the policy files into base images used for developer laptops or CI runners.

Values pinned in `requirements.toml` use a fail-closed "pin" mechanism: they cannot be overridden by user `config.toml`, environment variables, remote settings, or lower-priority layers. This makes `/etc/grok/requirements.toml` the authoritative source for compliance-critical policies such as disabling telemetry, enforcing sandbox profiles, restricting tools, or pinning specific feature flags.

### Claude Code compatibility (optional)

Organizations that already use Claude Code and have deployed its `managed-settings.json` file via MDM can continue to rely on that file. Grok reads a subset of policies from it (permission rules, MCP server allowlists, a few telemetry/feedback flags, and marketplace restrictions) for compatibility.

Grok's own `/etc/grok/requirements.toml` always takes precedence over the Claude `managed-settings.json` file. The Claude compatibility layer is only relevant for mixed Claude + Grok environments; pure Grok deployments should use `requirements.toml` + `config.toml`.

## Authentication

Grok Build supports four session authentication methods:

| Method | Trigger | Refreshable | Best for |
| --- | --- | --- | --- |
| Browser OIDC | `grok login` (default) | Yes | Interactive terminals with a browser |
| Device code | `grok login --device-auth` | Yes | SSH sessions, containers, headless hosts |
| External auth provider | `auth_provider_command` in config | Yes | Corporate IdPs, custom token brokers |
| API key | `XAI_API_KEY` env var or `model.api_key` in config | No | Scripts, CI/CD, headless automation |

When multiple credentials are available, Grok resolves them per model: `model.api_key` > `model.env_key` > active session token > `XAI_API_KEY`.

### Enterprise OIDC

Organizations with a corporate identity provider (Entra ID, Okta, Auth0, etc.) can configure Grok to authenticate directly against it:

```text
[auth.oidc]
issuer = "https://login.yourcompany.com"
client_id = "your-client-id"
```

Or via environment: `GROK_OIDC_ISSUER` and `GROK_OIDC_CLIENT_ID`. The flow uses PKCE and supports `refresh_token` grants for automatic renewal.

### External auth provider

Point Grok at an executable that produces a token on stdout:

```text
[auth]
auth_provider_command = "/usr/local/bin/your-auth-provider"
```

The command must print either a bare token string or JSON: `{"access_token": "...", "refresh_token": "...", "expires_in": 3600}` (`refresh_token` and `expires_in` are optional).

Grok runs the command on two contracts and sets `GROK_AUTH_EXPIRED` to tell them apart. It is `1` on a background refresh over a credential Grok already holds: nobody is watching, and the command has a few seconds before Grok kills it — so mint silently or exit non-zero, never wait for input. It is unset on a sign-in, where a user is attached, the command's stderr is shown to them, and there are up to 300 seconds for a browser round trip or a device code. A command that exits promptly on `GROK_AUTH_EXPIRED=1` rather than prompting is what makes the handover to the sign-in screen fast.

### API key

For CI/CD and headless automation, set the `XAI_API_KEY` environment variable — no config file needed:

```bash customLanguage="bash"
export XAI_API_KEY="xai-..."
grok -p "Review this diff" --output-format json --always-approve
```

On persistent developer workstations, you can instead bind a key to a specific model in `~/.grok/config.toml`:

```text
[model.grok-build]
api_key = "xai-..."

[models]
default = "grok-build"
```

See [Headless & Scripting](/build/cli/headless-scripting) for output formats and CLI flags.

### Device code

For environments without a browser (SSH, containers, cloud devboxes), device code login follows RFC 8628:

```bash customLanguage="bash"
grok login --device-auth
```

Grok prints a URL and a short user code. Complete login on any device with a browser.

### Restricting login methods

Two policies control how users authenticate. Set them in `requirements.toml` so a user `config.toml`, an environment variable, or a remote setting cannot override them.

`disable_api_key_auth` forces interactive IdP login. The `xai.api_key` method is no longer offered or accepted, and at request time a first-party xAI API key is replaced with the IdP session token, so a leftover `XAI_API_KEY` or per-model key cannot skip SSO. Third-party (BYOK) endpoints keep working, since their `base_url` is not on `x.ai`; restrict those through your own provider IAM.

```text
[grok_com_config]
disable_api_key_auth = true
```

`force_login_team_uuid` pins login to a team. The token's team principal must match the configured value, so a personal login or a login to the wrong team is rejected with an error and nothing is written to `auth.json`. You can set a single team UUID or a list, in which case any team in the list is allowed; an empty list rejects every login. Setting this also turns on `disable_api_key_auth`, because a bare API key does not carry team membership.

```text
[grok_com_config]
force_login_team_uuid = "<your-team-uuid>"
# Or allow several teams:
# force_login_team_uuid = ["<team-a-uuid>", "<team-b-uuid>"]
```

The value is the team's UUID, which the access token carries as its login principal. Enforcement applies every time a session is issued or reused, including cached tokens and silent refreshes. A session that no longer complies is cleared, so the user has to log in again. Run `grok inspect` to check which login policy loaded.

If you are migrating from Claude Code, `forceLoginMethod` maps to `disable_api_key_auth`, and `forceLoginOrgUUID` maps to `force_login_team_uuid`, which takes team UUIDs.

## Security controls

Day-to-day [permissions](/build/features/permissions) (modes, allow/deny rules) and [sandbox](/build/features/sandbox) profiles apply to individual machines as well as managed deployments. This section covers enterprise-only policy: pinning, headless modes, and locking always-approve off.

### Sandbox

Profiles, custom `sandbox.toml`, and how the sandbox relates to permissions are under [Sandbox](/build/features/sandbox). Pin a profile in `requirements.toml`:

```text
[sandbox]
profile = "workspace"
```

### Permissions

Ask, auto, and always-approve, plus CLI `--allow` / `--deny` and config rules, are under [Permissions](/build/features/permissions). For CI and headless runs, two additional modes matter:

| Mode | Behavior | Typical use |
| --- | --- | --- |
| `dontAsk` | Silently deny anything without an explicit allow rule | Headless, CI |
| `acceptEdits` | Auto-approve file edits; prompt for shell commands | Semi-automated workflows |

Example headless run:

```bash customLanguage="bash"
grok -p "Review the API changes" \
  --permission-mode dontAsk \
  --allow 'Bash(git *)' \
  --allow 'Bash(gh *)' \
  --allow 'Read' \
  --allow 'Grep' \
  --deny 'Bash(rm -rf *)' \
  --sandbox strict
```

**Locking bypass-permissions mode**

Set `disable_bypass_permissions_mode = true` under `[ui]` to turn always-approve (bypass-permissions) off across the deployment. This blocks every way to switch it back on: the `--yolo` and `--permission-mode bypassPermissions` flags, the in-session toggles (Ctrl+O, `/always-approve`, and the Shift+Tab mode cycle), client-supplied yolo settings, and catch-all `allow` rules such as `*` or `**`. Deny rules still apply, and behavior is unchanged when no lock is set.

```text
[ui]
disable_bypass_permissions_mode = true
```

To resist tampering, the lock is honored only from root-owned sources (`/etc/grok/requirements.toml` or the system layer), not from the user-writable `~/.grok/requirements.toml`. Claude Code's `managed-settings.json` `disableBypassPermissionsMode: "disable"` is **not** applied to grok's always-approve — grok honors that file's permission rules, MCP allowlists, and marketplace restrictions, but a developer's `--yolo` / `[ui] permission_mode` / runtime toggle still take effect. This keeps grok from inheriting a host's Claude Code lockdown (e.g. shared clusters hardened by AppSec); to disable always-approve in grok, set `disable_bypass_permissions_mode = true` in grok's own `requirements.toml`.

## Privacy & data lifecycle

### Data lifecycle

A session moves data through six phases:

1. **User input** — prompt and file content assembled locally.
2. **Transport** — sent over TLS 1.2/1.3 to the inference proxy.
3. **Inference** — the proxy forwards to the model. ZDR organizations route through a dedicated service identity that skips logging.
4. **Tool execution** — happens locally in the user's sandboxed environment.
5. **Response** — streams back over the same TLS connection.
6. **Session end** — no prompts, code, or responses are persisted at the inference layer for ZDR organizations. Local session history is stored in `~/.grok/`.

### Zero Data Retention

ZDR is enforced at the team level. When enabled for a team or enterprise, zero data retention occurs when using Grok Build. Video tools under ZDR require user-supplied output storage — see [Video Output Storage under ZDR](/build/settings/zdr-video-storage).
