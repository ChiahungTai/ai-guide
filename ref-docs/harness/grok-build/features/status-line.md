#### Features

# Status Line

The status line is an optional row that shows live session values. It can show the model, context-window usage, cost, or the output of a script you provide.

In the full-screen view the row sits above the shortcuts bar. In minimal mode it sits under the prompt info row. The row is hidden on the welcome screen and while a fullscreen subagent view is open. The status line is off by default.

## Configure the status line

Add a `[ui.status_line]` section to `~/.grok/config.toml`. Restart Grok.

The `type` key selects the mode. `builtin` shows values Grok renders. `command` runs your script. `disabled` shows nothing.

Grok reads this section only from your own configuration, or from configuration your administrator manages. A cloned repository cannot set a status line.

### Built-in items

Items appear in the order you list them. Long values shorten with an ellipsis.

```toml customLanguage="toml"
[ui.status_line]
type = "builtin"
items = ["cwd", "model", "context"]   # default when omitted
```

The default set renders as, for example, `my-project │ Grok 4.5 │ 12% ctx`.

| Item | Description |
| --- | --- |
| `cwd` | The name of the current directory. |
| `model` | The model's display name. |
| `context` | Context-window usage, as a percentage. The value turns amber at the auto-compaction threshold, or at 80 percent when the agent reports none. |
| `cost` | Cost for this Grok process. Hidden below $0.005. A resumed session counts from the resume. |
| `turn-timer` | Elapsed time of the current turn, after one second. |
| `session-name` | The session name, if set. |

### A command script

Set `type` to `command`. Point `command` at a script path or an inline shell command. A leading `~/` expands to your home directory.

These recipes are POSIX shell. They are tested on macOS and Linux. A `command` status line is untested on Windows.

1. Save `~/.grok/statusline.sh`. The script reads JSON from standard input and prints a line. This example uses [`jq`](https://jqlang.org/):

   ```bash customLanguage="bash"
   #!/bin/sh
   payload=$(cat)
   model=$(printf '%s' "$payload" | jq -r '.model.display_name // "?"')
   ctx=$(printf '%s' "$payload" | jq -r '.context_window.used_percentage // 0')
   printf '%s │ %s%% ctx\n' "$model" "$ctx"
   ```

2. Run `chmod +x ~/.grok/statusline.sh`. A file without the execute bit shows `[status line: could not start the script: …]`.

3. Set the command:

   ```toml customLanguage="toml"
   [ui.status_line]
   type = "command"
   command = "~/.grok/statusline.sh"
   ```

4. Restart Grok. The row appears once a session is active.

The script receives one JSON object on standard input. Common fields are `model.display_name`, `context_window.used_percentage`, `workspace.branch`, and `cwd`. Grok omits a field it cannot determine. Guard missing keys (`// "?"` in jq).

An idle session does not re-run the script. Set `refresh_interval` (seconds) on a `command` row to also run it on a timer. The key does nothing under `builtin` or `disabled`. `grok inspect` still reports it there.

Test the script before you configure it:

```bash customLanguage="bash"
~/.grok/statusline.sh <<'JSON'
{"workspace": {"current_dir": "/tmp/demo", "branch": "main"}, "model": {"display_name": "Grok 4.5"}}
JSON
```

### Disable the status line

Set `type` to `disabled`. `off`, `none`, and `hidden` mean the same. Removing the `[ui.status_line]` section also disables the row.

## Troubleshooting

Grok reads `[ui.status_line]` at startup. Restart Grok after you edit `config.toml`.

`grok inspect` lists problems in the section. A row that begins with `[ui.status_line]` names the key Grok could not read.

A script that prints nothing and fails shows `[status line: exit N]`. A timeout shows `[status line: timed out]`. A kill shows `[status line: killed by signal]`. A spawn failure, including a missing execute bit, shows `[status line: could not start the script: …]`. Standard error is never shown. Run Grok with `--debug` to read it.
