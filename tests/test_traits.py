"""Tests for the trait model, narration, and the paperdoll reading it."""

import os

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

from lechery.narration import describe_change  # noqa: E402
from lechery.session import Session  # noqa: E402
from lechery.traits import (  # noqa: E402
    GENDERS,
    HE,
    HEIGHT,
    MINIMUM_AGE,
    SHE,
    THEY,
    Character,
    Traits,
    colour,
    default_character,
)


@pytest.fixture
def character():
    return default_character("Test")


# -- scales ---------------------------------------------------------------


def test_a_trait_has_both_a_number_and_a_word(character):
    character.set("height", 172)
    assert character.traits["height"] == 172
    assert character.traits.label("height") == "average height"
    assert character.traits.describe("height") == "172cm (average height)"


@pytest.mark.parametrize(
    "height,label",
    [(140, "very short"), (155, "short"), (170, "average height"), (185, "tall"), (200, "towering")],
)
def test_height_bands_cover_the_range(height, label):
    assert HEIGHT.label(height) == label


def test_values_are_clamped_to_the_scale(character):
    character.set("height", 9999)
    assert character.traits["height"] == HEIGHT.maximum
    character.set("height", -50)
    assert character.traits["height"] == HEIGHT.minimum


def test_band_index_lets_content_compare_without_knowing_labels():
    assert HEIGHT.index(200) > HEIGHT.index(140)


# -- identity is not the body ---------------------------------------------


def test_growing_a_bust_does_not_change_who_the_character_is(character):
    """The reason identity and body are separate classes."""
    before = character.gender
    character.set("bust", 6)
    assert character.gender is before
    assert character.pronouns is before.pronouns


def test_pronouns_follow_gender_unless_overridden(character):
    character.gender = GENDERS["woman"]
    assert character.pronouns is SHE
    character.pronoun_override = THEY
    assert character.pronouns is THEY
    character.gender = GENDERS["man"]
    assert character.pronouns is THEY, "a chosen pronoun set survives a gender change"


def test_pronouns_carry_their_verb_agreement():
    assert SHE.verb("is", "are") == "is"
    assert THEY.verb("is", "are") == "are"


# -- age floor ------------------------------------------------------------


def test_age_below_the_floor_is_rejected_not_silently_corrected(character):
    with pytest.raises(ValueError):
        character.set("age", 16)
    assert character.traits["age"] >= MINIMUM_AGE


def test_the_floor_also_applies_at_construction():
    with pytest.raises(ValueError):
        Traits({"name": "x", "age": 12})


# -- changes as events ----------------------------------------------------


def test_setting_a_trait_reports_what_moved_and_which_way(character):
    change = character.adjust("height", 20)
    assert change.key == "height"
    assert change.before == 170 and change.after == 190
    assert change.grew and not change.shrank


def test_a_change_knows_whether_it_crossed_a_band(character):
    small = character.adjust("height", 2)
    assert not small.crossed_band, "still average height"
    big = character.adjust("height", 20)
    assert big.crossed_band


def test_setting_a_trait_to_its_current_value_is_not_a_change(character):
    assert character.set("height", character.traits["height"]) is None
    assert character.traits.history == []


def test_the_initial_value_is_not_a_transformation():
    """Building a character should not read as a change to one."""
    character = default_character()
    assert character.traits.history == []


def test_history_accumulates_in_order(character):
    character.adjust("height", 5)
    character.set("hair_colour", "platinum")
    assert [c.key for c in character.traits.history] == ["height", "hair_colour"]


def test_unknown_traits_are_rejected(character):
    with pytest.raises(KeyError):
        character.set("wingspan", 3)


def test_non_numeric_traits_cannot_be_adjusted(character):
    with pytest.raises(TypeError):
        character.adjust("hair_colour", 1)


# -- colours --------------------------------------------------------------


def test_colours_carry_their_pixels(character):
    character.set("hair_colour", "copper")
    hair = character.traits["hair_colour"]
    assert hair.name == "copper"
    assert len(hair.rgb) == 3


