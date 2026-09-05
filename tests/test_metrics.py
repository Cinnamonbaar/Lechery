"""Tests for the device-pixel scale system.

The bug this exists to prevent: rendering at CSS pixels and letting the
browser upscale, which is what made the phone build blurry. Everything is
authored in design units and multiplied on the way out, so a mistake here
shows up as an interface that is the wrong physical size rather than a
crash -- worth pinning precisely.
"""

import os

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

from lechery.ui import metrics  # noqa: E402
from lechery.ui.layout import BAR_WIDTH, TAB_WIDTH, WideLayout  # noqa: E402
from lechery.ui.profile import FormFactor, measure  # noqa: E402


@pytest.fixture
def at_3x():
    """A typical phone: three device pixels per design unit."""
    metrics.set_scale(3.0)
    yield
    metrics.set_scale(1.0)


def test_scale_defaults_to_one_so_the_layer_is_invisible():
    assert metrics.SCALE == 1.0
    assert metrics.px(15) == 15


def test_design_units_become_device_pixels(at_3x):
    assert metrics.px(15) == 45
    assert metrics.px(268) == 804


def test_device_pixels_convert_back_to_design_units(at_3x):
    assert metrics.design(1170) == 390


def test_scale_is_clamped_to_something_a_phone_can_actually_fill():
    assert metrics.set_scale(99) == metrics.MAX_SCALE
    assert metrics.set_scale(0.1) == metrics.MIN_SCALE
    metrics.set_scale(1.0)


def test_nonsense_scales_are_refused_rather_than_adopted():
    """A zero or missing ratio would collapse the whole interface."""
    metrics.set_scale(2.0)
    assert metrics.set_scale(0) == 2.0
    assert metrics.set_scale(None) == 2.0
    assert metrics.set_scale("wide") == 2.0
    metrics.set_scale(1.0)


# -- the decisions that must stay in design units -------------------------


def test_a_phone_is_measured_by_its_size_not_its_pixel_count(at_3x):
    """1170x2532 device pixels is an iPhone, not a desktop.

    Measuring raw pixels here is the bug that laid out the three-pane
    desktop view on a phone.
    """
    assert measure((1170, 2532)) is FormFactor.COMPACT


def test_a_desktop_is_still_a_desktop_at_1x():
    assert measure((1280, 760)) is FormFactor.WIDE


def test_a_hidpi_desktop_is_not_mistaken_for_a_phone():
    metrics.set_scale(2.0)
    try:
        assert measure((2560, 1520)) is FormFactor.WIDE
    finally:
        metrics.set_scale(1.0)


# -- layout scales with the display ---------------------------------------


def test_bars_take_the_same_physical_width_at_any_scale(at_3x):
    """A hi-dpi desktop: 1280 design units wide, 3840 device pixels."""
    layout = WideLayout(window=(3840, 2280))
    assert layout.left.width == BAR_WIDTH * 3


def test_a_collapsed_tab_stays_finger_sized_at_high_density(at_3x):
    layout = WideLayout(window=(3840, 2280))
    layout.toggle_left()
    assert layout.left.width == TAB_WIDTH * 3


def test_bars_still_give_way_before_the_play_area_does(at_3x):
    """A phone-sized window cannot fit two bars, whatever its pixel count."""
    layout = WideLayout(window=(1170, 2532))
    assert layout.left.width == TAB_WIDTH * 3
    assert layout.center.width > layout.left.width


def test_fonts_are_built_at_device_resolution(at_3x):
    from lechery.ui import fonts

    # The display is shared across the whole session; resizing it here
    # would silently change what every later test measures.
    fonts.clear_cache()
    small = fonts.load("body", 15)
    metrics.set_scale(1.0)
    fonts.clear_cache()
    unscaled = fonts.load("body", 15)

    assert small.get_height() > unscaled.get_height(), "3x text needs 3x pixels"
    fonts.clear_cache()


def test_tiles_scale_with_the_display(at_3x):
    from lechery.ui.worldview import TILE, tile_px

    assert tile_px() == TILE * 3


def test_the_creation_screen_stacks_by_physical_width_not_pixels(at_3x):
    """The bug this caught: 1170 device pixels read as wider than a laptop."""
    from lechery.ui.app import App
    from lechery.ui.screens.creation import CharacterCreation

    phone = App((1170, 2532))
    creation = phone.push(CharacterCreation())
    assert creation.stacked

    desktop = App((3840, 2280))
    assert not desktop.push(CharacterCreation()).stacked


def test_every_screen_lays_out_inside_a_retina_phone(at_3x):
    """Nothing may run off the bottom just because the pixels multiplied."""
    from lechery.ui.app import App
    from lechery.ui.screens.creation import FOOTER, STEPS, CharacterCreation

    window = (1170, 2532)
    app = App(window)
    creation = app.push(CharacterCreation())

    for index in range(len(STEPS)):
        creation.step = index
        creation._build()
        if creation.widgets:
            lowest = max(w.rect.bottom for w in creation.widgets)
            assert lowest <= window[1] - metrics.px(FOOTER), f"step {index} overflows"


def test_a_retina_phone_still_gets_finger_sized_touch_targets(at_3x):
    """44 design units is the guideline; in pixels it must grow, not stay."""
    from lechery.ui.layout import CompactLayout

    layout = CompactLayout(window=(1170, 2532))
    assert layout.left_handle.width >= metrics.px(44)


# -- page coordinates -----------------------------------------------------


def test_page_geometry_converts_device_pixels_to_css_pixels(at_3x):
    """The bug this caught, exactly.

    `from .metrics import SCALE` binds the value at import, so set_scale was
    never seen and the input element was positioned at three times its
    coordinates -- off the bottom of the page, where nothing could tap it.
    """
    from lechery.ui.nativetext import css_geometry

    left, top, width, height = css_geometry(pygame.Rect(270, 1100, 600, 96))
    assert (left, top, width, height) == (90, 1100 / 3, 200, 32)


def test_page_geometry_is_identity_at_1x():
    from lechery.ui.nativetext import css_geometry

    assert css_geometry(pygame.Rect(10, 20, 30, 40)) == (10, 20, 30, 40)


def test_the_name_field_lands_on_screen_on_a_phone(at_3x):
    """End to end: whatever the field's device rect, its CSS box is on the page."""
    from lechery.ui.app import App
    from lechery.ui.nativetext import css_geometry
    from lechery.ui.screens.creation import CharacterCreation

    viewport = (390, 844)
    window = (viewport[0] * 3, viewport[1] * 3)
    app = App(window)
    creation = app.push(CharacterCreation())

    field = creation.widgets[0]
    left, top, width, height = css_geometry(field.rect)

    assert 0 <= left and left + width <= viewport[0], "field runs off the side"
    assert 0 <= top and top + height <= viewport[1], "field runs off the bottom"


def test_no_module_binds_the_scale_at_import_time():
    """The whole class of bug: a stale copy of a value that changes.

    Checked structurally, because a stale binding behaves perfectly at 1x
    and only breaks on a device nobody testing has to hand.
    """
    import ast
    import pathlib

    ui = pathlib.Path(__file__).resolve().parent.parent / "lechery" / "ui"
    for path in ui.rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and "metrics" in node.module:
                imported = {alias.name for alias in node.names}
                assert "SCALE" not in imported, (
                    f"{path.name} binds SCALE at import; read metrics.SCALE instead"
                )
