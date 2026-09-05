"""Character creation: who you were, and what you woke up as.

Four steps, with the paperdoll beside them the whole time. The doll updates
as the sliders move because appearance choices are meaningless as numbers --
"height 178" tells you nothing until you can see it, and this game asks the
player to care about that body for the rest of the run.

The character is built into a live Character from the first frame rather
than collected into a form and constructed at the end. That way the preview
is the real thing, the same validation runs, and there is no second
representation of a character to keep in step.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

import pygame

from ...content.backstories import BACKSTORIES, Backstory
from ...stats import CREATION_POINTS, STAT_DEFAULT, Stat, StatBlock, Skills
from ...traits import EYE_COLOURS, HAIR_COLOURS, GENDERS, PRONOUN_SETS
from ...traits.character import Character, default_character
from ...traits.identity import Gender
from ...traits.scale import BUST, HEIGHT, PHALLUS, cup_size
from ...traits.traits import Traits
from ..fonts import load as load_font
from ..metrics import design, px
from .. import avatar as avatar_module
from ..paperdoll import Paperdoll
from ..text import TextStyle
from ..widgets import (
    ACCENT,
    MUTED,
    TEXT,
    Button,
    Cycler,
    Paragraph,
    Slider,
    TextField,
    Widget,
)
from .base import Screen

BACKGROUND = (13, 12, 16)
PANEL = (19, 17, 23)
HEADING = (226, 200, 148)
RULE = (48, 43, 56)
GOOD = (150, 178, 148)
BAD = (196, 132, 124)

MARGIN = 34
DOLL_WIDTH = 250
ROW_GAP = 46
FOOTER = 78

#: Below this width the doll goes above the controls instead of beside them.
STACK_BELOW = 760

#: How much of the body a stacked doll band may take. Capped as a fraction
#: as well as in pixels so a short landscape window does not give the figure
#: the whole screen and leave the controls off the bottom.
STACK_BAND = 190
STACK_BAND_FRACTION = 0.32


@dataclass
class Step:
    key: str
    title: str
    blurb: str


STEPS = (
    Step("identity", "Who are you?", "The parts of you that the change did not touch."),
    Step("body", "What did you wake up in?", "It will not stay this way."),
    Step("origin", "Where were you?", "Before. What you knew there, you still know."),
    Step("confirm", "Ready", "This is where it starts."),
)


class CharacterCreation(Screen):
    def __init__(self) -> None:
        super().__init__()
        #: Held here rather than on the character until the end: the model
        #: rejects an empty name, and it must be legal to backspace a field
        #: to empty mid-edit. finish() is what commits it, through the same
        #: validation as everything else.
        self.name = ""
        self.character = default_character("Wanderer")
        self.stats = StatBlock()
        self.skills = Skills()
        self.backstory_index = 0
        self.step = 0

        self.heading_font = load_font("heading", 26, bold=True)
        self.body = TextStyle(load_font("body", 15))
        self.small = TextStyle(load_font("body", 13))

        self.doll = Paperdoll((1, 1), self.character)
        # The drawn avatar exists only in a browser; the placeholder figure
        # stays for the desktop. Shown on every creation step, not just one.
        self.avatar = avatar_module.shared() if avatar_module.available() else None
        self.blurb = Paragraph(self.small, "", MUTED)
        self.detail = Paragraph(self.small, "", MUTED)

        self.widgets: list[Widget] = []
        self.buttons: list[Button] = []

    # -- lifecycle --------------------------------------------------------

    def enter(self, app) -> None:
        super().enter(app)
        self._apply_backstory()
        self._build()

    def leave(self) -> None:
        for widget in self.widgets:
            widget.destroy()
        self.widgets = []

    def resize(self, window: tuple[int, int]) -> None:
        self._build()

    @property
    def backstory(self) -> Backstory:
        return BACKSTORIES[self.backstory_index]

    # -- layout -----------------------------------------------------------

    @property
    def stacked(self) -> bool:
        """Whether the doll sits above the controls rather than beside them.

        Compared in design units. Against raw pixels a phone measures wider
        than a laptop, and lays itself out accordingly.
        """
        return design(self.app.window[0]) < STACK_BELOW

    def _columns(self) -> tuple[pygame.Rect, pygame.Rect]:
        """The doll's area and the controls' area.

        Side by side when there is width for it. When there is not, the doll
        goes above rather than away -- it is the whole reason the sliders
        mean anything, and a creation screen without it is a form.
        """
        width, height = self.app.window
        body = pygame.Rect(
            px(MARGIN), px(120), width - px(MARGIN) * 2, height - px(120) - px(FOOTER)
        )

        if self.stacked:
            band = min(px(STACK_BAND), int(body.height * STACK_BAND_FRACTION))
            doll = pygame.Rect(body.x, body.y, body.width, band)
            controls = pygame.Rect(
                body.x, doll.bottom + px(12), body.width, body.height - band - px(12)
            )
            return doll, controls

        doll = pygame.Rect(body.x, body.y, px(DOLL_WIDTH), body.height)
        controls = pygame.Rect(
            doll.right + px(MARGIN), body.y, body.width - px(DOLL_WIDTH) - px(MARGIN), body.height
        )
        return doll, controls

    def _build(self) -> None:
        if self.app is None:
            return
        _, controls = self._columns()
        # Widgets can own page elements; rebuilding without releasing them
        # leaves invisible inputs stacked over the canvas eating taps.
        for widget in self.widgets:
            widget.destroy()
        self.widgets = []

        builder = {
            "identity": self._build_identity,
            "body": self._build_body,
            "origin": self._build_origin,
            "confirm": self._build_confirm,
        }[STEPS[self.step].key]
        builder(controls)
        self._build_footer()

    def _rows(self, rect: pygame.Rect, count: int) -> list[pygame.Rect]:
        return [
            pygame.Rect(rect.x, rect.y + px(24) + index * px(ROW_GAP), rect.width, px(32))
            for index in range(count)
        ]

    # -- steps ------------------------------------------------------------

    def _build_identity(self, rect: pygame.Rect) -> None:
        rows = self._rows(rect, 3)
        genders = list(GENDERS.values())

        name = TextField(
            rows[0],
            "Name",
            self.body,
            text=self.name,
            placeholder="What they called you",
            on_change=self._set_name,
        )
        gender = Cycler(
            rows[1],
            "Gender",
            genders,
            self.body,
            index=self._index_of_gender(genders),
            format=lambda g: g.label,
            on_change=self._set_gender,
        )
        pronouns = Cycler(
            rows[2],
            "Pronouns",
            list(PRONOUN_SETS.values()),
            self.body,
            index=list(PRONOUN_SETS.values()).index(self.character.pronouns)
            if self.character.pronouns in PRONOUN_SETS.values()
            else 2,
            format=str,
            on_change=self._set_pronouns,
        )
        self.widgets = [name, gender, pronouns]

    def _build_body(self, rect: pygame.Rect) -> None:
        rows = self._rows(rect, 6)
        traits = self.character.traits

        self.widgets = [
            Slider(
                rows[0], "Age", self.body,
                minimum=18, maximum=60, value=float(traits["age"]),
                format=lambda v: f"{int(v)}",
                on_change=lambda v: self._set_trait("age", v),
            ),
            Slider(
                rows[1], "Height", self.body,
                minimum=HEIGHT.minimum, maximum=HEIGHT.maximum, value=float(traits["height"]),
                format=lambda v: f"{int(v)}cm · {HEIGHT.label(v)}",
                on_change=lambda v: self._set_trait("height", v),
            ),
            Cycler(
                rows[2], "Hair", list(HAIR_COLOURS), self.body,
                index=self._index_of_colour(HAIR_COLOURS, "hair_colour"),
                format=lambda c: c.name,
                on_change=lambda c: self._set_trait("hair_colour", c),
            ),
            Cycler(
                rows[3], "Eyes", list(EYE_COLOURS), self.body,
                index=self._index_of_colour(EYE_COLOURS, "eye_colour"),
                format=lambda c: c.name,
                on_change=lambda c: self._set_trait("eye_colour", c),
            ),
            Slider(
                rows[4], "Bust", self.body,
                minimum=BUST.minimum, maximum=BUST.maximum, value=float(traits["bust"]),
                format=lambda v: cup_size(v),
                on_change=lambda v: self._set_trait("bust", v),
            ),
            Slider(
                rows[5], "Phallus", self.body,
                minimum=PHALLUS.minimum, maximum=PHALLUS.maximum, value=float(traits["phallus"]),
                format=lambda v: PHALLUS.label(v) if v < 1 else f"{int(v)}cm · {PHALLUS.label(v)}",
                on_change=lambda v: self._set_trait("phallus", v),
            ),
        ]

    def _build_origin(self, rect: pygame.Rect) -> None:
        row = pygame.Rect(rect.x, rect.y + px(24), rect.width, px(32))
        self.widgets = [
            Cycler(
                row,
                "Before you were pulled here",
                list(BACKSTORIES),
                self.body,
                index=self.backstory_index,
                format=lambda b: b.name,
                on_change=self._set_backstory,
            )
        ]

    def _build_confirm(self, rect: pygame.Rect) -> None:
        self.widgets = []

    # -- callbacks --------------------------------------------------------

    def _set_name(self, text: str) -> None:
        self.name = text

    def _set_gender(self, gender: Gender) -> None:
        self.character.gender = gender
        self.character.pronoun_override = None
        self._build()  # the pronoun cycler follows the gender

    def _set_pronouns(self, pronouns) -> None:
        self.character.pronoun_override = pronouns

    def _set_trait(self, key: str, value) -> None:
        self.character.traits.set(key, value)

    def _set_backstory(self, backstory: Backstory) -> None:
        self.backstory_index = list(BACKSTORIES).index(backstory)
        self._apply_backstory()

    def _apply_backstory(self) -> None:
        """Rebuild stats from scratch, then apply.

        Applying deltas on top of the last backstory's would compound every
        time the player cycles through the list.
        """
        self.stats = StatBlock()
        self.skills = Skills()
        self.backstory.apply(self.stats, self.skills)

    def _index_of_gender(self, genders: list[Gender]) -> int:
        try:
            return genders.index(self.character.gender)
        except ValueError:
            return 0

    def _index_of_colour(self, palette, key: str) -> int:
        current = self.character.traits.get(key)
        for index, colour in enumerate(palette):
            if colour == current:
                return index
        return 0

    # -- navigation -------------------------------------------------------

    @property
    def can_advance(self) -> bool:
        if STEPS[self.step].key == "identity":
            return bool(self.name.strip())
        return True

    def _build_footer(self) -> None:
        width, height = self.app.window
        y = height - px(FOOTER) + px(16)
        back = Button(
            pygame.Rect(px(MARGIN), y, px(130), px(42)),
            "Back" if self.step else "Menu",
            self.body,
            self._back,
        )
        label = "Begin" if self.step == len(STEPS) - 1 else "Next"
        forward = Button(
            pygame.Rect(width - px(MARGIN) - px(160), y, px(160), px(42)),
            label,
            self.body,
            self._forward,
            primary=True,
        )
        forward.enabled = self.can_advance
        self.buttons = [back, forward]

    def _back(self) -> None:
        if self.step:
            self.step -= 1
            self._build()
        else:
            self.app.pop()

    def _forward(self) -> None:
        if not self.can_advance:
            return
        if self.step < len(STEPS) - 1:
            self.step += 1
            self._build()
        else:
            self._begin()

    def _begin(self) -> None:
        character = self.finish()
        self.app.start_game(character, opening=self.backstory.opening)

    def finish(self) -> Character:
        """Seal the character. Also the seam a test can drive without a UI."""
        self.character.stats = self.stats.copy()
        self.character.skills = self.skills.copy()
        self.character.backstory_id = self.backstory.id
        self.character.traits.set("name", self.name.strip() or "Wanderer")
        # Creation is not a transformation: nothing that happened here should
        # read as something that happened *to* the character.
        self.character.traits.history.clear()
        return self.character

    # -- frame ------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._back()
            return True

        # Native inputs are edited in the page, so their value is polled
        # rather than arriving as events.
        for widget in self.widgets:
            if hasattr(widget, "sync"):
                widget.sync()

        consumed = False
        for widget in self.widgets:
            if widget.handle_event(event):
                consumed = True
        for button in self.buttons:
            if button.handle_event(event):
                consumed = True

        # The Begin button enables the moment a name exists, so the footer
        # is refreshed after any input rather than only on step changes.
        if self.buttons:
            self.buttons[-1].enabled = self.can_advance
        return consumed

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(BACKGROUND)
        width, _ = surface.get_size()
        step = STEPS[self.step]

        heading = self.heading_font.render(step.title, True, HEADING)
        surface.blit(heading, (px(MARGIN), px(44)))

        self.blurb.set_text(step.blurb)
        self.blurb.draw(
            surface, pygame.Rect(px(MARGIN), px(84), width - px(MARGIN) * 2, px(24))
        )

        pygame.draw.line(
            surface, RULE, (px(MARGIN), px(112)), (width - px(MARGIN), px(112))
        )
        self._draw_progress(surface, width)

        doll_rect, controls = self._columns()
        if doll_rect.width:
            self._draw_doll(surface, doll_rect)

        for widget in self.widgets:
            widget.draw(surface)

        if STEPS[self.step].key == "origin":
            self._draw_backstory(surface, controls)
        elif STEPS[self.step].key == "confirm":
            self._draw_summary(surface, controls)

        for button in self.buttons:
            button.draw(surface)

    def _draw_progress(self, surface: pygame.Surface, width: int) -> None:
        x = width - px(MARGIN) - len(STEPS) * px(22)
        for index in range(len(STEPS)):
            colour = ACCENT if index <= self.step else RULE
            pygame.draw.circle(surface, colour, (x + index * px(22), px(58)), px(4))

    def _identity_lines(self) -> list[tuple[str, tuple[int, int, int]]]:
        character = self.character
        return [
            (self.name.strip() or "unnamed", TEXT),
            (f"{character.gender} · {character.pronouns}", MUTED),
            (f"read as {character.presentation().label}", MUTED),
        ]

    def _draw_doll(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        if self.stacked:
            self._draw_doll_banded(surface, rect)
        else:
            self._draw_doll_column(surface, rect)

    def _blit_figure(self, surface: pygame.Surface, figure_rect: pygame.Rect) -> None:
        """Draw the character's body into `figure_rect`.

        The real avatar when the browser has it, the primitive placeholder
        otherwise. Placed every frame so the page element it uses is not
        taken down by the end-of-frame sweep.
        """
        if self.avatar is not None:
            self.avatar.update(self.character)
            self.avatar.place(figure_rect)
            return
        self.doll.resize((figure_rect.width, figure_rect.height))
        surface.blit(self.doll.surface(), figure_rect)

    def _draw_doll_column(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        height = min(rect.height - px(90), int(rect.width * 1.5))
        width = int(height * 0.62)
        figure_rect = pygame.Rect(0, 0, width, height)
        figure_rect.midtop = (rect.centerx, rect.y)
        self._blit_figure(surface, figure_rect)

        y = rect.y + height + px(14)
        for line, colour in self._identity_lines():
            text = self.small.font.render(line, True, colour)
            surface.blit(text, text.get_rect(midtop=(rect.centerx, y)))
            y += self.small.line_height + px(2)

    def _draw_doll_banded(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        """Stacked: the figure at the left of the band, its lines beside it.

        Putting the text alongside rather than underneath is what makes the
        band affordable -- on a phone the vertical space it would otherwise
        cost is space the sliders need.
        """
        height = rect.height
        width = int(height * 0.62)
        figure_rect = pygame.Rect(rect.x, rect.y, width, height)
        self._blit_figure(surface, figure_rect)

        lines = self._identity_lines()
        block = len(lines) * (self.small.line_height + px(2))
        x = rect.x + width + px(18)
        y = rect.centery - block // 2
        for line, colour in lines:
            surface.blit(self.small.font.render(line, True, colour), (x, y))
            y += self.small.line_height + px(2)

    def _draw_backstory(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        backstory = self.backstory
        y = rect.y + px(84)

        tagline = self.small.font.render(backstory.tagline, True, ACCENT)
        surface.blit(tagline, (rect.x, y))
        y += self.small.line_height + px(10)

        self.detail.set_text(backstory.description)
        y = self.detail.draw(surface, pygame.Rect(rect.x, y, rect.width, px(100))) + px(16)

        self._draw_sheet(surface, pygame.Rect(rect.x, y, rect.width, px(200)))

    def _draw_summary(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        y = rect.y + px(24)
        character = self.character
        lines = [
            (self.name.strip() or "Wanderer", TEXT),
            (f"{character.gender} · {character.pronouns}", MUTED),
            (character.traits.describe("age") + " · " + character.traits.describe("height"), MUTED),
            (
                f"{character.traits.label('hair_colour')} hair, "
                f"{character.traits.label('eye_colour')} eyes",
                MUTED,
            ),
            (self.backstory.name, ACCENT),
        ]
        for line, colour in lines:
            surface.blit(self.small.font.render(line, True, colour), (rect.x, y))
            y += self.small.line_height + px(4)

        self._draw_sheet(surface, pygame.Rect(rect.x, y + px(12), rect.width, px(220)))

    def _draw_sheet(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        """Stats and skills, so the choice's consequences are visible."""
        font = self.small.font
        y = rect.y
        for stat in Stat:
            value = self.stats[stat]
            colour = TEXT if value == STAT_DEFAULT else (GOOD if value > STAT_DEFAULT else BAD)
            surface.blit(font.render(stat.label, True, MUTED), (rect.x, y))
            text = font.render(f"{value}  {self.stats.label(stat)}", True, colour)
            surface.blit(text, (rect.x + px(110), y))
            y += self.small.line_height + px(2)

        y += px(8)
        for definition, rank in self.skills.trained():
            surface.blit(font.render(definition.label, True, MUTED), (rect.x, y))
            surface.blit(
                font.render(self.skills.label(definition.key), True, TEXT), (rect.x + px(110), y)
            )
            y += self.small.line_height + px(2)
