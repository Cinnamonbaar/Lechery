"""Deriving per-area seeds from one master seed.

A single shared `Random` would couple every area to the order they were
generated in: add one room to the tutorial and the plains reshuffle. Deriving
an independent stream per area keeps each one stable no matter what else
changes, which matters as soon as areas start generating lazily on first
visit.
"""

from __future__ import annotations

import hashlib
import random


def derive_seed(master_seed: int, key: str) -> int:
    """A stable sub-seed for `key` under `master_seed`.

    Uses a hash rather than arithmetic so that adjacent keys ("area1",
    "area2") give unrelated streams instead of neighbouring ones.
    """
    digest = hashlib.sha256(f"{master_seed}:{key}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def rng_for(master_seed: int, key: str) -> random.Random:
    return random.Random(derive_seed(master_seed, key))
