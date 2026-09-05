"""Tests for stats, backstories, the screen stack, and character creation."""

import os

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

from lechery.content.backstories import BACKSTORIES, backstory  # noqa: E402
from lechery.stats import (  # noqa: E402
    SKILL_MAX,
    SKILLS,
    STAT_DEFAULT,
    STAT_MAX,
    Skills,
    Stat,
    StatBlock,
)
from lechery.ui.app import App  # noqa: E402
from lechery.ui.screens.base import Screen  # noqa: E402
from lechery.ui.screens.creation import STEPS, CharacterCreation  # noqa: E402
from lechery.ui.screens.menu import MainMenu  # noqa: E402
from lechery.ui.screens.play import PlayScreen  # noqa: E402


@pytest.fixture
def app():
    return App((1280, 760))


def click(pos):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)


# -- stats ----------------------------------------------------------------


def test_stats_default_to_ordinary():
    block = StatBlock()
    assert all(value == STAT_DEFAULT for _, value in block.items())
    assert block.spent == 0


def test_stats_are_clamped_to_their_range():
    block = StatBlock()
    block.set(Stat.VIGOUR, 999)
    assert block[Stat.VIGOUR] == STAT_MAX
    block.set(Stat.VIGOUR, -5)
    assert block[Stat.VIGOUR] >= 1


def test_skills_are_stored_sparsely():
    """An absent skill is untrained, not missing -- so the list can grow."""
    skills = Skills()
    assert skills.get("lore") == 0
    assert skills.ranks == {}
    skills.set("lore", 2)
    skills.set("lore", 0)
    assert skills.ranks == {}, "dropping to untrained should not leave a zero"


def test_skills_are_clamped_and_validated():
    skills = Skills()
    assert skills.set("lore", 99) == SKILL_MAX
    with pytest.raises(KeyError):
        skills.set("hacking", 1)


def test_trained_skills_come_back_best_first():
    skills = Skills()
    skills.set("lore", 1)
    skills.set("medicine", 3)
    assert [d.key for d, _ in skills.trained()] == ["medicine", "lore"]


# -- backstories ----------------------------------------------------------


def test_every_backstory_grants_stats_and_skills():
    for story in BACKSTORIES:
        stats, skills = StatBlock(), Skills()
        story.apply(stats, skills)
        assert stats.spent > 0, f"{story.id} grants no stats"
        assert skills.trained(), f"{story.id} grants no skills"


def test_backstories_are_roughly_balanced():
    """Not identical -- but no origin should be a strictly better pick."""
    budgets = []
    for story in BACKSTORIES:
        stats, skills = StatBlock(), Skills()
        story.apply(stats, skills)
        budgets.append(stats.spent + sum(r for _, r in skills.trained()))
    assert max(budgets) - min(budgets) <= 2


def test_every_backstory_names_only_real_skills():
    for story in BACKSTORIES:
        for key in story.skills:
            assert key in SKILLS, f"{story.id} grants unknown skill {key!r}"


def test_every_backstory_has_an_opening_line():
    """It is the only prose the player has before the world speaks."""
    for story in BACKSTORIES:
        assert story.opening.strip()
        assert story.tagline.strip()


def test_unknown_backstory_raises():
    with pytest.raises(KeyError):
        backstory("astronaut")


# -- the screen stack -----------------------------------------------------


def test_the_app_opens_on_the_menu(app):
    assert isinstance(app.screen, MainMenu)


def test_pushing_and_popping_returns_to_what_was_underneath(app):
    creation = app.push(CharacterCreation())
    assert app.screen is creation
    app.pop()
    assert isinstance(app.screen, MainMenu)


def test_popping_the_last_screen_quits(app):
    app.pop()
    assert not app.running


def test_a_resize_reaches_every_screen_on_the_stack(app):
    """Not just the top one, or going back lands on a stale layout."""
    class Recorder(Screen):
        def __init__(self):
            super().__init__()
            self.sizes = []

        def resize(self, window):
            self.sizes.append(window)

    recorder = Recorder()
    app.screens.insert(0, recorder)
    app.handle_event(pygame.event.Event(pygame.VIDEORESIZE, w=900, h=700))
    assert (900, 700) in recorder.sizes


def test_starting_a_game_replaces_creation_rather_than_stacking_it(app):
    """Escape from play must not land in a half-built character creator."""
    from lechery.traits import default_character

    app.push(CharacterCreation())
    app.start_game(default_character("Test"), seed=1)

    assert isinstance(app.screen, PlayScreen)
    assert not any(isinstance(s, CharacterCreation) for s in app.screens)
    assert isinstance(app.screens[0], MainMenu)


