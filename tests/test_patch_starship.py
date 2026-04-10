from pathlib import Path

import pytest

from devskin.patch_starship import (
    DevskinError,
    apply_preset,
    backup_path_for,
    load_preset,
    preview_diff,
    rollback,
)


@pytest.fixture
def sample_config(tmp_path: Path) -> Path:
    fixture = Path("tests/fixtures/starship.sample.toml")
    config_path = tmp_path / "starship.toml"
    config_path.write_text(fixture.read_text(encoding="utf-8"), encoding="utf-8")
    return config_path


def test_preset_loads_correctly() -> None:
    preset = load_preset("sfc-modern")
    assert preset.name == "sfc-modern"
    assert "directory" in preset.module_styles


def test_preview_generates_diff_without_modifying_file(sample_config: Path) -> None:
    before = sample_config.read_text(encoding="utf-8")
    diff = preview_diff(sample_config, "sfc-modern")
    after = sample_config.read_text(encoding="utf-8")

    assert "--- " in diff and "+++ " in diff
    assert "directory" in diff
    assert before == after


def test_apply_creates_backup_and_writes_changes(sample_config: Path) -> None:
    original = sample_config.read_text(encoding="utf-8")

    config_path, backup_path = apply_preset(sample_config, "sfc-modern")

    assert config_path == sample_config
    assert backup_path == backup_path_for(sample_config)
    assert backup_path.read_text(encoding="utf-8") == original
    assert sample_config.read_text(encoding="utf-8") != original


def test_rollback_restores_original_content(sample_config: Path) -> None:
    original = sample_config.read_text(encoding="utf-8")
    apply_preset(sample_config, "sfc-modern")

    rollback(sample_config)

    assert sample_config.read_text(encoding="utf-8") == original


def test_rollback_without_backup_fails_cleanly(sample_config: Path) -> None:
    with pytest.raises(DevskinError, match="No backup found"):
        rollback(sample_config)


def test_missing_config_fails_cleanly(tmp_path: Path) -> None:
    missing = tmp_path / "missing.toml"
    with pytest.raises(DevskinError, match="Starship config not found"):
        preview_diff(missing, "sfc-modern")
