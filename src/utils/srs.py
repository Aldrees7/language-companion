# src/utils/srs.py
"""
Language Companion – SRS (Spaced Repetition System)
---------------------------------------------------
Implements lightweight Leitner-style scheduling for vocabulary review.
Cards are persisted in JSON format through utils.storage.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict
from utils.constants import SRS_INTERVALS_DAYS, DEFAULT_EASE


def _today() -> datetime:
    """
    Returns the current UTC date truncated to midnight.
    This avoids time-of-day differences in due-date comparisons.
    """
    now = datetime.utcnow()
    return datetime(year=now.year, month=now.month, day=now.day)


def is_due(card: Dict) -> bool:
    """
    Returns True if the card is due for review (today or earlier).
    Cards with missing or invalid due dates are considered due.
    """
    due = card.get("due")
    if not due:
        return True
    try:
        return _today() >= datetime.fromisoformat(due)
    except Exception:
        return True


def schedule_next(card: Dict, quality: str) -> Dict:
    """
    Adjusts a card's review schedule based on user feedback.

    Parameters
    ----------
    card : dict
        The card dictionary containing keys: 'ease', 'step', 'due'.
    quality : str
        One of: "again", "hard", "good", "easy".

    Returns
    -------
    dict
        Updated card with recalculated ease, step, and next due date.
    """
    ease = float(card.get("ease", DEFAULT_EASE))
    step = int(card.get("step", 0))

    if quality == "again":
        step = 0
        ease = max(1.3, ease - 0.2)
    elif quality == "hard":
        ease = max(1.3, ease - 0.05)
        # step unchanged
    elif quality == "good":
        step = min(step + 1, len(SRS_INTERVALS_DAYS) - 1)
    elif quality == "easy":
        ease = min(3.0, ease + 0.05)
        step = min(step + 2, len(SRS_INTERVALS_DAYS) - 1)
    else:
        # fallback to neutral progression
        step = min(step + 1, len(SRS_INTERVALS_DAYS) - 1)

    next_due = _today() + timedelta(days=SRS_INTERVALS_DAYS[step])

    card["step"] = step
    card["ease"] = ease
    card["due"] = next_due.isoformat()

    return card