def test_the_menu_can_start_character_creation(app):
    new_game = app.screen.buttons[0]
    app.handle_event(click(new_game.rect.center))
    assert isinstance(app.screen, CharacterCreation)


def test_continue_is_shown_but_disabled_until_saving_exists(app):
    cont = app.screen.buttons[1]
    assert cont.label == "Continue"
    assert not cont.enabled


def test_the_menu_quit_button_stops_the_app(app):
    quit_button = [b for b in app.screen.buttons if b.label == "Quit"][0]
    app.handle_event(click(quit_button.rect.center))
    assert not app.running


# -- character creation ---------------------------------------------------


@pytest.fixture
def creation(app):
    return app.push(CharacterCreation())


def test_creation_starts_on_the_identity_step(creation):
    assert STEPS[creation.step].key == "identity"


def test_a_character_cannot_be_started_without_a_name(creation):
    assert not creation.can_advance
    creation.name = "Ilse"
    assert creation.can_advance


def test_typing_a_name_enables_the_next_button(creation):
    field = creation.widgets[0]
    creation.handle_event(click(field.rect.center))
    for letter in "Ilse":
        creation.handle_event(
            pygame.event.Event(pygame.KEYDOWN, key=ord(letter), unicode=letter)
        )
    assert creation.name == "Ilse"
    assert creation.buttons[-1].enabled


def test_the_preview_is_the_real_character_not_a_copy(creation):
    """One representation, so validation and the doll cannot disagree."""
    creation._set_trait("height", 190)
    assert creation.character.traits["height"] == 190
    assert creation.doll.character is creation.character


def test_changing_the_body_updates_the_doll(creation):
    creation.step = 1
    creation._build()
    before = creation.doll.surface()
    creation._set_trait("bust", 8)
    assert creation.doll.surface() is not before


def test_cycling_backstories_does_not_compound_their_bonuses(creation):
    """Applying deltas on top of the last one is the obvious bug here."""
    first = BACKSTORIES[0]
    creation._set_backstory(first)
    once = dict(creation.stats.values)

    for story in BACKSTORIES:
        creation._set_backstory(story)
    creation._set_backstory(first)

    assert dict(creation.stats.values) == once


def test_the_chosen_backstory_reaches_the_finished_character(creation):
    story = BACKSTORIES[1]
    creation._set_backstory(story)
    creation.name = "Ilse"
    character = creation.finish()

    assert character.backstory_id == story.id
    for key, rank in story.skills.items():
        assert character.skills.get(key) == rank


def test_creation_is_not_recorded_as_a_transformation(creation):
    """Choosing a body is not something that happened *to* the character."""
    creation._set_trait("height", 190)
    creation._set_trait("bust", 6)
    creation.name = "Ilse"
    character = creation.finish()
    assert character.traits.history == []


def test_an_unnamed_character_still_gets_a_name_at_the_end(creation):
    assert creation.finish().traits["name"]


def test_the_backstory_opening_is_the_first_prose_in_the_log(app, creation):
    creation.name = "Ilse"
    creation._set_backstory(BACKSTORIES[2])
    creation._begin()

    log = [e.text for e in app.screen.session.log]
    assert BACKSTORIES[2].opening in log


def test_stepping_forward_and_back_walks_the_steps(creation):
    creation.name = "Ilse"  # the first step will not advance without one
    for expected in range(1, len(STEPS)):
        creation._forward()
        assert creation.step == expected
    for expected in reversed(range(len(STEPS) - 1)):
        creation._back()
        assert creation.step == expected


def test_back_from_the_first_step_returns_to_the_menu(app, creation):
    creation._back()
    assert isinstance(app.screen, MainMenu)


def test_every_step_draws_at_both_form_factors(app):
    surface = pygame.display.get_surface()
    for size in [(1280, 760), (420, 860)]:
        host = App(size)
        creation = host.push(CharacterCreation())
        for index in range(len(STEPS)):
            creation.step = index
            creation._build()
            creation.draw(surface)


def test_the_doll_is_dropped_rather_than_shrunk_on_a_narrow_screen():
    """A thumbnail of a body is not a preview of one."""
    host = App((420, 860))
    creation = host.push(CharacterCreation())
    doll_rect, controls = creation._columns()
    assert doll_rect.width == 0
    assert controls.width > 300
