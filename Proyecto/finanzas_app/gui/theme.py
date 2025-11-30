from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Theme:
    SIDEBAR_BG: str = "#D7263D"
    ACTION_COLOR: str = "#E94F56"
    CARD_BG: str = "#F7E9D7"
    BACKGROUND: str = "#FAFAFA"
    PRIMARY_TEXT: str = "#2C2C2C"
    SECONDARY_TEXT: str = "#6E6E6E"
    BORDER: str = "#E0E0E0"
    ACTION_HOVER: str = "#F7E9D7"
    SUCCESS: str = "#4CAF50"
    WARNING: str = "#FFA545"
    LOGO_PATH: Path = Path(__file__).resolve().parents[2] / "assets" / "chancho.png"
