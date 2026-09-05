"""Entry point, for the desktop and for the browser.

The loop is async because pygbag requires it: a WASM build shares the
browser's single thread, so a frame that never yields locks the tab. The
`await asyncio.sleep(0)` is that yield.

The shape of this file is part of pygbag's build contract, and three things
about it are deliberate:

  Imports are guarded, because an import failure happens before any of our
  error handling could otherwise run, and in a browser that is a blank
  canvas with no explanation.

  Nothing raises SystemExit at module scope. pygbag executes this module as
  __main__, and a SystemExit propagating out of it ends the app rather than
  the frame.

  The loop is entered through a coroutine that never assumes it owns the
  event loop, because in a browser it does not.

    python main.py 1234        # desktop, replaying seed 1234
    python tools/buildweb.py   # build the web version
"""

from __future__ import annotations

import asyncio
import sys
import traceback

#: Recorded rather than raised: if importing the game fails, this file must
#: still load far enough to be able to say so.
IMPORT_ERROR: str | None = None

try:
    import pygame

    from lechery.platform import is_web
    from lechery.settings import Settings
    from lechery.ui.app import App
except Exception:  # pragma: no cover - exercised only when an import breaks
    IMPORT_ERROR = traceback.format_exc()

#: Desktop window size, and the fallback when the browser will not say.
SIZE = (1280, 760)
FPS = 60

#: How often to re-check the browser viewport, in frames. A phone rotating
#: is the case that matters, and it does not need to be caught instantly.
VIEWPORT_POLL = 30

#: Never advance the world by more than this in one frame. A browser tab in
#: the background stops painting, so the first frame after it returns can
#: carry seconds of elapsed time -- enough to move the player through a wall.
MAX_STEP = 1 / 30

CRASH_BG = (38, 16, 18)
CRASH_TEXT = (240, 220, 216)


def parse_seed(argv: list[str]) -> int | None:
    """The seed, if one was given and it is actually a number.

    Defensive because argv is not ours in a web build: pygbag invokes the
    module with whatever it likes, and int() on that would raise before the
    first frame.
    """
    for argument in argv:
        if argument.lstrip("-").isdigit():
            return int(argument.lstrip("-"))
    return None


def browser_viewport() -> tuple[int, int] | None:
    """The page's usable size, in CSS pixels, or None outside a browser.

    Without this the canvas is whatever size the build asked for, and a
    phone scales that into a letterboxed strip -- and worse, the game
    measures the canvas rather than the screen, so it lays out the desktop
    three-pane view on a phone. Reading the real viewport is what makes the
    compact layout trigger where it should.
    """
    try:
        import platform as runtime  # pygbag replaces this with its own

        window = getattr(runtime, "window", None)
        if window is None:
            return None

        width = int(window.innerWidth)
        height = int(window.innerHeight)
        if width > 0 and height > 0:
            return (width, height)
    except Exception:
        pass
    return None


# -- reporting a failure the player can actually see ----------------------


def report_to_page(text: str) -> bool:
    """Write a failure into the web page itself. Returns whether it worked.

    The canvas is useless for reporting a failure that happened before the
    canvas existed, and a phone has no console. pygbag exposes the browser
    window, so the document is the one surface guaranteed to be there.
    """
    try:
        import platform as runtime  # pygbag replaces this with its own

        window = getattr(runtime, "window", None)
        if window is None:
            return False

        escaped = (
            text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        )
        window.document.body.innerHTML = (
            "<pre style='white-space:pre-wrap;word-break:break-word;"
            "background:#231014;color:#f0dcd8;font:13px/1.45 monospace;"
            "margin:0;padding:14px;min-height:100vh'>" + escaped + "</pre>"
        )
        return True
    except Exception:
        return False


def report_to_canvas(text: str) -> bool:
    """Paint a failure onto the display, if there is one."""
    try:
        screen = pygame.display.get_surface()
        if screen is None:
            return False

        # Fill first and unconditionally: the font system may be what
        # failed, and a red screen saying "it crashed" beats one saying
        # nothing at all.
        screen.fill(CRASH_BG)
        pygame.display.flip()

        font = pygame.font.Font(None, 20)
        lines: list[str] = []
        for line in text.splitlines():
            while len(line) > 78:
                lines.append(line[:78])
                line = line[78:]
            lines.append(line)

        y = 16
        for line in lines[-30:]:
            screen.blit(font.render(line, True, CRASH_TEXT), (14, y))
            y += 22
        pygame.display.flip()
        return True
    except Exception:
        return False


def report(text: str) -> None:
    """Get a failure in front of the player by whatever means work."""
    print(text, file=sys.stderr)
    report_to_page(text)
    report_to_canvas(text)


async def show_crash(screen, report_text: str) -> None:
    """Report a crash and hold the app alive so the message stays up."""
    report(report_text)
    while True:
        try:
            pygame.event.get()
        except Exception:
            pass
        await asyncio.sleep(0.1)


# -- the game -------------------------------------------------------------


async def run(seed: int | None = None) -> int:
    """Set up and run the game. Any failure ends up on screen."""
    if IMPORT_ERROR is not None:
        report(IMPORT_ERROR)
        while True:
            await asyncio.sleep(0.1)

    screen = None
    try:
        pygame.init()
        pygame.display.set_caption("Lechery")

        # RESIZABLE is a desktop affordance; a browser canvas is sized by
        # the page, and asking for a mode it cannot give fails before
        # anything is drawn.
        flags = 0 if is_web() else pygame.RESIZABLE
        size = browser_viewport() or SIZE
        screen = pygame.display.set_mode(size, flags)

        # The canvas may not be the size requested, so measure what arrived.
        # Laying out against a size we did not get puts the interface
        # off-screen, which looks identical to a crash.
        size = screen.get_size()
        app = App(size, Settings.load())
        if seed is not None:
            from lechery.traits import default_character

            app.start_game(default_character(), seed=seed)

        clock = pygame.time.Clock()
        running = True
        frame = 0
        while running:
            dt = min(clock.tick(FPS) / 1000.0, MAX_STEP)
            running = app.step(screen, pygame.event.get(), dt)
            pygame.display.flip()

            # A browser sends no resize event pygame can see, so the
            # viewport is polled. This is what catches a phone rotating.
            frame += 1
            if frame % VIEWPORT_POLL == 0:
                viewport = browser_viewport()
                if viewport is not None and viewport != size:
                    size = viewport
                    screen = pygame.display.set_mode(size, flags)
                    app.resize(screen.get_size())

            # Hand the frame back to the browser, every pass.
            await asyncio.sleep(0)
    except Exception:
        await show_crash(screen, traceback.format_exc())

    pygame.quit()
    return 0


def main(argv: list[str] | None = None) -> int:
    """Desktop entry. Not used by the browser, which awaits `run` directly."""
    return asyncio.run(run(parse_seed(argv or [])))


if __name__ == "__main__":
    # No SystemExit: pygbag runs this module as __main__, and an exception
    # propagating out of it ends the app instead of the frame. On the
    # desktop asyncio.run owns the loop; in a browser one is already
    # running, so the coroutine is handed to it instead.
    try:
        _loop = asyncio.get_running_loop()
    except RuntimeError:
        _loop = None

    if _loop is None:
        asyncio.run(run(parse_seed(sys.argv[1:])))
    else:
        _loop.create_task(run(parse_seed(sys.argv[1:])))
