# Keyboard Shortcuts

Press `Ctrl+.` (or `Ctrl+X` on Windows and in terminals without the Kitty keyboard protocol) to open this list inside the TUI; entries that do not apply in the current context are dimmed.

Some chords differ by terminal; see [Terminal differences](#terminal-differences).

## Essentials

| Keys | Action |
| ---- | ------ |
| `Enter` | Send the prompt |
| `Tab` | Move focus between prompt and scrollback |
| `Esc` | Cancel the running turn |
| `Esc Esc` | Clear the prompt, or open rewind when it is empty |
| `Ctrl+C` | Cancel turn |
| `Shift+Tab` | Cycle mode (Normal / Plan / Auto when available / Always-approve) |
| `Ctrl+P` or `?` | Command palette |
| `Ctrl+.` / `Ctrl+X` | Keyboard shortcuts |
| `F2` or `Ctrl+,` | Settings |
| `Ctrl+Q` / `Ctrl+D` | Quit (press twice) |

## Input

| Keys | Action |
| ---- | ------ |
| `Ctrl+Enter` or `Ctrl+I` | Interject while a turn is running |
| `Shift+Enter` | Newline — or send, in multiline mode (`Alt+Enter` where `Shift+Enter` is unsupported) |
| `Ctrl+M` | Toggle multiline input |
| `Ctrl+R` | Search prompt history |
| `!` | Shell mode, on an empty prompt |

## Scrollback

Focus the scrollback with `Tab`, then navigate. Bare-letter keys require vim mode (`/vim-mode`, or `vim_mode = true` under `[ui]` in `config.toml`); the arrow-key equivalents always work.

| Keys | Action |
| ---- | ------ |
| `j` / `↓`, `k` / `↑` | Select next / previous entry |
| `Shift+L` / `Shift+→`, `Shift+H` / `Shift+←` | Next / previous turn |
| `Shift+J`, `Shift+K` | Next / previous response |
| `g`, `Shift+G` | Go to top / bottom |
| `Ctrl+U`, `Ctrl+D` | Scroll half page up / down |
| `Page Up`, `Page Down` | Scroll one page up / down |
| `h` / `←`, `l` / `→` | Collapse / expand the selected entry |
| `e`, `Shift+E` | Expand or collapse one entry / all entries |
| `Ctrl+E` | Toggle all thinking blocks |
| `r` | Toggle raw markdown |
| `y`, `Shift+Y` | Copy content / copy command or path |
| `Enter` or `Ctrl+F` | Open the selected block in the fullscreen viewer |
| `/` | Search scrollback (vim mode) |
| `x` | Kill the selected background task |

## Panels and session

| Keys | Action |
| ---- | ------ |
| `Ctrl+T` | Toggle the [todo pane](/build/features/sessions#todos) (agent screen) |
| `Ctrl+B` | Send the running command to the background |
| `Ctrl+;` or `Ctrl+'` | Toggle prompt queue |
| `Ctrl+S` | Open sessions |
| `Ctrl+L` | Open extensions |
| `Ctrl+G` | Toggle the [tasks pane](/build/features/background-tasks) |
| `Ctrl+O` | Toggle always-approve |
| `Ctrl+N` | New session (press twice) |
| `Ctrl+M` | Pick model, when the prompt is not focused |
| `Ctrl+\` | Open the [Agent Dashboard](/build/features/dashboard) |

## Terminal differences

* VS Code-family terminals (VS Code, Cursor, Windsurf, Zed): quit is `Ctrl+D` only, interject is `Ctrl+L`, half-page scroll is `Shift+D`, and `Ctrl+L` does not open extensions (use `/plugins`). Use `Alt+Enter` for newlines.
* Apple Terminal: `Ctrl+O` also interjects.
* WezTerm needs `enable_kitty_keyboard = true` for `Ctrl+Enter` and `Shift+Enter`.

See [Terminal Support](/build/cli/terminal-support) for fixes and diagnostics.
