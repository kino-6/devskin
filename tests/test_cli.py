from pathlib import Path

from devskin import cli


def test_list_contains_sfc_modern(capsys) -> None:
    rc = cli.main(["list"])
    out = capsys.readouterr().out

    assert rc == 0
    assert "sfc-modern" in out


def test_cli_missing_config_fails(monkeypatch, tmp_path: Path, capsys) -> None:
    monkeypatch.setattr(cli, "DEFAULT_CONFIG_PATH", tmp_path / "missing.toml")

    rc = cli.main(["preview", "sfc-modern"])
    captured = capsys.readouterr()

    assert rc == 1
    assert "Error:" in captured.err
