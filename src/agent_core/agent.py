# src/agent_core/agent.py
"""
Language Companion – Agent Core
--------------------------------
Handles LLM orchestration for all application modes:
    - explain
    - translate
    - grammar
    - quiz
    - vocab
    - review (study, flashcards, compact)

Provides language detection and structured vocabulary extraction.
"""

from __future__ import annotations

import json
import re
from typing import List, Dict, Any, Optional

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from utils.constants import (
    OPENAI_MODEL,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_P,
    QUIZ_COUNT,
    VOCAB_COUNT,
    TARGET_LANG,
)


# ---------------------------------------------------------------------------
# Language Detection
# ---------------------------------------------------------------------------

def detect_language(api_key: str, text: str) -> str:
    """
    Detects the language of a given text and returns its English name.
    Example outputs: "German", "Spanish", "French", etc.
    """
    llm = ChatOpenAI(
        model=OPENAI_MODEL,
        temperature=0.0,
        top_p=1.0,
        api_key=api_key,
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You output ONLY the language name in English "
         "(e.g., 'German', 'Spanish', 'French', 'Italian', "
         "'Russian', 'Arabic', 'Turkish'). No punctuation, no extra text."),
        ("user", "{text}")
    ])
    result = (prompt | llm).invoke({"text": text})
    return getattr(result, "content", "").strip()


# ---------------------------------------------------------------------------
# Agent Core Logic
# ---------------------------------------------------------------------------

def run_agent(
    api_key: str,
    text: str,
    mode: str = "explain",
    review_format: Optional[str] = None,
) -> str:
    """
    Executes the chosen agent mode using the configured LLM.
    Modes:
        - translate
        - grammar
        - quiz
        - vocab
        - review
        - explain (default)
    Returns a plain text response string.
    """
    llm = ChatOpenAI(
        model=OPENAI_MODEL,
        temperature=DEFAULT_TEMPERATURE,
        top_p=DEFAULT_TOP_P,
        api_key=api_key,
    )

    if mode == "translate":
        system_prompt = "Translate the following text naturally and fluently into English."

    elif mode == "grammar":
        system_prompt = (
            "Identify and explain grammar issues in the text clearly. "
            "Keep it concise and give 1–2 example sentences when useful."
        )

    elif mode == "quiz":
        system_prompt = (
            f"Create a language quiz with {QUIZ_COUNT} questions based on the text. "
            "Mix formats (multiple choice, fill-in-the-blank, meaning). "
            "Number the questions and provide answers at the end."
        )

    elif mode == "vocab":
        system_prompt = (
            f"Extract up to {VOCAB_COUNT} useful vocabulary items "
            f"(words or short phrases) with brief translations to {TARGET_LANG} "
            "and a short example from the text."
        )

    elif mode == "review":
        fmt = (review_format or "study").lower()
        if fmt == "compact":
            system_prompt = (
                "You are a language learning assistant. Create a REVIEW NOTE that helps "
                "the student study this text later.\n"
                "Format: Compact mobile review.\n"
                "Rules:\n"
                "- Start with a clear title based on the topic of the text.\n"
                "- Max 25 lines total. Start with a 1-line TL;DR.\n"
                "- Then 8–12 key vocab lines, each like: "
                "'• term — short translation — 3–5 word example'.\n"
                "- Then 3 micro-drills (fill-in/cloze) on separate lines. No extra text."
            )
        elif fmt == "flashcards":
            system_prompt = (
                "You are a language learning assistant. Create a REVIEW NOTE as MARKDOWN flashcards.\n"
                "Rules:\n"
                "- Start with a clear title based on the topic of the text.\n"
                "- Then produce 12 flashcards, each as two lines:\n"
                "Q: <term or cloze>\n"
                "A: <short answer>\n"
                "- Prioritize useful vocabulary and short phrases; answers under 10 words.\n"
                "- No extra commentary."
            )
        else:
            system_prompt = (
                "You are a language learning assistant. Create a REVIEW NOTE as a compact "
                "MARKDOWN study sheet.\n"
                "Rules:\n"
                "- Start with a clear title based on the topic of the text. Example:\n"
                "  # Study Sheet: <main topic>\n"
                "- Sections exactly:\n"
                "  1) **TL;DR** – 2–3 lines summarizing meaning for a learner.\n"
                "  2) **Grammar** – 2–4 bullets, <15 words each, with tiny examples.\n"
                "  3) **Vocab (10–12)** – lines like ‘term — translation — 4–6 word example’.\n"
                "  4) **Mini drill (3)** – short fill-in or transform prompts.\n"
                "- Keep it concise and copy-friendly. No extra commentary."
            )

    else:
        system_prompt = (
            "Explain the meaning of this text in simple, clear language "
            "for a learner at A2/B1 level."
        )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "{text}")
    ])
    result = (prompt | llm).invoke({"text": text})
    return getattr(result, "content", str(result))


# ---------------------------------------------------------------------------
# Vocabulary Extraction
# ---------------------------------------------------------------------------

def extract_vocab_json(api_key: str, text: str) -> List[Dict[str, Any]]:
    """
    Extracts vocabulary items as structured JSON and attaches detected language.
    Returns a list of dictionaries with the following keys:
        term, pos, translation, example_source, example_en, lang
    """
    lang = detect_language(api_key, text)

    llm = ChatOpenAI(
        model=OPENAI_MODEL,
        temperature=max(0.0, min(0.5, DEFAULT_TEMPERATURE - 0.3)),
        top_p=1.0,
        api_key=api_key,
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "Extract useful vocabulary from the user's text for a language learner. "
         "Return STRICT JSON array, where each item has keys exactly: "
         "term, pos, translation, example_source, example_en. Keep values short. "
         "Do not include any extra commentary or code fencing."),
        ("user", "{text}")
    ])
    raw = (prompt | llm).invoke({"text": text})
    raw_text = getattr(raw, "content", "") if raw is not None else ""

    def _try_json_load(s: str) -> Optional[List[Dict[str, Any]]]:
        try:
            parsed = json.loads(s)
            return parsed if isinstance(parsed, list) else None
        except Exception:
            return None

    parsed = _try_json_load(raw_text)
    if not parsed:
        fenced = re.search(r"```json\s*([\s\S]*?)```", raw_text, flags=re.IGNORECASE)
        if fenced:
            parsed = _try_json_load(fenced.group(1).strip())
    if not parsed:
        array_match = re.search(r"\[\s*\{.*?\}\s*\]", raw_text, flags=re.S)
        if array_match:
            parsed = _try_json_load(array_match.group(0).strip())

    data = parsed if parsed else []
    for d in data:
        d["lang"] = lang

    return data
