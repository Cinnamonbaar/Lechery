"""Tests for the trait-to-avatar mapping.

The library itself is a browser thing and cannot run here, so what is
tested is the part that is ours: the translation between our traits and
its dimensions, and the lifecycle that keeps a page element from
outliving the screen that placed it.
"""

import os

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

from lechery.traits import GENDERS, default_character  # noqa: E402
from lechery.ui import avatar  # noqa: E402


@pytest.fixture
def character():
    return default_character("Ilse")


# -- the mapping ----------------------------------------------------------


def test_height_passes_through_because_both_use_centimetres(character):
    character.set("height", 178)
    assert avatar.dimensions(character)["height"] == 178


def test_a_cup_size_becomes_the_librarys_own_scale(character):
    character.set("bust", 0)
    flat = avatar.dimensions(character)["breastSize"]
    character.set("bust", 12)
    full = avatar.dimensions(character)["breastSize"]

    assert flat == 0
    assert full == 100
    assert flat < full


def test_hair_colour_is_converted_to_the_hue_it_actually_is(character):
    """One source of truth for what "copper" means, not two colour tables."""
    character.set("hair_colour", "copper")
    dimensions = avatar.dimensions(character)

    # Copper is an orange: hue in the 15-40 degree range, well saturated.
    assert 10 <= dimensions["hairHue"] <= 45
    assert dimensions["hairSaturation"] > 30


def test_black_hair_maps_to_dark_rather_than_to_a_hue(character):
    character.set("hair_colour", "black")
    assert avatar.dimensions(character)["hairLightness"] < 20


def test_femininity_comes_from_how_the_body_reads(character):
    """Their core stat and our perception model are the same idea."""
    character.set("bust", 0)
    character.set("phallus", 18)
    masculine = avatar.femininity(character)

    character.set("phallus", 0)
    character.set("bust", 10)
    feminine = avatar.femininity(character)

    assert masculine < feminine
    assert avatar.FEM_LOW <= masculine <= avatar.FEM_HIGH
    assert avatar.FEM_LOW <= feminine <= avatar.FEM_HIGH


def test_femininity_reads_the_undressed_body(character):
    """It is drawing the body, so clothing should not be in the sum."""
    character.set("phallus", 20)
    character.set("bust", 0)
    assert avatar.femininity(character) < 5.5


def test_identity_does_not_move_the_drawing(character):
    """Gender is who they are; the figure shows the body."""
    before = avatar.payload(character)["fem"]
    character.gender = GENDERS["man"]
    assert avatar.payload(character)["fem"] == before


def test_only_dimensions_we_have_an_opinion_about_are_sent(character):
    """The rest keep the library's defaults, which are sensible averages."""
    sent = set(avatar.dimensions(character))
    assert "height" in sent and "breastSize" in sent
    assert "faceLength" not in sent
    assert "buttFullness" not in sent


# -- redrawing ------------------------------------------------------------


def test_the_signature_moves_only_when_the_drawing_would(character):
    before = avatar.signature(character)
    character.set("age", 40)  # not drawn
    assert avatar.signature(character) == before

    character.set("bust", 7)
    assert avatar.signature(character) != before


def test_update_reports_whether_anything_changed(character):
    figure = avatar.Avatar()
    assert figure.update(character) is True
    assert figure.update(character) is False

    character.set("height", 190)
    assert figure.update(character) is True


# -- lifecycle ------------------------------------------------------------


def test_an_unplaced_avatar_is_taken_down_at_the_end_of_the_frame():
    """It lives in the page, so it does not vanish when its screen stops
    drawing -- it would otherwise hang over the menu."""
    figure = avatar.Avatar()
    figure.visible = True

    figure.frame_done()
    assert not figure.visible


def test_a_placed_avatar_survives_the_frame():
    figure = avatar.Avatar()
    figure.place(pygame.Rect(0, 0, 100, 200))
    figure.frame_done()
    assert figure.visible


def test_placing_again_after_a_frame_keeps_it_up():
    figure = avatar.Avatar()
    for _ in range(3):
        figure.place(pygame.Rect(0, 0, 100, 200))
        figure.frame_done()
    assert figure.visible


def test_the_desktop_falls_back_to_the_placeholder_figure():
    """There is no browser here, so nothing can draw the real avatar."""
    from lechery.entities.actor import Player
    from lechery.ui.fonts import load as load_font
    from lechery.ui.paperdollpanel import PaperdollPanel
    from lechery.ui.text import TextStyle

    style = TextStyle(load_font("body", 15))
    panel = PaperdollPanel(Player(), style, style)

    assert not avatar.available()
    assert panel.avatar is None
    assert panel.doll is not None
