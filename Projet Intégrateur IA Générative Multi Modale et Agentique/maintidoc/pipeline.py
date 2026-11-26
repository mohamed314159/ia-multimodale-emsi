"""Enchaîne les étapes 2 et 3 : extraction, descriptions, embeddings et indexation."""

from pathlib import Path
from typing import Callable

from . import config
from .extraction import extraire_contenu, noeuds_descriptions
from .images import decrire_image
from .indexation import indexer_images, indexer_textes, vider_tables
from .rag import MoteurRAG


def ingerer_pdf(pdf: Path, decrire: bool = True,
                progression: Callable[[str], None] = print) -> MoteurRAG:
    """Indexe un PDF dans PGVector et renvoie un moteur RAG prêt à l'emploi."""
    progression("Suppression de l'ancien index...")
    vider_tables()

    progression("Extraction du texte, des tableaux et des images...")
    contenu = extraire_contenu(pdf, config.DOSSIER_IMAGES)
    progression(contenu.resume())

    if decrire:
        for i, img in enumerate(contenu.images, start=1):
            progression(f"Description de l'image {i}/{len(contenu.images)} (page {img.page})...")
            img.description = decrire_image(img.chemin)

    progression("Embeddings et indexation du texte dans PGVector...")
    index = indexer_textes(contenu.textes + contenu.tableaux + noeuds_descriptions(contenu.images))

    progression("Embeddings CLIP et indexation des images dans PGVector...")
    store_images = indexer_images(contenu.images)

    progression("Indexation terminée.")
    return MoteurRAG(index=index, store_images=store_images)
