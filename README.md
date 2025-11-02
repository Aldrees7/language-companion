# 🧑‍🏫 Language Companion
**An AI-powered study partner for language learners.**
Paste any lesson or upload files to explain, translate, analyze grammar, generate quizzes, extract vocabulary, and build review notes with spaced-repetition tracking.

---

## 🚀 Quick Start

### 1️⃣ Install dependencies
```bash
uv venv
uv sync
```

### 2️⃣ Set your API key
```bash
# PowerShell
$env:OPENAI_API_KEY="sk-..."
# or Linux/Mac
export OPENAI_API_KEY="sk-..."
```

### 3️⃣ Launch the app
```bash
uv run streamlit run src/app/app.py
```

---

## ✨ Features

### 🧩 Core Modes
| Mode | Description |
|-------|--------------|
| **Explain** | Simplifies and paraphrases text for A2/B1 learners. |
| **Translate** | Produces a natural, fluent English translation. |
| **Grammar** | Highlights key grammar points and examples. |
| **Quiz** | Generates 10 mixed question types (MCQ, cloze, meaning). |
| **Vocab** | Extracts 10–12 key words/phrases with examples. |

---

### 🧾 Review Note Formats
| Format | Output Style | Use Case |
|---------|---------------|----------|
| **Study Sheet** | Structured sections (TL;DR, Grammar, Vocab, Drills). | Print-style learning notes. |
| **Flashcards** | `Q:` / `A:` pairs. | Self-testing or Anki import. |
| **Compact** | 1-line bullets for quick review. | Mobile or smartwatch notes. |

---

### 💾 Spaced Repetition System (SRS)
- Vocabulary cards saved locally in `src/data/srs_db.json`.
- Grading buttons adjust review schedule:
  - **Again:** soon (reset)
  - **Hard:** shorter delay
  - **Good:** normal delay
  - **Easy:** longer delay
- Persistent storage — all progress is saved between sessions.

---

### 📂 File Support
Supports `.txt`, `.md`, `.pdf`, and `.docx` uploads.
Automatically extracts text using **PyMuPDF** (for PDFs) and **python-docx** (for Word files).

---

## 🧠 Architecture Overview

```
src/
 ├─ app/
 │   └─ app.py              # Streamlit UI
 ├─ agent_core/
 │   ├─ agent.py            # LangChain logic and prompts
 │   └─ prompts/system.json # Base system prompt
 ├─ utils/
 │   ├─ constants.py        # Configuration values
 │   ├─ storage.py          # Local JSON persistence
 │   └─ srs.py              # Spaced repetition scheduler
 └─ data/
     └─ srs_db.json         # Local SRS deck
```

---

## 🧩 Tech Stack
| Component | Library |
|------------|----------|
| **Frontend** | Streamlit |
| **LLM / Agents** | LangChain + OpenAI (GPT-4o-mini) |
| **Data Handling** | JSON (local storage) |
| **PDF & Word Parsing** | PyMuPDF, python-docx |
| **Code Quality** | Ruff + Black |
| **Dependency Management** | uv |

---

## 🔧 Constants & Config
All static configuration lives in `src/utils/constants.py` — including:
- model (`OPENAI_MODEL`)
- SRS intervals
- review batch size
- upload limits
- paths for data and review notes

---

## 🧪 Example Usage
Upload a file or paste text such as:

```
Anna steht früh auf und geht in das kleine Café an der Ecke.
Sie bestellt einen Kaffee mit Milch und ein Brötchen mit Marmelade.
```

Then choose:
- Mode → **Explain**
- Review Note Format → **Study Sheet**
- Click **Analyze** or **📝 Make Review Note**

---

## 📘 Project Status
✅ Functional & stable prototype.
💡 Optional future upgrades:
- Deck statistics in sidebar.
- Lesson history viewer.
- Cloud sync for user data.

---

## ⚖️ License
MIT License © 2025 Language Companion Developers