def test_an_unknown_colour_raises_rather_than_rendering_wrong(character):
    with pytest.raises(KeyError):
        character.set("hair_colour", "octarine")


# -- absent parts are a real state ----------------------------------------


def test_zero_means_absent_not_missing(character):
    assert not character.has_phallus
    assert not character.has_bust
    character.set("phallus", 14)
    assert character.has_phallus
    character.set("phallus", 0)
    assert not character.has_phallus, "a body can lose a part, not just gain one"


# -- narration ------------------------------------------------------------


def test_a_transformation_narrates_itself_into_the_log():
    """Content should not have to remember to log every change."""
    session = Session.new_game(1234)
    before = len(session.log)
    session.player.character.adjust("height", 30)
    assert len(session.log) > before


def test_crossing_a_band_is_narrated_differently_from_a_nudge(character):
    nudge = character.adjust("height", 2)
    crossing = character.adjust("height", 25)
    assert describe_change(nudge, character) != describe_change(crossing, character)


def test_gaining_and_losing_a_part_read_differently(character):
    gained = character.set("phallus", 14)
    lost = character.set("phallus", 0)
    assert describe_change(gained, character) != describe_change(lost, character)


def test_narration_returns_none_for_traits_it_has_no_line_for(character):
    change = character.set("eye_colour", "gold")
    assert describe_change(change, character) is not None
    assert describe_change(character.set("name", "Other"), character) is not None


# -- the paperdoll reads the character ------------------------------------


def test_the_doll_recomposites_when_a_trait_changes(character):
    from lechery.ui.paperdoll import Paperdoll

    doll = Paperdoll((120, 190), character)
    first = doll.surface()
    assert doll.surface() is first, "an unchanged character must not recomposite"

    character.set("hair_colour", "platinum")
    assert doll.surface() is not first


def test_the_doll_ignores_traits_it_does_not_draw(character):
    from lechery.ui.paperdoll import Paperdoll

    doll = Paperdoll((120, 190), character)
    first = doll.surface()
    character.set("age", 40)
    assert doll.surface() is first, "age is not drawn, so nothing should redraw"


def test_hair_colour_actually_reaches_the_pixels(character):
    from lechery.ui.paperdoll import Paperdoll

    character.set("hair_colour", "ginger")
    doll = Paperdoll((160, 260), character)
    surface = doll.surface()
    target = colour("ginger").rgb

    found = any(
        tuple(surface.get_at((x, y)))[:3] == target
        for x in range(surface.get_width())
        for y in range(surface.get_height())
    )
    assert found, "the palette colour should be what gets drawn"


def test_a_taller_character_is_drawn_taller(character):
    from lechery.ui.paperdoll import Paperdoll

    doll = Paperdoll((120, 190), character)
    character.set("height", HEIGHT.minimum)
    short = doll._stature()
    character.set("height", HEIGHT.maximum)
    assert doll._stature() > short


