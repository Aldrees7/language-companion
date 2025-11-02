# src/app/app.py
"""
Language Companion – Streamlit UI
---------------------------------
Analyze text (explain, translate, grammar, quiz, vocab), generate review notes,
and save vocabulary to a local SRS deck with review sessions.
"""

import os
import sys
import io
from pathlib import Path

# Ensure src/ is importable (for agent_core, utils, etc.)
SRC_ROOT = Path(__file__).resolve().parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

import streamlit as st
from dotenv import load_dotenv
import fitz  # PyMuPDF
from docx import Document

from agent_core.agent import run_agent, extract_vocab_json
from utils.storage import upsert_cards, load_db, save_db
from utils.srs import is_due, schedule_next
from utils.constants import (
    REVIEW_BATCH_SIZE,
    APP_TITLE,
    SIDEBAR_CAPTION,
)

# Load environment variables from .env if present
load_dotenv()


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def resolve_api_key(sidebar_key: str | None) -> str | None:
    """
    Prefer the sidebar key; fallback to environment variable.
    """
    return sidebar_key or os.getenv("OPENAI_API_KEY")


def read_file_to_text(file) -> str:
    """
    Read uploaded lesson files (.txt, .md, .pdf, .docx).
    Falls back gracefully if the format cannot be parsed.
    """
    try:
        filename = file.name.lower()
        data = file.getvalue()

        if filename.endswith(".pdf"):
            text = ""
            with fitz.open(stream=io.BytesIO(data), filetype="pdf") as pdf:
                for page in pdf:
                    text += page.get_text("text")
            return text.strip()

        if filename.endswith(".docx"):
            doc = Document(io.BytesIO(data))
            return "\n".join(p.text for p in doc.paragraphs).strip()

        if filename.endswith((".txt", ".md")):
            return data.decode("utf-8", errors="ignore")

        return "[Unsupported file type]"
    except Exception as e:
        return f"[Error reading file: {e}]"


def get_input_text(uploaded_file, typed_text) -> str:
    """
    Prefer typed text; if empty and a file exists, read the file.
    """
    txt = (typed_text or "").strip()
    if uploaded_file and not txt:
        txt = read_file_to_text(uploaded_file)
    return txt


# -----------------------------------------------------------------------------
# Page & Sidebar
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Language Companion", page_icon="🧑‍🏫", layout="wide")
st.title(APP_TITLE)
st.markdown(
    "Paste a lesson or text, then choose a mode: "
    "**Explain**, **Translate**, **Grammar**, **Quiz**, or **Vocab**. "
    "You can also generate a compact **Review Note**."
)

st.sidebar.caption(SIDEBAR_CAPTION)
st.sidebar.header("🔑 Settings")
api_key = st.sidebar.text_input("OpenAI API key", type="password")

mode = st.sidebar.radio(
    "Mode",
    ["explain", "translate", "grammar", "quiz", "vocab"],
    index=0,
)

review_format_label = st.sidebar.radio(
    "Review Note Format",
    ["Study Sheet", "Flashcards", "Compact"],
    index=0,
)
format_key = {"Study Sheet": "study", "Flashcards": "flashcards", "Compact": "compact"}[
    review_format_label
]

# -----------------------------------------------------------------------------
# Inputs
# -----------------------------------------------------------------------------
uploaded = st.file_uploader(
    "Upload lesson file (.txt, .md, .pdf, .docx)",
    type=["txt", "md", "pdf", "docx"],
)
text_input = st.text_area("Or paste text here:", height=220)

# Buttons row
col_a, col_b = st.columns([1, 1])

with col_a:
    if st.button("➕ Save vocab to Review", key="save_vocab"):
        resolved_key = resolve_api_key(api_key)
        if not resolved_key:
            st.warning("Enter your key in the sidebar or set OPENAI_API_KEY in .env")
            st.stop()
        text = get_input_text(uploaded, text_input)
        if not text:
            st.warning("Please upload or paste some text first.")
            st.stop()
        with st.spinner("Extracting vocab..."):
            items = extract_vocab_json(api_key=resolved_key, text=text)
        if not items:
            st.info("No vocab extracted.")
        else:
            n = upsert_cards(items)
            st.success(f"Saved {n} vocab item(s) to your review deck.")

