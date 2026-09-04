"""Tests for layout, the message log, and the paperdoll's compositing.

These need a display surface but not a window; SDL's dummy driver provides
one, so the UI is testable in CI like everything else.
"""

import os

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

from lechery.log import Kind, MessageLog  # noqa: E402
from lechery.session import Session  # noqa: E402
from lechery.ui.layout import BAR_WIDTH, MIN_CENTER, TAB_WIDTH, ScreenLayout  # noqa: E402


@pytest.fixture(scope="module", autouse=True)
def display():
    pygame.init()
    pygame.display.set_mode((1280, 760))
    yield
    pygame.quit()


# -- layout ---------------------------------------------------------------


def test_the_three_panes_tile_the_window_exactly():
    layout = ScreenLayout(window=(1280, 760))
    assert layout.left.right == layout.center.left
    assert layout.center.right == layout.right.left
    assert layout.right.right == 1280


def test_collapsing_a_bar_gives_its_width_to_the_centre():
    layout = ScreenLayout(window=(1280, 760))
    before = layout.center.width
    layout.toggle_left()
    assert layout.left.width == TAB_WIDTH
    assert layout.center.width == before + BAR_WIDTH - TAB_WIDTH


def test_a_collapsed_bar_keeps_a_clickable_tab():
    """A bar with no handle is a bar the player cannot get back."""
    layout = ScreenLayout(window=(1280, 760))
    layout.toggle_right()
    assert layout.right.width == TAB_WIDTH
    assert layout.right.collidepoint(1280 - 5, 400)


def test_a_narrow_window_shrinks_the_bars_not_the_play_area():
    layout = ScreenLayout(window=(700, 600))
    assert layout.center.width >= MIN_CENTER
    assert layout.left.width < BAR_WIDTH


def test_panes_stay_valid_at_absurdly_small_sizes():
    layout = ScreenLayout(window=(200, 200))
    for rect in (layout.left, layout.center, layout.right):
        assert rect.width >= 1
    assert layout.right.right == 200


# -- message log ----------------------------------------------------------

def test_log_keeps_kinds_for_styling():
    log = MessageLog()
    log.title("A Room")
    log.prose("It is dark.")
    assert [e.kind for e in log] == [Kind.TITLE, Kind.PROSE]


def test_log_is_capped_and_drops_the_oldest():
    log = MessageLog(limit=3)
    for index in range(5):
        log.add(str(index))
    assert [e.text for e in log] == ["2", "3", "4"]


def test_entering_a_room_logs_its_name_and_prose_once():
    session = Session.new_game(1234)
    start = session.room
    assert [e.kind for e in session.log] == [Kind.TITLE, Kind.PROSE]

    door = next(iter(session.room_map.doorways.values()))
    session.enter_room(door.target_room_id, arriving_from=door.direction)
    session.enter_room(start.id, arriving_from=door.direction.opposite)

    titles = [e.text for e in session.log if e.kind is Kind.TITLE]
    prose = [e.text for e in session.log if e.kind is Kind.PROSE]
    assert titles.count(start.name) == 2, "the name marks every visit"
    assert len(prose) == 2, "prose fires once per room, not once per visit"


# -- paperdoll ------------------------------------------------------------


def test_paperdoll_composites_slots_in_declared_order():
    from lechery.ui.paperdoll import SLOTS, Paperdoll

    drawn = []
    doll = Paperdoll((100, 160))
    for name in ("hair", "backdrop", "torso"):
        doll.set_slot(name, lambda surface, rect, name=name: drawn.append(name))
    doll.surface()
    assert drawn == sorted(drawn, key=SLOTS.index)


def test_paperdoll_caches_until_something_changes():
    from lechery.ui.paperdoll import Paperdoll

    doll = Paperdoll((100, 160))
    first = doll.surface()
    assert doll.surface() is first, "recompositing every frame would be wasteful"

    doll.set_slot("held", lambda surface, rect: None)
    assert doll.surface() is not first


def test_paperdoll_rejects_an_unknown_slot():
    """Slot order is the contract; a typo must not silently draw nothing."""
    from lechery.ui.paperdoll import Paperdoll

    with pytest.raises(KeyError):
        Paperdoll((10, 10)).set_slot("wings", lambda surface, rect: None)


# -- the assembled app ----------------------------------------------------


def test_app_draws_every_pane_without_error():
    from lechery.ui.app import App

    surface = pygame.display.get_surface()
    session = Session.new_game(1234)
    app = App(session, surface.get_size())

    app.draw(surface)
    app.layout.toggle_left()
    app.layout.toggle_right()
    app.draw(surface)


def test_the_world_view_measures_the_centre_pane_not_the_window():
    """Otherwise a collapsed bar would shift the framing of every room."""
    from lechery.ui.app import App

    surface = pygame.display.get_surface()
    app = App(Session.new_game(1234), surface.get_size())

    app.draw(surface)
    framed = app.world.camera_offset()
    app.layout.toggle_left()
    app.draw(surface)
    assert app.world.camera_offset() != framed
    assert app.world.rect == app.layout.center