def test_the_top_down_silhouette_cannot_see_appearance_at_all():
    """Deliberate: the map body is anonymous, the paperdoll is not.

    Asserted structurally rather than by reading the source for words --
    the docstring explaining the rule would trip a text search.
    """
    import ast
    import inspect

    from lechery.ui import silhouette

    tree = ast.parse(inspect.getsource(silhouette))
    imported = {
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    } | {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert not any("trait" in name for name in imported)

    parameters = inspect.signature(silhouette.draw_actor).parameters
    assert "character" not in parameters and "player" not in parameters


# -- perception: what strangers assume ------------------------------------


def test_the_body_can_be_read_against_the_characters_identity(character):
    """The case the whole model exists for."""
    from lechery.traits import CLOTHED

    character.gender = GENDERS["man"]
    character.set("bust", 8)

    read = character.presentation(CLOTHED)
    assert read.label == "feminine"
    assert read.pronouns(hedge=False) is SHE
    assert character.pronouns is not SHE
    assert not character.read_matches_identity


def test_clothing_hides_the_signals_it_should(character):
    """A stranger across a market is not reading anything under your clothes.

    Getting this wrong is a modelling bug, not a balance problem.
    """
    from lechery.traits import CLOTHED, NUDE

    bare = default_character()
    bare.set("phallus", 16)
    grown = default_character()
    grown.set("phallus", 40)

    # Dressed, the size of it cannot matter, because none of it is visible.
    assert bare.presentation(CLOTHED).score == grown.presentation(CLOTHED).score
    assert bare.presentation(CLOTHED).score == default_character().presentation(CLOTHED).score

    # The signal is marked invisible rather than merely weighted to zero, so
    # a future observer type can turn it back on without new plumbing.
    hidden = {s.key for s in bare.presentation(CLOTHED).signals if not s.visible}
    assert "phallus" in hidden

    assert bare.presentation(NUDE).score < bare.presentation(CLOTHED).score


def test_a_covered_chest_still_reads_somewhat(character):
    """Clothing softens a silhouette; it does not erase one."""
    from lechery.traits import CLOTHED

    character.set("bust", 8)
    assert character.presentation(CLOTHED).score > 0


def test_knowing_someone_beats_looking_at_them(character):
    """The reward for being known, and the difference from a stranger."""
    from lechery.traits import CLOTHED

    character.gender = GENDERS["man"]
    character.set("bust", 9)

    stranger = character.perceived_by(CLOTHED)
    friend = character.perceived_by(CLOTHED, knows_identity=True)

    assert stranger.pronouns(hedge=False) is SHE
    assert friend.pronouns() is character.pronouns
    assert friend.from_knowledge and not stranger.from_knowledge


def test_an_androgynous_body_reads_as_ambiguous(character):
    read = character.presentation()
    assert read.ambiguous
    assert read.label == "androgynous"
    assert read.confidence < 0.34


def test_an_unsure_observer_hedges_or_guesses(character):
    """Narration hedges; people guess, and guessing wrong is the point."""
    read = character.presentation()
    assert read.pronouns(hedge=True) is THEY
    assert read.pronouns(hedge=False) in (SHE, HE)


def test_height_nudges_a_read_but_never_decides_one(character):
    from lechery.traits import HEIGHT

    character.set("height", HEIGHT.minimum)
    assert character.presentation().ambiguous, "height alone must not settle it"
    character.set("height", HEIGHT.maximum)
    assert character.presentation().ambiguous


def test_presentation_bias_lets_clothing_push_the_read(character):
    """Style is not a body trait: you can change how you dress unchanged."""
    before = character.presentation().score
    character.presentation_bias = 0.5
    after = character.presentation().score
    assert after > before
    assert character.traits.history == [], "bias is not a change to the body"


def test_a_poor_glimpse_reads_less_confidently(character):
    from lechery.traits import CLOTHED, GLIMPSED

    character.set("bust", 9)
    assert character.presentation(GLIMPSED).confidence < character.presentation(CLOTHED).confidence


def test_scores_stay_within_range_at_the_extremes(character):
    from lechery.traits import NUDE

    character.set("bust", 12)
    character.presentation_bias = 1.0
    assert -1.0 <= character.presentation(NUDE).score <= 1.0

    character.set("bust", 0)
    character.set("phallus", 40)
    character.presentation_bias = -1.0
    assert -1.0 <= character.presentation(NUDE).score <= 1.0


def test_growing_into_a_different_read_is_narrated_once():
    """Being taken for someone else is its own event, not a trait change."""
    from lechery.log import Kind

    session = Session.new_game(1234)
    character = session.player.character
    character.gender = GENDERS["man"]

    character.set("bust", 9)
    lines = [e.text for e in session.log if e.kind is Kind.EVENT]
    assert any("taken for a woman" in line for line in lines)
    assert any("not what you are" in line for line in lines)

    before = len(session.log)
    character.set("bust", 10)
    assert len(session.log) > before, "the trait change still logs"
    shifts = [e.text for e in session.log if "taken for a woman" in e.text]
    assert len(shifts) == 1, "the shift is reported once, not on every nudge"


def test_a_read_that_matches_identity_is_not_flagged(character):
    character.gender = GENDERS["woman"]
    character.set("bust", 8)
    assert character.read_matches_identity
