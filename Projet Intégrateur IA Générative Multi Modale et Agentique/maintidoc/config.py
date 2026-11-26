"""Configuration centrale du projet, lue depuis le fichier .env."""

import os
from pathlib import Path

from dotenv import load_dotenv

RACINE = Path(__file__).resolve().parent.parent
load_dotenv(RACINE / ".env")

# --- PostgreSQL + PGVector ---
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = int(os.getenv("PG_PORT", "5433"))
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "postgres")
PG_DATABASE = os.getenv("PG_DATABASE", "maintidoc")

# Tables créées par LlamaIndex (il ajoute le préfixe "data_")
TABLE_TEXTE = "maintidoc_texte"
TABLE_IMAGES = "maintidoc_images"

# --- Modèle de chat : "azure" (par défaut) ou "ollama" ---
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "azure").lower()

# --- Azure OpenAI ---
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-mini")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

# --- Ollama (option open source) ---
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5:7b")
VISION_MODEL = os.getenv("VISION_MODEL", "qwen2.5vl:3b")

# --- Embeddings ---
# Texte : modèle multilingue (questions en français, document en anglais)
TEXT_EMBED_MODEL = os.getenv("TEXT_EMBED_MODEL", "intfloat/multilingual-e5-small")
TEXT_EMBED_DIM = int(os.getenv("TEXT_EMBED_DIM", "384"))
# Images : CLIP. L'encodeur texte multilingue partage le même espace que l'encodeur image.
CLIP_IMAGE_MODEL = "clip-ViT-B-32"
CLIP_TEXT_MODEL = "sentence-transformers/clip-ViT-B-32-multilingual-v1"
CLIP_DIM = 512

# --- Dossiers ---
DOSSIER_DATA = RACINE / "data"
DOSSIER_IMAGES = DOSSIER_DATA / "images"
DOSSIER_UPLOADS = DOSSIER_DATA / "uploads"


def pdf_par_defaut() -> Path:
    """Renvoie le PDF recommandé par le prof : « Attention is all you need »."""
    candidats = sorted((RACINE / "Supports de cours").rglob("attention*.pdf"))
    if not candidats:
        raise FileNotFoundError("PDF « Attention is all you need » introuvable dans Supports de cours")
    return candidats[0]
