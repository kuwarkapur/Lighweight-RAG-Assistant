import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DOCUMENTS_DIR = DATA_DIR / "documents"
STRUCTURED_DIR = DATA_DIR / "structured"
CHROMA_DIR = PROJECT_ROOT / ".chroma_db"
CSV_PATH = STRUCTURED_DIR / "inventory_aging.csv"

HF_TOKEN = os.getenv("HF_TOKEN", "")
HF_EMBEDDING_MODEL = os.getenv(
    "HF_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)
HF_LLM_MODEL = os.getenv("HF_LLM_MODEL", "meta-llama/Llama-3.1-8B-Instruct")
HF_LLM_FALLBACK = os.getenv("HF_LLM_FALLBACK", "HuggingFaceH4/zephyr-7b-beta")

TOP_K = 5
TOP_K_WORKFLOW = 8
LLM_CONTEXT_MAX = 3
CHUNK_SIZE = 500  # max words per sub-chunk when a section exceeds SECTION_CHUNK_SIZE
CHUNK_OVERLAP = 50
SECTION_CHUNK_SIZE = 150  # sections at or below this word count stay as one chunk

# Retrieval post-processing
CONTEXT_SCORE_FLOOR = 0.40

# Retrieval confidence thresholds
THRESHOLD_HIGH = 0.65
THRESHOLD_MEDIUM = 0.45
THRESHOLD_LOW = 0.45  # scores below this abstain

# Abstain when top hit is weak and retrieval is ambiguous
ABSTAIN_WEAK_TOP_SCORE = 0.55
ABSTAIN_MIN_SCORE_GAP = 0.05
