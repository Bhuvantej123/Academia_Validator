"""
config.py — Central Configuration
Authenticity Validator of Academia
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ─── Base Paths ───────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
REPORT_DIR = BASE_DIR / "reports"

UPLOAD_DIR.mkdir(exist_ok=True)
REPORT_DIR.mkdir(exist_ok=True)

# ─── Database ─────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{BASE_DIR / 'academia.db'}")

# ─── File Handling ────────────────────────────────────────────────
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_FILE_SIZE_MB = 20
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# ─── Preprocessing ────────────────────────────────────────────────
MIN_SENTENCE_LENGTH = 10   # characters
MAX_CHUNK_SIZE = 512       # tokens per chunk for transformer models

# ─── Scoring Weights ──────────────────────────────────────────────
SCORE_WEIGHTS = {
    "plagiarism": 0.40,       # 40% weight
    "ai_detection": 0.35,     # 35% weight
    "authorship": 0.25,       # 25% weight
}

# ─── Plagiarism ───────────────────────────────────────────────────
PLAGIARISM_SIMILARITY_THRESHOLD = 0.80   # cosine similarity threshold
PLAGIARISM_MODEL = "all-MiniLM-L6-v2"   # lightweight Sentence-BERT

# ─── AI Detection ─────────────────────────────────────────────────
AI_DETECTION_THRESHOLD = 0.65            # probability threshold
AI_DETECTION_MODEL = "roberta-base-openai-detector"  # HuggingFace model

# ─── Authorship ───────────────────────────────────────────────────
AUTHORSHIP_CONSISTENCY_THRESHOLD = 0.70  # minimum cosine similarity
AUTHORSHIP_WINDOW_SIZE = 5               # sentences per window

# ─── Report ───────────────────────────────────────────────────────
REPORT_VERSION = "1.0.0"
MAX_FLAGGED_SECTIONS = 20

# ─── API ──────────────────────────────────────────────────────────
API_TITLE = "Authenticity Validator of Academia"
API_VERSION = "1.0.0"
API_DESCRIPTION = (
    "Analyses academic documents for plagiarism, AI-generated content, "
    "and authorship consistency, then returns a combined authenticity score."
)
