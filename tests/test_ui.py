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
from lechery.ui.layout import (  # noqa: E402
    BAR_WIDTH,
    MIN_CENTER,
    TAB_WIDTH,
    CompactLayout,
    WideLayout,
)
from lechery.ui.profile import FormFactor, measure, resolve  # noqa: E402
from lechery.settings import LayoutMode, Settings  # noqa: E402


# -- layout ---------------------------------------------------------------


def test_the_three_panes_tile_the_window_exactly():
    layout = WideLayout(window=(1280, 760))
    assert layout.left.right == layout.center.left
    assert layout.center.right == layout.right.left
    assert layout.right.right == 1280


def test_collapsing_a_bar_gives_its_width_to_the_centre():
    layout = WideLayout(window=(1280, 760))
    before = layout.center.width
    layout.toggle_left()
    assert layout.left.width == TAB_WIDTH
    assert layout.center.width == before + BAR_WIDTH - TAB_WIDTH


def test_a_collapsed_bar_keeps_a_clickable_tab():
    """A bar with no handle is a bar the player cannot get back."""
    layout = WideLayout(window=(1280, 760))
    layout.toggle_right()
    assert layout.right.width == TAB_WIDTH
    assert layout.right.collidepoint(1280 - 5, 400)


def test_a_narrow_window_shrinks_the_bars_not_the_play_area():
    layout = WideLayout(window=(700, 600))
    assert layout.center.width >= MIN_CENTER
    assert layout.left.width < BAR_WIDTH


def test_panes_stay_valid_at_absurdly_small_sizes():
    layout = WideLayout(window=(200, 200))
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
    from lechery.ui.screens.play import PlayScreen

    surface = pygame.display.get_surface()
    session = Session.new_game(1234)
    screen = PlayScreen(session, surface.get_size())

    screen.draw(surface)
    screen.layout.toggle_left()
    screen.layout.toggle_right()
    screen.draw(surface)


def test_the_world_view_measures_the_centre_pane_not_the_window():
    """Otherwise a collapsed bar would shift the framing of every room."""
    from lechery.ui.screens.play import PlayScreen

    surface = pygame.display.get_surface()
    screen = PlayScreen(Session.new_game(1234), surface.get_size())

    screen.draw(surface)
    framed = screen.world.camera_offset()
    screen.layout.toggle_left()
    screen.draw(surface)
    assert screen.world.camera_offset() != framed
    assert screen.world.rect == screen.layout.center


# -- form factor ----------------------------------------------------------


@pytest.mark.parametrize(
    "window,expected",
    [
        ((1920, 1080), FormFactor.WIDE),
        ((1280, 760), FormFactor.WIDE),
        ((1024, 768), FormFactor.WIDE),
        ((390, 844), FormFactor.COMPACT),      # phone, upright
        ((844, 390), FormFactor.COMPACT),      # phone, on its side: too narrow
        ((820, 1180), FormFactor.COMPACT),     # tablet, upright
        ((1180, 820), FormFactor.WIDE),        # tablet, landscape
        ((700, 900), FormFactor.COMPACT),      # desktop window dragged narrow
    ],
)
def test_form_factor_is_measured_from_the_window(window, expected):
    """The point of measuring rather than detecting: a desktop window
    dragged narrow and a phone reach the same answer."""
    assert measure(window) == expected


def test_an_explicit_setting_overrides_the_measurement():
    phone = (390, 844)
    assert resolve(LayoutMode.AUTO, phone) is FormFactor.COMPACT
    assert resolve(LayoutMode.WIDE, phone) is FormFactor.WIDE
    assert resolve(LayoutMode.COMPACT, (1920, 1080)) is FormFactor.COMPACT


# -- compact layout -------------------------------------------------------


def test_compact_gives_the_whole_window_to_the_world():
    layout = CompactLayout(window=(390, 844))
    assert layout.center.size == (390, 844)


def test_compact_drawers_overlay_and_leave_the_world_visible():
    layout = CompactLayout(window=(390, 844))
    layout.toggle_right()
    assert layout.overlays
    assert layout.right.width < 390, "a drawer that covers everything is a screen"
    assert layout.center.size == (390, 844), "the world keeps its rect underneath"


def test_opening_one_compact_drawer_closes_the_other():
    layout = CompactLayout(window=(390, 844))
    layout.toggle_left()
    layout.toggle_right()
    assert layout.right_open and not layout.left_open


def test_compact_drawers_start_closed():
    """On a small screen the world is what the player opened the game for."""
    layout = CompactLayout(window=(390, 844))
    assert not layout.left_open and not layout.right_open


def test_compact_handles_are_finger_sized_and_do_not_overlap():
    layout = CompactLayout(window=(390, 844))
    assert layout.left_handle.width >= 44 and layout.left_handle.height >= 44
    assert not layout.left_handle.colliderect(layout.right_handle)


# -- switching layouts ----------------------------------------------------


def test_the_app_switches_layout_when_the_window_changes_shape():
    from lechery.ui.screens.play import PlayScreen

    screen = PlayScreen(Session.new_game(1234), (1280, 760))
    assert screen.form is FormFactor.WIDE

    screen.handle_event(pygame.event.Event(pygame.VIDEORESIZE, w=390, h=844))
    assert screen.form is FormFactor.COMPACT
    assert screen.layout.overlays


