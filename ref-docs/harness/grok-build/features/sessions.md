#### Features

# Sessions

Grok saves every conversation to disk automatically — prompts, responses, tool calls, and file snapshots — under `~/.grok/sessions/`, keyed by working directory. Sessions work the same in the TUI, headless mode, and over ACP.

## Resuming

In the TUI, `/resume` opens a picker of recent sessions for the current workspace; the welcome screen lists them too. From the command line:

```bash customLanguage="bash"
grok --resume <session-id>   # a specific session
grok --resume                # the most recent for this directory
grok -c                      # shorthand: continue the most recent
```

In headless mode, read the session ID back from JSON output and pass it to `-r` to build multi-step automations:

```bash customLanguage="bash"
grok -p "Start the refactor" --output-format json | jq -r '.sessionId'
```

`-s, --session-id` names a new session with a UUID you supply; it does not resume existing ones. To branch a resumed session instead of continuing it, add `--fork-session`.

## Forking

`/fork [directive]` branches the current session into a peer that starts from a copy of the conversation. Pass `--worktree` or `--no-worktree` to choose whether the fork runs in an isolated copy of the repository, so parallel sessions do not overwrite each other's files — see [Worktrees](/build/features/worktrees).

## Rewinding

`/rewind` (or `Esc Esc` while idle) lists a rewind point per prompt. Selecting one restores all files to their state at that point and truncates the conversation to match. Rewind modifies files on disk — reverted changes are lost unless committed to git.

## Compacting

`/compact [context]` compresses the conversation history to reclaim context window, with optional instructions about what to preserve. Grok also auto-compacts as the context window fills; check usage with `/context` or `/session-info`.

## Todos

For multi-step work, the agent keeps a structured todo list so you can see what is planned, what is in progress, and what is done. Items use statuses pending, in progress, completed, and cancelled (when a step is dropped).

On the agent screen, press `Ctrl+T` to view the todo pane. The list is part of the session: resume the same session and the todos return with their last statuses.

Todos are separate from [background tasks](/build/features/background-tasks), which track long-running commands and monitors.

## Housekeeping

| Command | What it does |
| ------- | ------------ |
| `/sessions` | Switch, rename, or close active sessions |
| `/rename <title>` | Rename the current session (alias `/title`) |
| `grok sessions list` | List recent sessions for this directory |
| `grok sessions search <query>` | Search session titles and prompts |
| `grok sessions delete <id>` | Permanently delete a session |
| `grok export <id> [file]` | Export a transcript as Markdown (`--clipboard` to copy) |
