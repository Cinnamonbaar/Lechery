"""Tests for the things a pygbag build changes.

None of these need a browser. They pin the behaviours that differ under
Emscripten, faking the platform check, so a regression shows up here rather
than after packaging.
"""

import asyncio
import os

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

import lechery.platform as platform  # noqa: E402
from lechery.session import Session  # noqa: E402
from lechery.settings import Settings, default_path  # noqa: E402
from lechery.ui import fonts  # noqa: E402


@pytest.fixture
def pretend_web(monkeypatch):
    monkeypatch.setattr(platform.sys, "platform", "emscripten")
    fonts.clear_cache()
    yield
    fonts.clear_cache()


# -- platform -------------------------------------------------------------


def test_web_is_detected_from_sys_platform(pretend_web):
    assert platform.is_web()


def test_settings_live_somewhere_persistent_in_the_browser(pretend_web):
    """Anywhere but /data is wiped on reload, and fails silently."""
    assert str(default_path()).startswith("/data/")


def test_settings_live_under_home_on_the_desktop():
    assert not str(default_path()).startswith("/data/")


# -- fonts ----------------------------------------------------------------


def test_fonts_never_ask_the_system_in_a_web_build(pretend_web, monkeypatch):
    """SysFont degrades silently in WASM, so a web build must not call it.

    Left unchecked this is invisible until after packaging, when the web
    build renders in a different typeface than the desktop one.
    """
    def explode(*args, **kwargs):
        raise AssertionError("SysFont must not be called in a web build")

    monkeypatch.setattr(pygame.font, "SysFont", explode)
    assert fonts.load("body", 15) is not None


def test_font_loading_always_returns_a_usable_font(monkeypatch):
    """Every fallback removed, pygame's own bundled font must still answer."""
    monkeypatch.setattr(fonts, "_bundled", lambda role, size: None)
    monkeypatch.setattr(fonts, "_system", lambda size, bold: None)
    fonts.clear_cache()
    font = fonts.load("body", 15)
    assert font.render("x", True, (255, 255, 255)).get_width() > 0


def test_fonts_are_cached_per_role_and_size():
    fonts.clear_cache()
    assert fonts.load("body", 15) is fonts.load("body", 15)
    assert fonts.load("body", 15) is not fonts.load("body", 22)


# -- the frame ------------------------------------------------------------


def test_a_frame_runs_without_a_loop_around_it():
    """The frame body holds no async, so both loops share every real line."""
    from lechery.ui.app import App

    surface = pygame.display.get_surface()
    app = App(surface.get_size())
    assert app.step(surface, [], 1 / 60) is True


def test_closing_the_window_stops_the_loop():
    from lechery.ui.app import App

    surface = pygame.display.get_surface()
    app = App(surface.get_size())
    assert app.step(surface, [pygame.event.Event(pygame.QUIT)], 1 / 60) is False


def test_escape_in_play_returns_to_the_menu_rather_than_quitting():
    """Escape used to quit the game. With a menu on the stack it should not."""
    from lechery.traits import default_character
    from lechery.ui.app import App
    from lechery.ui.screens.menu import MainMenu

    surface = pygame.display.get_surface()
    app = App(surface.get_size())
    app.push(_Blank())
    app.start_game(default_character("Test"), seed=1234)

    assert app.step(
        surface, [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)], 1 / 60
    ) is True
    assert isinstance(app.screen, MainMenu)


class _Blank:
    """Stands in for the creation screen, which start_game replaces."""

    transparent = False

    def enter(self, app):
        self.app = app

    def leave(self):
        pass

    def resize(self, window):
        pass

    def handle_event(self, event):
        return False

    def update(self, dt):
        pass

    def draw(self, surface):
        pass


def test_the_entry_point_is_a_coroutine():
    """pygbag drives an async entry point; a plain function would not run."""
    import main as entry

    assert asyncio.iscoroutinefunction(entry.run)