def test_resizing_within_one_form_factor_keeps_the_open_drawers():
    """Rebuilding the layout on every resize would discard the arrangement."""
    from lechery.ui.screens.play import PlayScreen

    screen = PlayScreen(Session.new_game(1234), (390, 844))
    screen.layout.toggle_right()
    screen.handle_event(pygame.event.Event(pygame.VIDEORESIZE, w=400, h=860))
    assert screen.layout.right_open


def test_the_layout_override_survives_a_resize_that_would_change_it():
    from lechery.ui.screens.play import PlayScreen

    settings = Settings(layout_mode=LayoutMode.WIDE)
    screen = PlayScreen(Session.new_game(1234), (1280, 760), settings)
    screen.handle_event(pygame.event.Event(pygame.VIDEORESIZE, w=390, h=844))
    assert screen.form is FormFactor.WIDE, "a stated preference is not second-guessed"


def test_touch_controls_follow_the_layout_unless_forced():
    from lechery.ui.screens.play import PlayScreen

    assert not PlayScreen(Session.new_game(1), (1280, 760)).uses_touch_controls
    assert PlayScreen(Session.new_game(1), (390, 844)).uses_touch_controls
    forced = PlayScreen(Session.new_game(1), (1280, 760), Settings(touch_controls=True))
    assert forced.uses_touch_controls


def test_app_draws_both_layouts_without_error():
    from lechery.ui.screens.play import PlayScreen

    surface = pygame.display.get_surface()
    for size in [(1280, 760), (390, 844)]:
        screen = PlayScreen(Session.new_game(1234), size)
        screen.draw(surface)
        screen.layout.toggle_right()
        screen.draw(surface)


# -- thumbstick -----------------------------------------------------------


def test_the_stick_reports_a_direction_from_a_drag():
    from lechery.ui.touch import Thumbstick

    window = (390, 844)
    stick = Thumbstick()
    origin = (100, 700)
    stick.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=origin), window)
    stick.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=(origin[0] + 40, origin[1])), window)

    dx, dy = stick.direction()
    assert dx > 0 and abs(dy) < 1e-9


def test_the_stick_ignores_drags_outside_its_zone():
    from lechery.ui.touch import Thumbstick

    window = (390, 844)
    stick = Thumbstick()
    assert not stick.handle_event(
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(380, 20)), window
    )
    assert not stick.active


def test_the_stick_has_a_dead_zone_so_a_tap_is_not_a_twitch():
    from lechery.ui.touch import Thumbstick

    window = (390, 844)
    stick = Thumbstick()
    stick.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(100, 700)), window)
    stick.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=(102, 701)), window)
    assert stick.direction() == (0.0, 0.0)


def test_the_stick_is_clamped_to_unit_length():
    from lechery.ui.touch import Thumbstick

    window = (390, 844)
    stick = Thumbstick()
    stick.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(100, 700)), window)
    stick.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=(100 + 500, 700)), window)
    dx, dy = stick.direction()
    assert (dx**2 + dy**2) ** 0.5 <= 1.0 + 1e-9


def test_releasing_the_stick_stops_movement():
    from lechery.ui.touch import Thumbstick

    window = (390, 844)
    stick = Thumbstick()
    stick.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(100, 700)), window)
    stick.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=(160, 700)), window)
    stick.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=(160, 700)), window)
    assert stick.direction() == (0.0, 0.0)
    assert not stick.active


def test_moving_with_the_stick_turns_the_body_to_face_travel():
    """Without a cursor there is nothing else to aim by."""
    from lechery.ui.screens.play import PlayScreen

    screen = PlayScreen(Session.new_game(1234), (390, 844))
    screen.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(100, 700)))
    screen.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=(160, 700)))
    screen.update(1 / 60)
    assert abs(screen.session.player.facing) < 1e-6  # facing east


# -- settings -------------------------------------------------------------


def test_settings_round_trip_through_a_file(tmp_path):
    path = tmp_path / "settings.json"
    Settings(layout_mode=LayoutMode.COMPACT, wide_left_open=False, path=path).save()
    assert Settings.load(path).layout_mode is LayoutMode.COMPACT
    assert Settings.load(path).wide_left_open is False


def test_missing_or_corrupt_settings_fall_back_to_defaults(tmp_path):
    """Losing preferences must never cost the player the game."""
    assert Settings.load(tmp_path / "absent.json").layout_mode is LayoutMode.AUTO

    corrupt = tmp_path / "bad.json"
    corrupt.write_text("{not json at all")
    assert Settings.load(corrupt).layout_mode is LayoutMode.AUTO


def test_unknown_keys_and_bad_values_are_ignored_not_fatal():
    """A settings file written by a newer build must still load."""
    settings = Settings.from_dict({"layout_mode": "hologram", "future_option": 3})
    assert settings.layout_mode is LayoutMode.AUTO


def test_saving_to_an_unwritable_path_reports_failure_without_raising(tmp_path):
    blocked = tmp_path / "file"
    blocked.write_text("")
    assert Settings().save(blocked / "nested" / "settings.json") is False
