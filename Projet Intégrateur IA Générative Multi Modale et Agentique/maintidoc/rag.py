"""Étape 4 : question-réponse et génération.

1. Récupérer les passages pertinents dans PGVector (texte, tableaux, descriptions d'images).
2. Construire un prompt avec ce contexte.
3. Générer une réponse sourcée avec le LLM (Azure gpt-4.1-mini, ou Qwen via Ollama).
"""

from llama_index.core.schema import NodeWithScore
from llama_index.core.vector_stores import MetadataFilter, MetadataFilters

from .images import decrire_image
from .llm import chat_model
from .indexation import (charger_index_textes, charger_store_images, rechercher_images_clip,
                         rechercher_images_par_image)

PROMPT_RAG = """Tu es MaintiDoc, un assistant documentaire pour techniciens de maintenance.
Réponds à la question en t'appuyant UNIQUEMENT sur les extraits ci-dessous.
Cite tes sources avec leur numéro et leur page, par exemple [2] (page 3).
Si les extraits ne permettent pas de répondre, dis-le clairement au lieu d'inventer.
Réponds en français.

Extraits :
{contexte}

Question : {question}

Réponse :"""


def formater_passages(passages: list[NodeWithScore], max_caracteres: int = 1200) -> str:
    """Met en forme les passages retrouvés, numérotés, avec leur type et leur page."""
    if not passages:
        return "Aucun passage trouvé."
    blocs = []
    for i, p in enumerate(passages, start=1):
        m = p.node.metadata
        texte = p.node.get_content()[:max_caracteres]
        blocs.append(f"[{i}] ({m.get('type')} - {m.get('fichier')}, page {m.get('page')})\n{texte}")
    return "\n\n".join(blocs)


def en_sources(passages: list[NodeWithScore], outil: str) -> list[dict]:
    """Convertit des passages en dictionnaires simples (affichage Streamlit)."""
    return [
        {"outil": outil, "type": p.node.metadata.get("type"), "page": p.node.metadata.get("page"),
         "chemin": p.node.metadata.get("chemin"), "score": round(p.score or 0, 3),
         "texte": p.node.get_content()[:500]}
        for p in passages
    ]


class MoteurRAG:
    """Regroupe l'index texte, l'index images (CLIP) et le LLM."""

    def __init__(self, index=None, store_images=None):
        self.index = index if index is not None else charger_index_textes()
        self.store_images = store_images if store_images is not None else charger_store_images()
        self.llm = chat_model(temperature=0.1)

    def rechercher(self, question: str, k: int = 5, type_: str | None = None) -> list[NodeWithScore]:
        """Recherche sémantique ; `type_` peut filtrer sur "texte", "tableau" ou "image"."""
        filtres = MetadataFilters(filters=[MetadataFilter(key="type", value=type_)]) if type_ else None
        return self.index.as_retriever(similarity_top_k=k, filters=filtres).retrieve(question)

    def rechercher_images(self, question: str, k: int = 3) -> list[NodeWithScore]:
        """Recherche CLIP texte -> image."""
        return [NodeWithScore(node=n, score=s) for n, s in rechercher_images_clip(self.store_images, question, k)]

    def rechercher_par_image(self, chemin, k: int = 3) -> list[NodeWithScore]:
        """Recherche CLIP image -> image (requête avec une photo)."""
        return [NodeWithScore(node=n, score=s) for n, s in rechercher_images_par_image(self.store_images, chemin, k)]

    def enrichir_question(self, question: str, image=None) -> tuple[str, list[NodeWithScore]]:
        """Requête multimodale (texte + image) : la photo est décrite par le modèle vision
        et comparée aux figures du document avec CLIP ; le tout est ajouté à la question."""
        if image is None:
            return question, []
        description = decrire_image(image)
        similaires = self.rechercher_par_image(image, k=2)
        texte = (f"{question}\n\n[Photo jointe par l'utilisateur] Description : {description}\n"
                 f"Figures du document les plus proches de la photo :\n{formater_passages(similaires, 400)}")
        return texte, similaires

    def repondre(self, question: str, k: int = 5, image=None) -> tuple[str, list[NodeWithScore]]:
        """Pipeline RAG complet : récupération puis génération (image facultative)."""
        question_complete, similaires = self.enrichir_question(question, image)
        passages = self.rechercher(question_complete, k)
        prompt = PROMPT_RAG.format(contexte=formater_passages(passages), question=question_complete)
        return self.llm.invoke(prompt).content.strip(), passages + similaires
