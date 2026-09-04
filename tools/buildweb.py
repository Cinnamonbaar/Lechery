"""Build the web version, shipping only what the game needs.

pygbag packages the whole directory it is pointed at and has no exclude
flag, so aiming it at the repo root ships the test suite and pytest's cache
to every player. Download size is the browser's tax, so this stages the
shipping files into a clean directory first and builds that.

    python tools/buildweb.py            # build only
    python tools/buildweb.py --serve    # build and serve on localhost:8000
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STAGE = ROOT / "build" / "stage"

#: Everything the game needs at runtime, and nothing else.
SHIPPED = ["main.py", "lechery", "assets"]

#: Dropped from the staged copy: caches and bytecode add weight and nothing
#: else, and they are regenerated on the player's machine anyway.
JUNK = shutil.ignore_patterns("__pycache__", "*.pyc", ".*")


def stage() -> Path:
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)

    for name in SHIPPED:
        source = ROOT / name
        if not source.exists():
            continue
        if source.is_dir():
            shutil.copytree(source, STAGE / name, ignore=JUNK)
        else:
            shutil.copy2(source, STAGE / name)
    return STAGE


def main(argv: list[str]) -> int:
    staged = stage()
    files = sum(1 for _ in staged.rglob("*") if _.is_file())
    size = sum(f.stat().st_size for f in staged.rglob("*") if f.is_file())
    print(f"staged {files} files ({size / 1024:.0f} KiB) in {staged}")

    command = [sys.executable, "-m", "pygbag", "--title", "Lechery"]
    if "--serve" not in argv:
        command.append("--build")
    command.append(str(staged))

    print(" ".join(command))
    return subprocess.call(command)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
