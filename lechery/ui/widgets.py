"""Small interactive widgets for the menu and creation screens.

Deliberately minimal: enough to build the screens that exist, with no
framework underneath. Each widget owns a rect, draws itself, and reports
whether it consumed an event -- which is all the coordination the screens
here need, and far less machinery than a retained-mode UI would impose.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional, Sequence

import pygame

from . import metrics
from .metrics import px
from .nativetext import (
    NativeInput,
    ask_text,
    available as native_available,
    in_browser,
)
from .text import TextStyle, wrap

TEXT = (206, 200, 196)
MUTED = (126, 120, 130)
ACCENT = (222, 192, 136)
FIELD_BG = (26, 23, 31)
FIELD_EDGE = (58, 52, 66)
FIELD_HOVER = (40, 36, 48)
DISABLED = (78, 74, 84)

ROW_HEIGHT = 38
ARROW_WIDTH = 30


class Widget:
    """Base: a rect that can draw and maybe consume events."""

    def __init__(self, rect: pygame.Rect, style: TextStyle) -> None:
        self.rect = rect
        self.style = style
        self.hovered = False
        self.enabled = True

    def destroy(self) -> None:
        """Release anything outside pygame's world. Overridden where needed.

        Screens rebuild their widgets freely, so anything a widget puts in
        the page has to come back out with it.
        """

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        return False

    def draw(self, surface: pygame.Surface) -> None:  # pragma: no cover - base
        raise NotImplementedError

    def _clicked(self, event: pygame.event.Event, rect: Optional[pygame.Rect] = None) -> bool:
        return (
            self.enabled
            and event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and (rect or self.rect).collidepoint(event.pos)
        )


class Button(Widget):
    def __init__(
        self,
        rect: pygame.Rect,
        label: str,
        style: TextStyle,
        on_click: Optional[Callable[[], None]] = None,
        *,
        primary: bool = False,
    ) -> None:
        super().__init__(rect, style)
        self.label = label
        self.on_click = on_click
        self.primary = primary

    def handle_event(self, event: pygame.event.Event) -> bool:
        super().handle_event(event)
        if self._clicked(event):
            if self.on_click is not None:
                self.on_click()
            return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        background = FIELD_HOVER if (self.hovered and self.enabled) else FIELD_BG
        pygame.draw.rect(surface, background, self.rect, border_radius=px(4))
        pygame.draw.rect(
            surface,
            ACCENT if (self.primary and self.enabled) else FIELD_EDGE,
            self.rect,
            width=px(1),
            border_radius=px(4),
        )
        colour = TEXT if self.enabled else DISABLED
        if self.primary and self.enabled:
            colour = ACCENT
        text = self.style.font.render(self.label, True, colour)
        surface.blit(text, text.get_rect(center=self.rect.center))


class Cycler(Widget):
    """A labelled value with arrows either side.

    Used instead of a dropdown because a dropdown needs an overlay layer and
    a click-outside rule, and every option list here is short enough that
    stepping through it is no worse.
    """

    def __init__(
        self,
        rect: pygame.Rect,
        label: str,
        options: Sequence,
        style: TextStyle,
        *,
        index: int = 0,
        format: Optional[Callable[[object], str]] = None,
        on_change: Optional[Callable[[object], None]] = None,
    ) -> None:
        super().__init__(rect, style)
        self.label = label
        self.options = list(options)
        self.index = max(0, min(index, len(self.options) - 1))
        self.format = format or str
        self.on_change = on_change

    @property
    def value(self):
        return self.options[self.index]

    def set_value(self, value) -> None:
        if value in self.options:
            self.index = self.options.index(value)

    def _step(self, delta: int) -> None:
        self.index = (self.index + delta) % len(self.options)
        if self.on_change is not None:
            self.on_change(self.value)

    @property
    def left_rect(self) -> pygame.Rect:
        return pygame.Rect(self.rect.x, self.rect.y, px(ARROW_WIDTH), self.rect.height)

    @property
    def right_rect(self) -> pygame.Rect:
        return pygame.Rect(
            self.rect.right - px(ARROW_WIDTH), self.rect.y, px(ARROW_WIDTH), self.rect.height
        )

    def handle_event(self, event: pygame.event.Event) -> bool:
        super().handle_event(event)
        if self._clicked(event, self.left_rect):
            self._step(-1)
            return True
        if self._clicked(event, self.right_rect):
            self._step(1)
            return True
        if self._clicked(event):
            self._step(1)  # clicking the body advances, like a toggle
            return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        font = self.style.font
        surface.blit(font.render(self.label, True, MUTED), (self.rect.x, self.rect.y - px(18)))

        pygame.draw.rect(surface, FIELD_BG, self.rect, border_radius=px(4))
        pygame.draw.rect(surface, FIELD_EDGE, self.rect, width=px(1), border_radius=px(4))

        for rect, glyph in ((self.left_rect, "‹"), (self.right_rect, "›")):
            hovered = rect.collidepoint(pygame.mouse.get_pos())
            text = font.render(glyph, True, ACCENT if hovered else MUTED)
            surface.blit(text, text.get_rect(center=rect.center))

        value = font.render(self.format(self.value), True, TEXT)
        surface.blit(value, value.get_rect(center=self.rect.center))


class Slider(Widget):
    """A numeric value dragged along a track."""

    def __init__(
        self,
        rect: pygame.Rect,
        label: str,
        style: TextStyle,
        *,
        minimum: float,
        maximum: float,
        value: float,
        step: float = 1.0,
        format: Optional[Callable[[float], str]] = None,
        on_change: Optional[Callable[[float], None]] = None,
    ) -> None:
        super().__init__(rect, style)
        self.label = label
        self.minimum = minimum
        self.maximum = maximum
        self.value = value
        self.step = step
        self.format = format or (lambda v: str(int(v)))
        self.on_change = on_change
        self.dragging = False

    @property
    def fraction(self) -> float:
        span = self.maximum - self.minimum
        return 0.0 if span <= 0 else (self.value - self.minimum) / span

    def set_from_x(self, x: int) -> None:
        span = self.maximum - self.minimum
        fraction = max(0.0, min(1.0, (x - self.rect.x) / max(self.rect.width, 1)))
        raw = self.minimum + fraction * span
        stepped = round(raw / self.step) * self.step
        value = max(self.minimum, min(self.maximum, stepped))
        if value != self.value:
            self.value = value
            if self.on_change is not None:
                self.on_change(value)

    def handle_event(self, event: pygame.event.Event) -> bool:
        super().handle_event(event)
        if self._clicked(event):
            self.dragging = True
            self.set_from_x(event.pos[0])
            return True
        if event.type == pygame.MOUSEMOTION and self.dragging:
            self.set_from_x(event.pos[0])
            return True
        if event.type == pygame.MOUSEBUTTONUP and self.dragging:
            self.dragging = False
            return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        font = self.style.font
        surface.blit(font.render(self.label, True, MUTED), (self.rect.x, self.rect.y - px(18)))
        value = font.render(self.format(self.value), True, TEXT)
        surface.blit(value, (self.rect.right - value.get_width(), self.rect.y - px(18)))

        track = pygame.Rect(self.rect.x, self.rect.centery - px(2), self.rect.width, px(4))
        pygame.draw.rect(surface, FIELD_BG, track, border_radius=px(2))
        filled = pygame.Rect(track.x, track.y, int(track.width * self.fraction), track.height)
        pygame.draw.rect(surface, FIELD_EDGE, filled, border_radius=px(2))

        knob_x = self.rect.x + int(self.rect.width * self.fraction)
        pygame.draw.circle(surface, ACCENT, (knob_x, self.rect.centery), px(7))


class TextField(Widget):
    """A single-line text input."""

    def __init__(
        self,
        rect: pygame.Rect,
        label: str,
        style: TextStyle,
        *,
        text: str = "",
        max_length: int = 40,
        placeholder: str = "",
        on_change: Optional[Callable[[str], None]] = None,
    ) -> None:
        super().__init__(rect, style)
        self.label = label
        self.text = text
        self.max_length = max_length
        self.placeholder = placeholder
        self.on_change = on_change
        self.focused = False

        # In a browser the text is edited in a real input element laid over
        # this rect; there is no way to raise a phone keyboard otherwise.
        # Whether or not that element exists, a tap that reaches pygame in a
        # browser is handled by the prompt dialog -- so the field stays
        # usable if the overlay is disabled or fails to receive input.
        self.in_browser = in_browser()
        self.native: Optional[NativeInput] = None
        if native_available():
            self.native = NativeInput(
                rect,
                text=text,
                max_length=max_length,
                placeholder=placeholder,
                colour="#cec8c4",
                # The font was built at device resolution; the page wants
                # CSS pixels, same as the geometry.
                font_size=round(style.font.get_height() / max(metrics.SCALE, 1.0)),
            )

    def _ask_with_dialog(self) -> None:
        """Edit the value through the browser's prompt dialog."""
        answer = ask_text(self.label or "Name", self.text)
        if answer is None:
            return
        self.text = answer[: self.max_length]
        if self.native is not None and self.native.element is not None:
            try:
                self.native.element.value = self.text
            except Exception:
                pass
        if self.on_change is not None:
            self.on_change(self.text)

    def sync(self) -> bool:
        """Adopt whatever the native input holds. Returns whether it moved.

        Polled rather than driven by events: the element belongs to the
        page, and its edits never reach pygame's queue at all.
        """
        if self.native is None:
            return False
        self.native.move(self.rect)
        value = self.native.value
        self.focused = self.native.focused
        if value == self.text:
            return False
        self.text = value
        if self.on_change is not None:
            self.on_change(self.text)
        return True

    def destroy(self) -> None:
        if self.native is not None:
            self.native.destroy()
            self.native = None

    def handle_event(self, event: pygame.event.Event) -> bool:
        super().handle_event(event)

        if self.in_browser:
            # With an overlay, the element takes the tap and pygame never
            # sees it. A tap arriving *here* means it did not -- no overlay,
            # wrong stacking, or a browser routing taps to the canvas
            # anyway. Either way the dialog handles it, so whichever path
            # receives the tap is the one that answers.
            if (
                event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and self.rect.collidepoint(event.pos)
            ):
                self._ask_with_dialog()
                return True
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Clicking elsewhere unfocuses, so typing cannot land in a field
            # the player has visibly moved away from.
            self.focused = self.rect.collidepoint(event.pos)
            return self.focused

        if not self.focused or event.type != pygame.KEYDOWN:
            return False

        if event.key == pygame.K_BACKSPACE:
            self.text = self.text[:-1]
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_ESCAPE):
            self.focused = False
            return True
        elif event.unicode and event.unicode.isprintable():
            if len(self.text) < self.max_length:
                self.text += event.unicode
        else:
            return False

        if self.on_change is not None:
            self.on_change(self.text)
        return True

    def draw(self, surface: pygame.Surface) -> None:
        self.sync()
        font = self.style.font
        surface.blit(font.render(self.label, True, MUTED), (self.rect.x, self.rect.y - px(18)))

        pygame.draw.rect(surface, FIELD_BG, self.rect, border_radius=px(4))
        pygame.draw.rect(
            surface, ACCENT if self.focused else FIELD_EDGE, self.rect, width=px(1),
            border_radius=px(4)
        )

        if self.native is not None:
            # A native input is drawing the text itself; drawing ours too
            # would double it, offset by a pixel or two.
            return

        shown = self.text or self.placeholder
        colour = TEXT if self.text else MUTED
        text = font.render(shown, True, colour)
        surface.blit(text, (self.rect.x + px(10), self.rect.centery - text.get_height() // 2))

        if self.focused and (pygame.time.get_ticks() // 500) % 2 == 0:
            x = self.rect.x + px(12) + font.size(self.text)[0]
            pygame.draw.line(
                surface, ACCENT, (x, self.rect.y + px(8)), (x, self.rect.bottom - px(8)), px(1)
            )


@dataclass
class Paragraph:
    """Wrapped read-only prose, laid out once per width change."""

    style: TextStyle
    text: str = ""
    colour: tuple[int, int, int] = MUTED
    _width: int = field(default=0, repr=False)
    _lines: list[str] = field(default_factory=list, repr=False)

    def draw(self, surface: pygame.Surface, rect: pygame.Rect) -> int:
        if rect.width != self._width:
            self._width = rect.width
            self._lines = wrap(self.text, self.style.font, rect.width)
        y = rect.y
        for line in self._lines:
            surface.blit(self.style.font.render(line, True, self.colour), (rect.x, y))
            y += self.style.line_height
        return y

    def set_text(self, text: str) -> None:
        if text != self.text:
            self.text = text
            self._width = 0  # force a re-wrap
