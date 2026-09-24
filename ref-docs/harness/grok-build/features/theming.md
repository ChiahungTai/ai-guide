#### Features

# Theming

Run `/theme` (alias `/t`) to open the theme picker with a live preview, `/theme <name>` to switch directly, or set it in `~/.grok/config.toml`:

```toml customLanguage="toml"
[ui]
theme = "tokyonight"
```

## Built-in themes

| Theme | Names | Truecolor required |
| ----- | ----- | ------------------ |
| GrokNight (default) | `groknight`, `dark` | No |
| GrokDay | `grokday`, `light`, `day` | No |
| TokyoNight | `tokyonight`, `tokyo` | Yes |
| RosePineMoon | `rosepine`, `rose-pine-moon` | Yes |
| OscuraMidnight | `oscura`, `oscura-midnight` | Yes |

On terminals without truecolor, themes are quantized to the available palette and the picker hides the truecolor-only entries. If colors look wrong, see [Terminal Support](/build/cli/terminal-support).

## Following the system appearance

Set `theme = "auto"` (alias `"system"`) to track your OS light/dark setting; changes apply within seconds, without a restart. Dark maps to GrokNight and light to GrokDay unless overridden:

```toml customLanguage="toml"
[ui]
theme = "auto"
auto_dark_theme = "tokyonight"
auto_light_theme = "grokday"
```

For a denser layout, `/compact-mode` reduces padding and persists the choice. Finer appearance controls (scrollback layout, block styling, animations) live in `~/.grok/pager.toml`.
