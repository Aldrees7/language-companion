# src/utils/constants.py
"""
Language Companion – Shared Constants
-------------------------------------
Centralizes configuration for models, prompts, uploads, SRS/memory, and UI.
Update these values instead of scattering literals across the codebase.
"""

from pathlib import Path

# === OpenAI / Model Config ===
OPENAI_MODEL: str = "gpt-4o-mini"
DEFAULT_TEMPERATURE: float = 0.5         # used by run_agent()
DEFAULT_TOP_P: float = 1.0               # used by run_agent()

# === Upload Config ===
MAX_UPLOAD_MB: int = 5
ALLOWED_FILE_TYPES = {".txt", ".md", ".pdf"}

# === Agent: Quiz + Vocabulary ===
QUIZ_COUNT: int = 10                     # # of quiz questions in quiz mode
VOCAB_COUNT: int = 12                    # max extracted vocab items
TARGET_LANG: str = "English"             # target for vocab translations

# === Review-note Settings (agent 'review' mode) ===
REVIEW_NOTE_FORMATS = ["Study Sheet", "Flashcards", "Compact"]
REVIEW_VOCAB_MIN: int = 10               # guidance only (kept in prompts)
REVIEW_VOCAB_MAX: int = 12               # guidance only (kept in prompts)
DRILL_COUNT: int = 3                     # guidance only (kept in prompts)

# === SRS / Memory ===
SRS_DB_PATH: Path = Path("src/data/srs_db.json")
REVIEW_BATCH_SIZE: int = 15
SRS_INTERVALS_DAYS = [1, 3, 7, 14, 30]   # simple Leitner-style schedule
DEFAULT_EASE: float = 2.5

# === History / Review Notes (optional visibility layer) ===
REVIEW_NOTES_PATH: Path = Path("src/data/review_notes")
HISTORY_PATH: Path = Path("src/data/history.json")
HISTORY_MAX: int = 200
PREVIEW_ROWS: int = 6

# === UI / Misc ===
APP_TITLE: str = "🧑‍🏫 Language Companion"
SIDEBAR_CAPTION: str = (
    "🔐 Your study data is stored locally at src/data/srs_db.json"
)
