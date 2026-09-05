"""Tests for the web build's staging and output collection.

The bug these guard is the one that broke the first CI run: pygbag writes
to <app_dir>/build/web, and the app dir is the staging directory, so the
output lands nested. Nothing about that is visible from a passing exit
code -- pygbag succeeds and the page is simply somewhere else.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import buildweb  # noqa: E402


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    """Point the build script at a temporary tree."""
    monkeypatch.setattr(buildweb, "ROOT", tmp_path)
    monkeypatch.setattr(buildweb, "STAGE", tmp_path / "build" / "stage")
    monkeypatch.setattr(buildweb, "OUTPUT", tmp_path / "build" / "web")
    return tmp_path


def fake_pygbag_output(sandbox):
    nested = buildweb.STAGE / "build" / "web"
    nested.mkdir(parents=True)
    (nested / "index.html").write_text("<html></html>")
    (nested / "lechery.apk").write_text("bundle")
    return nested


def test_output_is_collected_to_a_predictable_path(sandbox):
    """A build whose output location depends on invocation traps callers."""
    fake_pygbag_output(sandbox)
    output = buildweb.collect()

    assert output == buildweb.OUTPUT
    assert (output / "index.html").is_file()
    assert not (buildweb.STAGE / "build" / "web").exists()


def test_collect_raises_when_pygbag_produced_nothing(sandbox):
    """Silence here is what published a blank page."""
    with pytest.raises(FileNotFoundError):
        buildweb.collect()


def test_collect_replaces_a_previous_build(sandbox):
    fake_pygbag_output(sandbox)
    buildweb.collect()
    (buildweb.OUTPUT / "stale.txt").write_text("from an older build")

    fake_pygbag_output(sandbox)
    buildweb.collect()
    assert not (buildweb.OUTPUT / "stale.txt").exists()


def test_staging_ships_the_game_and_nothing_else(sandbox, monkeypatch):
    """Tests and caches in the bundle are download size for every player."""
    for name in ("lechery", "tests"):
        (sandbox / name).mkdir()
        (sandbox / name / "mod.py").write_text("")
    (sandbox / "lechery" / "__pycache__").mkdir()
    (sandbox / "lechery" / "__pycache__" / "mod.cpython-312.pyc").write_text("")
    (sandbox / ".pytest_cache").mkdir()
    (sandbox / "main.py").write_text("")

    staged = buildweb.stage()
    shipped = {p.relative_to(staged).as_posix() for p in staged.rglob("*") if p.is_file()}

    assert "main.py" in shipped
    assert "lechery/mod.py" in shipped
    assert not any("test" in path for path in shipped)
    assert not any("pycache" in path or ".pyc" in path for path in shipped)
