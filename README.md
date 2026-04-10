# devskin

Apply modern-retro presets to developer tools with minimal, reversible patches.

## Concept

`devskin` is intentionally **not** a strict retro emulator for your prompt. Instead, it aims for a practical modern look with a subtle nostalgic mood. The focus is readability and long-session ergonomics first, then style.

## Why “modern retro”

Classic retro replicas often lean on pixel fonts, heavy effects, and novelty symbols that reduce daily usability. `devskin` keeps your Starship layout mostly intact and adjusts color/style conservatively, so the prompt remains familiar and copy/paste-friendly.

## MVP scope

This MVP supports:
- Ubuntu on WSL
- Starship only
- `~/.config/starship.toml` only
- Preset: `sfc-modern`

Commands:
- `devskin list`
- `devskin preview sfc-modern`
- `devskin apply sfc-modern`
- `devskin rollback`

## Installation (uv)

```bash
uv sync
```

Run the CLI with:

```bash
uv run devskin list
```

## CLI usage

```bash
uv run devskin list
uv run devskin preview sfc-modern
uv run devskin apply sfc-modern
uv run devskin rollback
```

### Behavior

- `list`: shows available presets.
- `preview`: prints a unified diff of changes and **does not write files**.
- `apply`: always writes a backup first, then writes the patched config.
- `rollback`: restores from the backup.

## Backup and rollback

`devskin` uses a deterministic backup path next to the original config:

- Config: `~/.config/starship.toml`
- Backup: `~/.config/starship.toml.devskin.bak`

If the backup already exists, `apply` overwrites it with the current config before writing new changes. This keeps rollback behavior predictable.

## Limitations

- No VS Code integration yet
- No Windows Terminal integration yet
- No tmux integration
- No pixel-font/CRT simulation
- Single target and single preset in this MVP

## Future work

- VS Code support
- Windows Terminal support
- Additional presets
- Intensity levels (`subtle`, `balanced`, `expressive`)