def test_the_real_loop_yields_to_the_browser_every_frame(monkeypatch):
    """A frame that never yields freezes the tab, so count the suspensions.

    This drives main.run itself with the App and the display stubbed out,
    because the yield is only worth testing where it actually lives.
    """
    import main as entry

    frames = {"count": 0}
    yields = {"count": 0}

    class ThreeFrameApp:
        def __init__(self, *args, **kwargs):
            pass

        def step(self, surface, events, dt):
            frames["count"] += 1
            return frames["count"] < 3

        def start_game(self, *args, **kwargs):
            pass

    async def counting_sleep(delay):
        assert delay == 0, "the yield must not stall the frame"
        yields["count"] += 1

    monkeypatch.setattr(entry, "App", ThreeFrameApp)
    monkeypatch.setattr(entry.asyncio, "sleep", counting_sleep)
    monkeypatch.setattr(entry.pygame.display, "flip", lambda: None)
    monkeypatch.setattr(entry.pygame, "quit", lambda: None)

    assert asyncio.run(entry.run(1234)) == 0
    assert frames["count"] == 3
    assert yields["count"] == frames["count"], "every frame must yield, the last included"


def test_a_long_frame_cannot_tunnel_the_player_through_a_wall():
    """A backgrounded tab returns with seconds of elapsed time in one frame."""
    from lechery.space import overlaps_solid

    import main as entry

    session = Session.new_game(1234)
    before = session.player.position
    session.update((-1, 0), entry.MAX_STEP)
    assert not overlaps_solid(
        session.room_map.tilemap, session.player.position, session.player.half_extents
    )
    assert session.player.position != before


# -- startup robustness ---------------------------------------------------


def test_a_seed_is_only_taken_from_an_argument_that_is_a_number():
    """argv is not ours in a web build: pygbag passes what it likes.

    int() on that would raise before the first frame, which in a browser
    is a blank canvas and no explanation.
    """
    import main as entry

    assert entry.parse_seed([]) is None
    assert entry.parse_seed(["1234"]) == 1234
    assert entry.parse_seed(["/data/data/org.python/assets/main.py"]) is None
    assert entry.parse_seed(["--dev", "main.py", "77"]) == 77


def test_fonts_prefer_pygames_own_default_in_a_web_build(pretend_web):
    """There is no OS font list in WASM, so SysFont is a last resort there."""
    order = [source.__name__ for source in fonts._sources("body", 15, False)]
    assert order.index("default") < order.index("system")


def test_fonts_prefer_a_system_font_on_the_desktop():
    """An OS font is a real improvement over pygame's default."""
    order = [source.__name__ for source in fonts._sources("body", 15, False)]
    assert order.index("system") < order.index("default")


def test_font_loading_raises_with_a_reason_when_every_source_fails(monkeypatch):
    """A silent font failure takes the interface with it and explains nothing."""
    monkeypatch.setattr(fonts, "_bundled", lambda role, size: None)
    monkeypatch.setattr(fonts, "_default", lambda size: None)
    monkeypatch.setattr(fonts, "_system", lambda size, bold: None)
    fonts.clear_cache()

    with pytest.raises(RuntimeError, match="no font available"):
        fonts.load("body", 15)
    fonts.clear_cache()


def test_a_crash_paints_the_screen_rather_than_leaving_it_blank():
    """The whole point: a browser shows nothing for an unhandled exception."""
    import asyncio

    import main as entry

    surface = pygame.display.get_surface()
    surface.fill((0, 0, 0))

    async def drive():
        # show_crash never returns, so it is raced against a timeout.
        task = asyncio.ensure_future(entry.show_crash(surface, "Traceback: boom"))
        await asyncio.sleep(0)
        task.cancel()

    asyncio.run(drive())
    assert surface.get_at((5, 5))[:3] == entry.CRASH_BG, "the canvas should be painted"


def test_the_entry_module_never_raises_system_exit_at_module_scope():
    """pygbag runs main.py as __main__; a SystemExit there ends the app.

    Asserted on the source because the failure only happens under pygbag,
    where there is nothing to observe it with.
    """
    import ast
    import pathlib

    source = pathlib.Path(__file__).resolve().parent.parent / "main.py"
    tree = ast.parse(source.read_text())

    for node in tree.body:
        for inner in ast.walk(node):
            if isinstance(inner, ast.Raise) and isinstance(inner.exc, ast.Call):
                name = getattr(inner.exc.func, "id", "")
                assert name != "SystemExit", "SystemExit at module scope ends a pygbag app"