with col_b:
    if st.button("▶️ Start Review", key="start_review"):
        st.session_state["_start_review"] = True

# Single container so results replace instead of stacking
result_area = st.container()

# -----------------------------------------------------------------------------
# Analyze
# -----------------------------------------------------------------------------
if st.button("Analyze"):
    resolved_key = resolve_api_key(api_key)
    if not resolved_key:
        st.warning("Enter your key in the sidebar or set OPENAI_API_KEY in .env")
        st.stop()

    text = get_input_text(uploaded, text_input)
    if not text:
        st.warning("Please upload or paste some text first.")
        st.stop()

    with st.spinner("Thinking..."):
        output = run_agent(api_key=resolved_key, text=text, mode=mode)

    result_area.empty()
    with result_area:
        st.subheader("Result")
        st.markdown(output)

# -----------------------------------------------------------------------------
# Review Note
# -----------------------------------------------------------------------------
if mode in {"vocab", "explain", "grammar"}:
    if st.button("📝 Make Review Note", key="make_review"):
        resolved_key = resolve_api_key(api_key)
        if not resolved_key:
            st.warning("Enter your key in the sidebar or set OPENAI_API_KEY in .env")
            st.stop()

        text = get_input_text(uploaded, text_input)
        if not text:
            st.warning("Please upload or paste some text first.")
            st.stop()

        with st.spinner("Composing review note..."):
            note_md = run_agent(
                api_key=resolved_key,
                text=text,
                mode="review",
                review_format=format_key,  # "study" | "flashcards" | "compact"
            )

        st.markdown("---")
        st.subheader("Review Note")
        st.markdown(note_md)
        st.download_button(
            label="⬇️ Download note (.md)",
            data=note_md,
            file_name="review_note.md",
            mime="text/markdown",
        )

# -----------------------------------------------------------------------------
# Review Session
# -----------------------------------------------------------------------------
if st.session_state.get("_start_review"):
    st.markdown("---")
    st.header("🧠 Review Session")

    db = load_db()
    due_cards = [c for c in db["cards"] if is_due(c)][:REVIEW_BATCH_SIZE]

    if not due_cards:
        st.success("No cards are due today. 🎉")
        if st.button("Close"):
            st.session_state["_start_review"] = False
        st.stop()

    idx_key = "_review_idx"
    if idx_key not in st.session_state:
        st.session_state[idx_key] = 0

    i = st.session_state[idx_key]
    if i >= len(due_cards):
        st.success("Session complete! ✅")
        st.session_state["_start_review"] = False
        st.session_state[idx_key] = 0
        save_db(db)
        st.stop()

    card = due_cards[i]
    st.subheader(f"Card {i+1} of {len(due_cards)}")

    with st.expander("💬 Reveal Answer", expanded=False):
        st.markdown(f"**Term**: {card['term']}")
        if card.get("pos"):
            st.write(f"**Part of speech**: {card['pos']}")
        st.write(f"**Translation**: {card.get('translation', '')}")
        if card.get("example_source"):
            st.write(f"**Example (source)**: {card['example_source']}")
        if card.get("example_en"):
            st.write(f"**Example (English)**: {card['example_en']}")

    c1, c2, c3, c4 = st.columns(4)

    def _grade(q: str):
        db2 = load_db()
        for j, dc in enumerate(db2["cards"]):
            if (
                dc["term"].lower() == card["term"].lower()
                and dc.get("lang", "auto") == card.get("lang", "auto")
            ):
                db2["cards"][j] = schedule_next(dc, q)
                break
        save_db(db2)
        st.session_state[idx_key] += 1

    with c1:
        st.button("Again", on_click=lambda: _grade("again"))
    with c2:
        st.button("Hard", on_click=lambda: _grade("hard"))
    with c3:
        st.button("Good", on_click=lambda: _grade("good"))
    with c4:
        st.button("Easy", on_click=lambda: _grade("easy"))

    st.caption("Grades advance the next due date. Close the session any time.")
