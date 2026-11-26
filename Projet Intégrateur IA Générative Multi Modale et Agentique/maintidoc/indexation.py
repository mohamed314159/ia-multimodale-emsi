"""Étapes 2 et 3 : stockage des vecteurs et métadonnées dans PGVector (PostgreSQL).

Deux tables :
- data_maintidoc_texte  : morceaux de texte, tableaux et descriptions d'images
                          (embeddings multilingual-e5-small, 384 dimensions)
- data_maintidoc_images : images (embeddings CLIP, 512 dimensions)
"""

from functools import lru_cache

import sqlalchemy
from llama_index.core import Settings, StorageContext, VectorStoreIndex
from llama_index.core.schema import TextNode
from llama_index.core.vector_stores import VectorStoreQuery
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.postgres import PGVectorStore

from . import config
from .extraction import ImageExtraite
from .images import embedding_requete_clip, embeddings_images


def url_postgres() -> sqlalchemy.URL:
    return sqlalchemy.URL.create(
        "postgresql+psycopg2", username=config.PG_USER, password=config.PG_PASSWORD,
        host=config.PG_HOST, port=config.PG_PORT, database=config.PG_DATABASE,
    )


@lru_cache(maxsize=None)
def embedding_texte() -> HuggingFaceEmbedding:
    """Modèle d'embedding open source. e5 attend les préfixes « query: » et « passage: »."""
    modele = HuggingFaceEmbedding(
        model_name=config.TEXT_EMBED_MODEL,
        query_instruction="query: ",
        text_instruction="passage: ",
    )
    Settings.embed_model = modele  # évite que LlamaIndex cherche OpenAI par défaut
    return modele


def _store(table: str, dimension: int) -> PGVectorStore:
    return PGVectorStore.from_params(
        database=config.PG_DATABASE, host=config.PG_HOST, port=str(config.PG_PORT),
        user=config.PG_USER, password=config.PG_PASSWORD,
        table_name=table, embed_dim=dimension,
    )


def vider_tables() -> None:
    """Supprime les tables pour réindexer un nouveau document à partir de zéro."""
    moteur = sqlalchemy.create_engine(url_postgres())
    with moteur.begin() as connexion:
        for table in (config.TABLE_TEXTE, config.TABLE_IMAGES):
            connexion.execute(sqlalchemy.text(f'DROP TABLE IF EXISTS "data_{table}"'))
    moteur.dispose()


# ---------- Texte, tableaux, descriptions ----------

def indexer_textes(noeuds: list[TextNode]) -> VectorStoreIndex:
    """Calcule les embeddings des nœuds et les enregistre dans PGVector."""
    contexte = StorageContext.from_defaults(vector_store=_store(config.TABLE_TEXTE, config.TEXT_EMBED_DIM))
    return VectorStoreIndex(noeuds, storage_context=contexte, embed_model=embedding_texte(), show_progress=True)


def charger_index_textes() -> VectorStoreIndex:
    """Recharge l'index déjà présent dans PostgreSQL (sans recalculer les embeddings)."""
    store = _store(config.TABLE_TEXTE, config.TEXT_EMBED_DIM)
    return VectorStoreIndex.from_vector_store(store, embed_model=embedding_texte())


# ---------- Images (CLIP) ----------

def indexer_images(images: list[ImageExtraite]) -> PGVectorStore:
    """Enregistre les vecteurs CLIP des images avec leur page, chemin et description."""
    store = _store(config.TABLE_IMAGES, config.CLIP_DIM)
    vecteurs = embeddings_images([img.chemin for img in images])
    noeuds = [
        TextNode(
            text=img.description or f"Figure de la page {img.page}",
            embedding=vecteur,
            metadata={"type": "image", "fichier": img.fichier, "page": img.page, "chemin": str(img.chemin)},
        )
        for img, vecteur in zip(images, vecteurs)
    ]
    if noeuds:
        store.add(noeuds)
    return store


def charger_store_images() -> PGVectorStore:
    return _store(config.TABLE_IMAGES, config.CLIP_DIM)


def rechercher_images_clip(store: PGVectorStore, question: str, k: int = 3) -> list[tuple[TextNode, float]]:
    """Recherche texte -> image : renvoie les k images les plus proches de la question."""
    return _requete(store, embedding_requete_clip(question), k)


def rechercher_images_par_image(store: PGVectorStore, chemin, k: int = 3) -> list[tuple[TextNode, float]]:
    """Recherche image -> image : la photo du technicien est comparée aux figures du document."""
    return _requete(store, embeddings_images([chemin])[0], k)


def _requete(store: PGVectorStore, vecteur: list[float], k: int) -> list[tuple[TextNode, float]]:
    resultat = store.query(VectorStoreQuery(query_embedding=vecteur, similarity_top_k=k))
    return list(zip(resultat.nodes or [], resultat.similarities or []))
