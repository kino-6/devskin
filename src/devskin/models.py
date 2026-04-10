from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class StarshipPreset:
    name: str
    description: str
    module_styles: dict[str, str]
    top_level: dict[str, str | bool]
    python_venv_prompt: str | None = None