def test_game_imports_are_guarded_so_a_failure_can_be_reported():
    """An import error happens before any handler could otherwise run."""
    import main as entry

    assert hasattr(entry, "IMPORT_ERROR")
    assert entry.IMPORT_ERROR is None, "the game should import cleanly here"


def test_a_failure_is_reported_by_every_route_available():
    import main as entry

    surface = pygame.display.get_surface()
    surface.fill((0, 0, 0))

    entry.report("Traceback: something broke")

    # No browser here, so the page route is unavailable and the canvas
    # route must have carried it.
    assert entry.report_to_page("x") is False
    assert surface.get_at((5, 5))[:3] == entry.CRASH_BG


def test_reporting_survives_there_being_no_display(monkeypatch):
    """The canvas may not exist yet when the failure happens."""
    import main as entry

    monkeypatch.setattr(entry.pygame.display, "get_surface", lambda: None)
    assert entry.report_to_canvas("boom") is False
    entry.report("boom")  # must not raise


def test_the_build_canvas_matches_the_size_the_game_asks_for():
    """Different sizes lay the interface out against a surface we never got."""
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
    import buildweb

    import main as entry

    assert buildweb.CANVAS == entry.SIZE


def test_the_viewport_is_unavailable_outside_a_browser():
    """There is no window to ask, so the desktop size stands."""
    import main as entry

    assert entry.browser_viewport() is None


def test_the_viewport_is_read_from_the_browser_window_when_there_is_one(monkeypatch):
    """A phone must lay out against the screen, not the build's canvas size."""
    import sys
    import types

    import main as entry

    window = types.SimpleNamespace(innerWidth=390, innerHeight=844)
    fake_runtime = types.SimpleNamespace(window=window)
    monkeypatch.setitem(sys.modules, "platform", fake_runtime)

    assert entry.browser_viewport() == (390, 844)


def test_a_nonsense_viewport_is_ignored(monkeypatch):
    """A canvas of zero size would take the whole interface with it."""
    import sys
    import types

    import main as entry

    monkeypatch.setitem(
        sys.modules,
        "platform",
        types.SimpleNamespace(window=types.SimpleNamespace(innerWidth=0, innerHeight=0)),
    )
    assert entry.browser_viewport() is None


def test_resizing_the_app_repicks_the_layout():
    """Rotation and a desktop resize are the same event downstream."""
    from lechery.ui.app import App
    from lechery.ui.profile import FormFactor

    app = App((1280, 760))
    assert app.form is FormFactor.WIDE

    app.resize((390, 844))
    assert app.form is FormFactor.COMPACT
    assert app.window == (390, 844)


# -- the on-screen keyboard shrinking the viewport ------------------------


def test_the_keyboard_shrinking_the_viewport_is_not_a_resize():
    """The bug: tapping the field deselected it instantly.

    An on-screen keyboard takes room from the bottom of the page. Treating
    that as a resize recreates the display, which destroys the focus that
    opened the keyboard in the first place.
    """
    import main as entry

    phone = (390, 844)
    with_keyboard = (390, 480)
    assert entry.should_adopt(phone, with_keyboard, typing=True) is False


def test_a_rotation_is_still_adopted_while_typing():
    """Width is the reliable signal: a keyboard never changes it."""
    import main as entry

    assert entry.should_adopt((390, 844), (844, 390), typing=True) is True


def test_the_viewport_growing_back_is_adopted():
    """Dismissing the keyboard must restore the full-height layout."""
    import main as entry

    assert entry.should_adopt((390, 480), (390, 844), typing=True) is True


def test_a_height_change_with_nothing_focused_is_a_real_resize():
    import main as entry

    assert entry.should_adopt((390, 844), (390, 700), typing=False) is True


def test_no_change_is_not_a_resize():
    import main as entry

    assert entry.should_adopt((390, 844), (390, 844), typing=False) is False


def test_overlaid_fields_are_never_reported_focused_off_the_web():
    from lechery.ui import nativetext

    assert nativetext.any_focused() is False


def test_the_input_font_is_large_enough_that_ios_will_not_zoom():
    """Below 16px Safari zooms the page and scrolls the field into view."""
    from lechery.ui.nativetext import MIN_FONT_PX

    assert MIN_FONT_PX >= 16
