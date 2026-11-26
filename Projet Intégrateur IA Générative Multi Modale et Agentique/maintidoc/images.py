"""Étape 3 : traitement des images.

- CLIP (via sentence-transformers) transforme chaque image en vecteur de 512 dimensions.
  Une question texte est projetée dans le même espace avec l'encodeur texte multilingue,
  ce qui permet de retrouver une image à partir d'une question en français.
- Un modèle vision (gpt-4.1-mini sur Azure, ou Qwen2.5-VL via Ollama) génère une
  description textuelle de chaque image ; cette description est ensuite indexée comme du texte.
"""

import base64
from functools import lru_cache
from pathlib import Path

from langchain_core.messages import HumanMessage
from PIL import Image
from sentence_transformers import SentenceTransformer

from . import config
from .llm import chat_model

PROMPT_DESCRIPTION = (
    "Tu es un assistant technique. Décris précisément cette image extraite d'un document "
    "technique : type de figure (schéma, photo, graphique, tableau), éléments visibles, "
    "textes et légendes lisibles, et ce qu'elle illustre. Réponds en français, en 5 phrases maximum."
)


@lru_cache(maxsize=None)
def _modele(nom: str) -> SentenceTransformer:
    return SentenceTransformer(nom)


def embeddings_images(chemins: list[Path]) -> list[list[float]]:
    """Vecteurs CLIP normalisés des images."""
    if not chemins:
        return []
    images = [Image.open(c).convert("RGB") for c in chemins]
    vecteurs = _modele(config.CLIP_IMAGE_MODEL).encode(images, normalize_embeddings=True)
    return vecteurs.tolist()


def embedding_requete_clip(texte: str) -> list[float]:
    """Vecteur CLIP d'une question texte (dans le même espace que les images)."""
    return _modele(config.CLIP_TEXT_MODEL).encode([texte], normalize_embeddings=True)[0].tolist()


@lru_cache(maxsize=1)
def _modele_vision():
    return chat_model(vision=True)


def decrire_image(chemin: Path) -> str:
    """Description textuelle d'une image par le modèle vision."""
    chemin = Path(chemin)
    mime = "image/png" if chemin.suffix.lower() == ".png" else "image/jpeg"
    donnees = base64.b64encode(chemin.read_bytes()).decode()
    message = HumanMessage(content=[
        {"type": "text", "text": PROMPT_DESCRIPTION},
        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{donnees}"}},
    ])
    return _modele_vision().invoke([message]).content.strip()
