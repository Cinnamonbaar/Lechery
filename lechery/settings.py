"""Player settings, persisted to disk.

Model-side and pygame-free. Settings are read at startup and written when
changed; a corrupt or missing file falls back to defaults rather than
refusing to launch, because losing your preferences should never cost you
the game.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from .platform import data_dir


class LayoutMode(Enum):
    """How the screen should be divided.

    AUTO measures the window; the other two are the player's override, for
    when the measurement disagrees with what they want -- a tablet user who
    prefers the full three-pane view, or a desktop user who wants the
    world to fill the window.
    """

    AUTO = "auto"
    WIDE = "wide"
    COMPACT = "compact"


def default_path() -> Path:
    """Resolved per call, not at import: the answer differs in the browser."""
    return data_dir() / "settings.json"


@dataclass
class Settings:
    layout_mode: LayoutMode = LayoutMode.AUTO

    #: Bars the player last had open, remembered per layout so switching
    #: between them does not lose the arrangement.
    wide_left_open: bool = True
    wide_right_open: bool = True

    #: Draw the on-screen movement stick even on a mouse-and-keyboard
    #: machine. None means "decide from the layout".
    touch_controls: Optional[bool] = None

    path: Optional[Path] = field(default=None, repr=False, compare=False)

    # -- persistence ------------------------------------------------------

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "Settings":
        path = path or default_path()
        try:
            data = json.loads(path.read_text())
        except (OSError, ValueError):
            return cls(path=path)
        return cls.from_dict(data, path=path)

    @classmethod
    def from_dict(cls, data: dict[str, Any], path: Optional[Path] = None) -> "Settings":
        settings = cls(path=path)
        for key, value in data.items():
            if not hasattr(settings, key) or key == "path":
                continue  # an unknown key is a setting from another version
            if key == "layout_mode":
                try:
                    value = LayoutMode(value)
                except ValueError:
                    continue
            setattr(settings, key, value)
        return settings

    def to_dict(self) -> dict[str, Any]:
        data = {k: v for k, v in asdict(self).items() if k != "path"}
        data["layout_mode"] = self.layout_mode.value
        return data

    def save(self, path: Optional[Path] = None) -> bool:
        """Write settings. Returns whether it worked; never raises.

        A read-only home directory is a reason to lose preferences, not a
        reason to crash mid-game.
        """
        path = path or self.path or default_path()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(self.to_dict(), indent=2))
            return True
        except OSError:
            return False
