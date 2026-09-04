"""The root view: panes, input, and the layout they arrange themselves into.

Owns the layout and hands each pane its rect every frame, so a collapse, a
resize or a change of form factor needs no cached geometry anywhere else.
"""

from __future__ import annotations

import pygame

from ..session import Session
from ..settings import LayoutMode, Settings
from .layout import Layout, make_layout
from .logpanel import LogPanel
from .paperdollpanel import PaperdollPanel
from .fonts import load as load_font
from .profile import FormFactor, resolve
from .text import TextStyle
from .touch import Thumbstick
from .worldview import WorldView

BACKGROUND = (12, 11, 14)
SCRIM = (0, 0, 0, 140)
HANDLE_BG = (26, 23, 31, 220)
HANDLE_EDGE = (74, 68, 82)
HANDLE_MARK = (188, 178, 196)


class App:
    def __init__(
        self,
        session: Session,
        size: tuple[int, int],
        settings: Settings | None = None,
    ) -> None:
        self.session = session
        self.settings = settings or Settings()
        self.window = size

        self.form = resolve(self.settings.layout_mode, size)
        self.layout = self._make_layout()
        self.stick = Thumbstick()

        body = TextStyle(load_font("body", 15))
        heading = TextStyle(load_font("heading", 13, bold=True))
        tab = TextStyle(load_font("heading", 12, bold=True))

        self.paperdoll = PaperdollPanel(session.player, body, tab)
        self.paperdoll.style = heading
        self.log = LogPanel(session.log, body, tab)
        self.world = WorldView(session, self.layout.center)

    # -- layout -----------------------------------------------------------

    def _make_layout(self) -> Layout:
        if self.form is FormFactor.WIDE:
            return make_layout(
                self.form,
                self.window,
                left_open=self.settings.wide_left_open,
                right_open=self.settings.wide_right_open,
            )
        return make_layout(self.form, self.window)

    def _refresh_form(self) -> None:
        """Re-evaluate the form factor, rebuilding the layout if it changed.

        Only on a change: rebuilding every frame would throw away which
        drawers the player had open.
        """
        form = resolve(self.settings.layout_mode, self.window)
        if form is self.form:
            self.layout.window = self.window
            return
        self.form = form
        self.layout = self._make_layout()

    def set_layout_mode(self, mode: LayoutMode) -> None:
        """The settings override. Persists, so the choice survives a restart."""
        self.settings.layout_mode = mode
        self._refresh_form()
        self.settings.save()

    @property
    def uses_touch_controls(self) -> bool:
        if self.settings.touch_controls is not None:
            return self.settings.touch_controls
        return self.form is FormFactor.COMPACT

    # -- input ------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.VIDEORESIZE:
            self.window = (event.w, event.h)
            self._refresh_form()
            return

        if event.type == pygame.KEYDOWN and self._handle_key(event):
            return

        if self.uses_touch_controls and self.stick.handle_event(event, self.window):
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._handle_click(event.pos):
                return

        self.log.handle_event(event)
        self.paperdoll.handle_event(event)

    def _handle_key(self, event: pygame.event.Event) -> bool:
        if event.key == pygame.K_LEFTBRACKET:
            self.layout.toggle_left()
            self._remember_bars()
            return True
        if event.key == pygame.K_RIGHTBRACKET:
            self.layout.toggle_right()
            self._remember_bars()
            return True
        if event.key == pygame.K_F5:
            # Cycle the override, so the compact view is reachable on a
            # desktop without editing a file.
            order = list(LayoutMode)
            self.set_layout_mode(order[(order.index(self.settings.layout_mode) + 1) % len(order)])
            return True
        return False

    def _handle_click(self, pos: tuple[int, int]) -> bool:
        """Handles open a bar; a tap on the scrim closes one."""
        if self.layout.left_handle.collidepoint(pos) and not self.layout.left_open:
            self.layout.toggle_left()
            self._remember_bars()
            return True
        if self.layout.right_handle.collidepoint(pos) and not self.layout.right_open:
            self.layout.toggle_right()
            self._remember_bars()
            return True

        if self.layout.overlays and (self.layout.left_open or self.layout.right_open):
            covered = self.layout.left.collidepoint(pos) or self.layout.right.collidepoint(pos)
            if not covered:
                self.layout.left_open = self.layout.right_open = False
                return True
        return False

    def _remember_bars(self) -> None:
        if self.form is FormFactor.WIDE:
            self.settings.wide_left_open = self.layout.left_open
            self.settings.wide_right_open = self.layout.right_open

    def _movement(self) -> tuple[tuple[float, float], bool]:
        """Combine keyboard and stick. Returns the vector and whether to aim
        at the mouse -- a player using the stick has no cursor to aim with."""
        stick = self.stick.direction()
        if stick != (0.0, 0.0):
            return stick, False

        keys = pygame.key.get_pressed()
        keyboard = (
            float((keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])),
            float((keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP])),
        )
        return keyboard, not self.uses_touch_controls

    def update(self, dt: float) -> None:
        self.layout.window = self.window
        self.world.rect = self.layout.center
        direction, aim_at_mouse = self._movement()
        self.world.update(direction, dt, aim_at_mouse=aim_at_mouse)

    # -- the frame --------------------------------------------------------

    def step(self, surface: pygame.Surface, events, dt: float) -> bool:
        """One whole frame: events, update, draw. Returns whether to keep going.

        The loop that calls this is async under pygbag and plain on the
        desktop, so the frame itself must contain neither -- keeping it here
        means the two loops share every line that matters, and this one can
        be driven synchronously by a test.
        """
        for event in events:
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False
            self.handle_event(event)

        self.update(dt)
        self.draw(surface)
        return True

    # -- drawing ----------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(BACKGROUND)

        self.layout.window = self.window
        self.world.rect = self.layout.center
        self.world.draw(surface)

        self.paperdoll.open = self.layout.left_open
        self.log.open = self.layout.right_open

        if self.layout.overlays:
            self._draw_compact(surface)
        else:
            self.paperdoll.draw(surface, self.layout.left)
            self.log.draw(surface, self.layout.right)

        if self.uses_touch_controls:
            self.stick.draw(surface)

    def _draw_compact(self, surface: pygame.Surface) -> None:
        """Drawers over the world, with a scrim so text stays readable."""
        open_drawer = self.layout.left_open or self.layout.right_open
        if open_drawer:
            scrim = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            scrim.fill(SCRIM)
            surface.blit(scrim, (0, 0))

        if self.layout.left_open:
            self.paperdoll.draw(surface, self.layout.left)
        if self.layout.right_open:
            self.log.draw(surface, self.layout.right)

        if not self.layout.left_open:
            self._draw_handle(surface, self.layout.left_handle, "self")
        if not self.layout.right_open:
            self._draw_handle(surface, self.layout.right_handle, "log")

    def _draw_handle(self, surface: pygame.Surface, rect: pygame.Rect, kind: str) -> None:
        """A finger-sized button; the compact layout has no room for a strip."""
        button = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(button, HANDLE_BG, button.get_rect(), border_radius=8)
        surface.blit(button, rect)
        pygame.draw.rect(surface, HANDLE_EDGE, rect, width=1, border_radius=8)

        inner = rect.inflate(-18, -18)
        if kind == "self":
            pygame.draw.circle(surface, HANDLE_MARK, (inner.centerx, inner.y + 4), 4)
            pygame.draw.rect(
                surface, HANDLE_MARK, pygame.Rect(inner.centerx - 5, inner.y + 11, 10, 11),
                border_radius=3,
            )
        else:
            for index in range(3):
                y = inner.y + 4 + index * 7
                pygame.draw.line(surface, HANDLE_MARK, (inner.x, y), (inner.right, y), 2)
