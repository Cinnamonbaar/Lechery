"""Text rendering boilerplate.

Pygame gives you `Font.render` and nothing else -- no wrapping, no layout, no
caching. This module is the missing layer. Wrapping a paragraph means
measuring every candidate line, which is far too slow to redo at 60fps, so
laid-out results are cached and only recomputed when the text or the width
changes.
"""

from __future__ import annotations

from dataclasses import dataclass

import pygame


@dataclass(frozen=True)
class TextStyle:
    font: pygame.font.Font
    color: tuple[int, int, int] = (222, 216, 208)
    line_spacing: float = 1.35

    @property
    def line_height(self) -> int:
        return int(self.font.get_linesize() * self.line_spacing)


def wrap(text: str, font: pygame.font.Font, width: int) -> list[str]:
    """Greedy word wrap to `width` pixels, honouring explicit newlines.

    A word longer than the line is broken mid-word rather than allowed to
    overflow the box.
    """
    lines: list[str] = []
    for paragraph in text.split("\n"):
        if not paragraph.strip():
            lines.append("")
            continue
        line = ""
        for word in paragraph.split(" "):
            candidate = f"{line} {word}".strip()
            if line and font.size(candidate)[0] > width:
                lines.append(line)
                line = word
            else:
                line = candidate
            while font.size(line)[0] > width and len(line) > 1:
                cut = len(line) - 1
                while cut > 1 and font.size(line[:cut])[0] > width:
                    cut -= 1
                lines.append(line[:cut])
                line = line[cut:]
        lines.append(line)
    return lines


class TextBlock:
    """A wrapped paragraph that re-lays-out only when it has to."""

    def __init__(self, style: TextStyle, text: str = "", width: int = 0) -> None:
        self.style = style
        self._text = text
        self._width = width
        self._lines: list[str] = []
        self._dirty = True

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        if value != self._text:
            self._text = value
            self._dirty = True

    @property
    def width(self) -> int:
        return self._width

    @width.setter
    def width(self, value: int) -> None:
        if value != self._width:
            self._width = value
            self._dirty = True

    @property
    def lines(self) -> list[str]:
        if self._dirty:
            self._lines = wrap(self._text, self.style.font, self._width) if self._width else []
            self._dirty = False
        return self._lines

    @property
    def height(self) -> int:
        return len(self.lines) * self.style.line_height

    def draw(self, surface: pygame.Surface, x: int, y: int) -> int:
        """Blit the block; returns the y coordinate just past the last line."""
        line_height = self.style.line_height
        for index, line in enumerate(self.lines):
            if line:
                surface.blit(
                    self.style.font.render(line, True, self.style.color),
                    (x, y + index * line_height),
                )
        return y + self.height
