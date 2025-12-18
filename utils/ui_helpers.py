# utils/ui_helpers.py
# Helper utilities for textual bars & minimap emojis
from __future__ import annotations
import random
from typing import Any, Dict, List


def _get_health_color_ratio(ratio: float) -> str:
    """Return the appropriate square emoji for the given health ratio."""
    if ratio < 0.25:
        return "🟥"
    if ratio < 0.5:
        return "🟨"
    return "🟩"


def create_progress_bar(current: int, maximum: int, length: int = 10, *, colorize: bool = False) -> str:
    """
    Build a simple █ / ░ progress bar  (e.g. HP, EXP).

    When ``colorize`` is True, the filled portion uses square emojis that shift
    from green → yellow → red as the percentage decreases.
    """
    if maximum <= 0:
        return "[No Data]"

    current = max(0, current)
    ratio = min(max(current / float(maximum), 0.0), 1.0)
    filled = int(round(length * ratio))

    if colorize:
        filled_char = _get_health_color_ratio(ratio)
        empty_char = "⬜"
    else:
        filled_char = "█"
        empty_char = "░"

    bar = filled_char * filled + empty_char * (length - filled)
    return f"[{bar}] {current}/{maximum}"


def create_cooldown_bar(current_cd: float, max_cd: float, length: int = 10) -> str:
    """
    Visualise an ability cooldown.  When current_cd ≤ 0 → “[Ready]”
    """
    current_cd = min(current_cd, max_cd)
    if max_cd <= 0 or current_cd <= 0:
        return "[Ready]"

    filled = int(round(length * (max_cd - current_cd) / max_cd))
    bar    = "█" * filled + "░" * (length - filled)
    return f"[{bar}]"


def get_emoji_for_room_type(room_type: str) -> str:
    """
    Return an emoji representing the supplied room type (case‑insensitive).
    Unknown types ⇒ black square.
    """
    mapping = {
        "safe":           "🟩",
        "monster":        "🟥",
        "boss":           "💀",
        "illusion":       "🔮",
        "npc":            "👤",
        "item":           "🟦",
        "chest_unlocked": "🟦",
        "shop":           "🟪",
        "exit":           "🚪",
        "locked":         "🔒",
        "staircase_up":   "🔼",
        "staircase_down": "🔽",
        "trap":           "🟧",
    }
    if not room_type:
        return "⬛"
    return mapping.get(room_type.lower(), "⬛")


def format_status_effects(effects: List[Dict[str, Any]]) -> str:
    """
    Render a list of status-effect dicts as:
      🩸 Poison (2) 🔥 Burn (1) ❤️ Regen (3)
    Each dict MUST have:
      - 'icon':       a one‑char emoji or short string
      - 'effect_name':string
      - 'remaining':   int (turns left)
    """
    parts: List[str] = []
    for e in effects:
        icon = e.get("icon") or e.get("icon_url", "")
        name = e.get("effect_name", "").strip()
        rem  = e.get("remaining")

        # skip anything malformed
        if not icon or not name or rem is None:
            continue

        parts.append(f"{icon} {name} ({rem})")

    # join with a single space so they flow left-to-right
    return " ".join(parts)
