"""Shared test setup.

One display for the whole session. Each module used to create and quit its
own, which worked module by module and broke when they ran together: the
first module to finish tore down the display the rest were still using.
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
# No audio device in CI, and nothing here needs sound.
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest


@pytest.fixture(scope="session", autouse=True)
def display():
    pygame.init()
    pygame.display.set_mode((1280, 760))
    yield
    pygame.quit()


@pytest.fixture(autouse=True)
def unscaled_display():
    """Every test starts at scale 1, whatever the last one did.

    The scale is module-level state, and a test that leaves it at 3x makes
    unrelated tests measure a screen three times the size they expect.
    """
    from lechery.ui import fonts, metrics

    yield
    if metrics.SCALE != 1.0:
        metrics.set_scale(1.0)
        fonts.clear_cache()
