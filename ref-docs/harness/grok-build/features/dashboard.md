#### Features

# Agent Dashboard

The dashboard is a fullscreen overview of every session: which agents need input, which are working, and which are done. Open it with `Ctrl+\`, the `/dashboard` command, or `grok dashboard` from the shell.

Rows are grouped by state — Needs input, Working, Idle, Inactive, Completed, Failed — and update live. Press `Ctrl+G` to group by directory instead.

## Working with agents

Selecting a row opens a peek panel showing the agent's latest activity. Type to reply: an idle agent receives the message immediately, a busy one queues it. Permission prompts and questions can be answered inline with the number keys. Press `Enter` to attach to the session in a full details view; `Ctrl+\` returns to the dashboard, and `Ctrl+[` / `Ctrl+]` cycle between sessions.

The input bar at the bottom dispatches prompts to new sessions. `Ctrl+L` changes the working directory for new agents, and `Ctrl+W` toggles whether they start in a [git worktree](/build/features/worktrees).

## Keys

| Keys | Action |
| ---- | ------ |
| `↑`/`↓` | Select row |
| `Enter` | Open the selected session |
| `Ctrl+/` | Search — `a:<name>` by agent, `s:<state>` by state, or plain text |
| `Ctrl+T` | Pin / unpin agent |
| `Ctrl+R` | Rename agent |
| `Ctrl+X` | Stop / close agent (press twice) |
| `Shift+↑`/`Shift+↓` | Reorder pinned agents |
| `Esc` | Close peek, then filter, then the dashboard |

Grouping and pins persist under `[dashboard]` in `~/.grok/config.toml`. Set `enabled = false` there, or `GROK_AGENT_DASHBOARD=0`, to disable the feature.
