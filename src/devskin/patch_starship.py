from __future__ import annotations

import copy
import difflib
from importlib import resources
from pathlib import Path
import tomllib

from devskin.models import StarshipPreset

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "starship.toml"


class DevskinError(Exception):
    """Base exception for user-facing CLI errors."""


def backup_path_for(config_path: Path) -> Path:
    return config_path.with_name(config_path.name + ".devskin.bak")


def available_presets() -> list[str]:
    preset_dir = resources.files("devskin").joinpath("presets")
    return sorted(path.name.removesuffix(".yaml") for path in preset_dir.iterdir() if path.suffix == ".yaml")


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    return value


def _parse_simple_yaml(text: str, preset_name: str) -> dict:
    data: dict[str, object] = {}
    current_map: dict[str, str] | None = None

    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue

        indent = len(line) - len(line.lstrip(" "))
        if indent not in {0, 2}:
            raise DevskinError(f"Preset '{preset_name}' malformed YAML at line {line_no}: unsupported indentation")

        if indent == 0:
            if ":" not in line:
                raise DevskinError(f"Preset '{preset_name}' malformed YAML at line {line_no}: missing ':'")
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value == "":
                if key not in {"top_level", "module_styles"}:
                    raise DevskinError(
                        f"Preset '{preset_name}' malformed YAML at line {line_no}: only maps are allowed here"
                    )
                nested: dict[str, str] = {}
                data[key] = nested
                current_map = nested
            else:
                current_map = None
                data[key] = _strip_quotes(value)
        else:
            if current_map is None:
                raise DevskinError(f"Preset '{preset_name}' malformed YAML at line {line_no}: unexpected nested key")
            entry = line.strip()
            if ":" not in entry:
                raise DevskinError(f"Preset '{preset_name}' malformed YAML at line {line_no}: missing ':'")
            key, value = entry.split(":", 1)
            current_map[key.strip()] = _strip_quotes(value)

    return data


def load_preset(name: str) -> StarshipPreset:
    preset_path = resources.files("devskin").joinpath("presets", f"{name}.yaml")
    if not preset_path.is_file():
        raise DevskinError(f"Preset '{name}' not found. Run 'devskin list' to see available presets.")

    data = _parse_simple_yaml(preset_path.read_text(encoding="utf-8"), name)

    top_level_raw = data.get("top_level", {})
    top_level: dict[str, str | bool] = {}
    for key, value in dict(top_level_raw).items():
        if value == "true":
            top_level[key] = True
        elif value == "false":
            top_level[key] = False
        else:
            top_level[key] = value

    return StarshipPreset(
        name=name,
        description=str(data.get("description", "")),
        module_styles=dict(data.get("module_styles", {})),
        top_level=top_level,  # type: ignore[arg-type]
        python_venv_prompt=data.get("python_venv_prompt"),
    )


def read_starship_config(config_path: Path) -> dict:
    if not config_path.exists():
        raise DevskinError(
            f"Starship config not found at {config_path}. Create it first, then run devskin again."
        )
    try:
        return tomllib.loads(config_path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise DevskinError(f"Starship config at {config_path} is malformed TOML: {exc}") from exc


def apply_preset_to_config(config: dict, preset: StarshipPreset) -> dict:
    patched = copy.deepcopy(config)

    for key, value in preset.top_level.items():
        patched[key] = value

    for module_name, style in preset.module_styles.items():
        module_cfg = patched.get(module_name)
        if not isinstance(module_cfg, dict):
            module_cfg = {}
            patched[module_name] = module_cfg
        module_cfg["style"] = style

    if preset.python_venv_prompt:
        python_cfg = patched.get("python")
        if not isinstance(python_cfg, dict):
            python_cfg = {}
            patched["python"] = python_cfg
        python_cfg.setdefault("format", preset.python_venv_prompt)

    return patched


def _toml_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def render_toml(config: dict) -> str:
    lines: list[str] = []
    for key, value in config.items():
        if not isinstance(value, dict):
            lines.append(f"{key} = {_toml_value(value)}")
    if lines:
        lines.append("")

    for section, section_values in config.items():
        if not isinstance(section_values, dict):
            continue
        lines.append(f"[{section}]")
        for key, value in section_values.items():
            lines.append(f"{key} = {_toml_value(value)}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def preview_diff(config_path: Path, preset_name: str) -> str:
    current = read_starship_config(config_path)
    preset = load_preset(preset_name)
    patched = apply_preset_to_config(current, preset)

    before = render_toml(current).splitlines(keepends=True)
    after = render_toml(patched).splitlines(keepends=True)
    return "".join(
        difflib.unified_diff(
            before,
            after,
            fromfile=str(config_path),
            tofile=f"{config_path} ({preset_name})",
        )
    )


def apply_preset(config_path: Path, preset_name: str) -> tuple[Path, Path]:
    current = read_starship_config(config_path)
    preset = load_preset(preset_name)
    patched = apply_preset_to_config(current, preset)

    backup_path = backup_path_for(config_path)
    backup_path.write_text(config_path.read_text(encoding="utf-8"), encoding="utf-8")
    config_path.write_text(render_toml(patched), encoding="utf-8")
    return config_path, backup_path


def rollback(config_path: Path) -> Path:
    backup_path = backup_path_for(config_path)
    if not backup_path.exists():
        raise DevskinError(
            f"No backup found at {backup_path}. Run 'devskin apply <preset>' before rollback."
        )
    config_path.write_text(backup_path.read_text(encoding="utf-8"), encoding="utf-8")
    return config_path
