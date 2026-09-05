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
