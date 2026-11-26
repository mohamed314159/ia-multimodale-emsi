"""Étape 6 : orchestration agentique avec LangChain.

L'agent (Azure gpt-4.1-mini, ou Qwen via Ollama) dispose de trois outils et choisit lui-même lesquels appeler :
- rechercher_documentation : passages de texte (et descriptions d'images)
- rechercher_tableaux      : uniquement les tableaux
- rechercher_figures       : images retrouvées par CLIP, avec leur description

Requête multimodale : une photo peut accompagner la question (décrite par le modèle
vision et comparée aux figures du document avec CLIP).

Gestion du contexte :
- mémoire de conversation par fil (checkpointer InMemorySaver + thread_id)
- passages tronqués pour ne pas saturer la fenêtre de contexte du modèle
"""

from dataclasses import dataclass, field

from langchain.agents import create_agent
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver

from .llm import chat_model
from .rag import MoteurRAG, en_sources, formater_passages

PROMPT_SYSTEME = """Tu es MaintiDoc, un assistant documentaire pour techniciens de maintenance.
Pour répondre, utilise tes outils de recherche dans la documentation indexée :
- rechercher_documentation pour les questions générales sur le contenu,
- rechercher_tableaux pour les valeurs chiffrées, résultats ou comparaisons,
- rechercher_figures quand la question porte sur un schéma, une figure ou une photo.
Tu peux appeler plusieurs outils. Base ta réponse uniquement sur ce qu'ils renvoient,
cite les pages utilisées, et dis-le si l'information est absente. Réponds en français.
Tu ne pilotes aucun équipement et ne remplaces pas un technicien habilité."""


@dataclass
class AgentMaintiDoc:
    agent: object
    moteur: MoteurRAG
    sources: list[dict] = field(default_factory=list)

    def demander(self, question: str, fil: str = "defaut", image=None) -> dict:
        """Pose une question (avec une photo facultative) ; `fil` identifie la conversation."""
        self.sources.clear()
        question, similaires = self.moteur.enrichir_question(question, image)
        self.sources.extend(en_sources(similaires, "photo_jointe"))
        etat = self.agent.invoke(
            {"messages": [{"role": "user", "content": question}]},
            config={"configurable": {"thread_id": fil}},
        )
        return {
            "reponse": etat["messages"][-1].content,
            "sources": list(self.sources),
            "outils": sorted({s["outil"] for s in self.sources}),
        }


def construire_agent(moteur: MoteurRAG, k: int = 4) -> AgentMaintiDoc:
    sources: list[dict] = []

    @tool
    def rechercher_documentation(requete: str) -> str:
        """Cherche des passages de texte dans la documentation technique indexée."""
        passages = moteur.rechercher(requete, k=k)
        sources.extend(en_sources(passages, "rechercher_documentation"))
        return formater_passages(passages, max_caracteres=1000)

    @tool
    def rechercher_tableaux(requete: str) -> str:
        """Cherche uniquement dans les tableaux du document (valeurs, résultats, comparaisons)."""
        passages = moteur.rechercher(requete, k=3, type_="tableau")
        sources.extend(en_sources(passages, "rechercher_tableaux"))
        return formater_passages(passages, max_caracteres=1500)

    @tool
    def rechercher_figures(requete: str) -> str:
        """Cherche les figures, schémas ou photos du document (CLIP) et renvoie leur description."""
        passages = moteur.rechercher_images(requete, k=3)
        sources.extend(en_sources(passages, "rechercher_figures"))
        return formater_passages(passages, max_caracteres=800)

    agent = create_agent(
        model=chat_model(),
        tools=[rechercher_documentation, rechercher_tableaux, rechercher_figures],
        system_prompt=PROMPT_SYSTEME,
        checkpointer=InMemorySaver(),
    )
    return AgentMaintiDoc(agent=agent, moteur=moteur, sources=sources)
