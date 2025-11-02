# src/utils/storage.py
"""
Language Companion – Local Storage Utilities
--------------------------------------------
Handles persistence for lessons and vocabulary cards using a local JSON file.
This provides a lightweight alternative to database storage.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List
from utils.constants import SRS_DB_PATH


def _ensure_file() -> Path:
    """
    Ensures that the SRS database file exists and is initialized.
    Creates parent directories if needed.
    """
    path = Path(SRS_DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)

    if not path.exists():
        path.write_text(
            json.dumps({"lessons": [], "cards": []}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    return path


def load_db() -> Dict[str, Any]:
    """
    Loads the SRS database from disk.
    Returns an empty schema if the file is missing or corrupted.
    """
    path = _ensure_file()
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"lessons": [], "cards": []}


def save_db(db: Dict[str, Any]) -> None:
    """
    Saves the provided database dictionary back to disk.
    """
    path = _ensure_file()
    path.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8")


def upsert_cards(new_cards: List[Dict[str, Any]]) -> int:
    """
    Inserts or updates vocabulary cards in the SRS database.

    Upsert is based on (term.lower(), lang).
    Returns the number of processed cards.
    """
    db = load_db()
    existing = {
        (c["term"].lower(), c.get("lang", "auto")): i
        for i, c in enumerate(db["cards"])
    }

    count = 0
    for new_card in new_cards:
        key = (new_card["term"].lower(), new_card.get("lang", "auto"))
        if key in existing:
            idx = existing[key]
            db["cards"][idx].update(
                {k: v for k, v in new_card.items() if v is not None}
            )
        else:
            db["cards"].append(new_card)
        count += 1

    save_db(db)
    return count
