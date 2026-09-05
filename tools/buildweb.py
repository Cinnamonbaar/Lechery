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

#: pygbag writes its output to <app_dir>/build/web, and the app dir is the
#: staging directory -- so the result lands nested. It is moved up to this
#: predictable path afterwards, since a build whose output location depends
#: on how it was invoked is a trap for every caller.
OUTPUT = ROOT / "build" / "web"

#: Everything the game needs at runtime, and nothing else.
SHIPPED = ["main.py", "lechery", "assets"]

#: Canvas size, passed to pygbag so the page and main.py's set_mode agree.
#: Left to differ, the game lays itself out against a surface it did not
#: get, which looks exactly like a crash.
CANVAS = (1280, 760)

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


def collect() -> Path:
    """Move pygbag's nested output up to build/web. Returns that path."""
    produced = STAGE / "build" / "web"
    if not produced.is_dir():
        raise FileNotFoundError(f"pygbag produced nothing at {produced}")

    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    shutil.move(str(produced), str(OUTPUT))
    return OUTPUT


def main(argv: list[str]) -> int:
    staged = stage()
    files = sum(1 for _ in staged.rglob("*") if _.is_file())
    size = sum(f.stat().st_size for f in staged.rglob("*") if f.is_file())
    print(f"staged {files} files ({size / 1024:.0f} KiB) in {staged}")

    serving = "--serve" in argv
    command = [
        sys.executable,
        "-m",
        "pygbag",
        "--title",
        "Lechery",
        # No "click to start" gate. It exists so a browser will let the
        # audio context open on a user gesture; with no audio yet it is a
        # pointless step between the player and the game.
        "--ume_block",
        "0",
        "--width",
        str(CANVAS[0]),
        "--height",
        str(CANVAS[1]),
    ]
    if not serving:
        command.append("--build")
    command.append(str(staged))

    print(" ".join(command))
    code = subprocess.call(command)
    if code or serving:
        # Serving leaves pygbag's own server pointed at the nested path, so
        # there is nothing to move and nothing to check.
        return code

    try:
        output = collect()
    except FileNotFoundError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    page = output / "index.html"
    if not page.is_file():
        # pygbag can finish successfully having fetched nothing useful, so
        # the page is checked here rather than trusting the exit code.
        print(f"error: no index.html in {output}", file=sys.stderr)
        return 1

    total = sum(f.stat().st_size for f in output.rglob("*") if f.is_file())
    print(f"built {output} ({total / 1024:.0f} KiB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
