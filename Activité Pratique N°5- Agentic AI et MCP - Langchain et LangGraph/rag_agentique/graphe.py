"""Chatbot Agentic RAG construit avec LangGraph, sur le support de cours « Agentic AI et MCP ».

Ce module est utilisé par :
- LangGraph Studio (fichier langgraph.json à la racine de l'AP5, variable `graph`) ;
- l'interface web Streamlit (rag_agentique/app_streamlit.py).

Graphe :
    START -> agent --(pas de tool)--> END
               |
               +--(tool_calls)--> recuperer --> [pertinent ?] --oui--> generer --> END
                                                    |
                                                    +--non--> reformuler --> agent
"""

import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from langchain.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain.tools import tool
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic import BaseModel, Field

DOSSIER_AP5 = Path(__file__).resolve().parent.parent
PDF_COURS = DOSSIER_AP5 / "Supports de cours" / "Annonce - Agentic AI et MCP - Langchain et Langgraph" / "Agentic AI et MCP.pdf"
FICHIER_INDEX = DOSSIER_AP5 / "index_faiss_cours.bin"   # créé par la partie A.6
MAX_REFORMULATIONS = 2

load_dotenv(DOSSIER_AP5 / ".env")


def _azure() -> dict:
    return dict(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    )


def creer_llm(temperature: float = 0) -> AzureChatOpenAI:
    return AzureChatOpenAI(**_azure(), azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
                           temperature=temperature, timeout=60)


def creer_embeddings() -> AzureOpenAIEmbeddings:
    return AzureOpenAIEmbeddings(**_azure(), azure_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
                                 chunk_size=64)


def charger_index() -> FAISS:
    """Charge l'index FAISS du cours (créé par la partie A.6) ou le construit s'il n'existe pas.

    L'index est sérialisé en un seul fichier lu par Python : FAISS (C++) ne sait pas ouvrir
    un chemin Windows contenant des accents comme « Activité Pratique N°5 »."""
    embeddings = creer_embeddings()
    if FICHIER_INDEX.exists():
        return FAISS.deserialize_from_bytes(FICHIER_INDEX.read_bytes(), embeddings,
                                            allow_dangerous_deserialization=True)
    pages = [p for p in PyPDFLoader(str(PDF_COURS)).load() if p.page_content.strip()]
    chunks = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200).split_documents(pages)
    index = FAISS.from_documents(chunks, embeddings)
    FICHIER_INDEX.write_bytes(index.serialize_to_bytes())
    return index


# ---------------------------------------------------------------- prompts

PROMPT_AGENT = """Tu es l'assistant pédagogique du cours « Agentic AI et MCP » (LangChain, LangGraph, MCP).
Réponds en français.
- Pour toute question sur le contenu du cours, appelle le tool rechercher_cours. Rédige une requête riche :
  les mots-clés de la question, leurs synonymes et leur équivalent anglais
  (ex. « mémoire » -> « mémoire de la conversation memory checkpointer InMemorySaver thread_id »).
- Pour une salutation ou une question sur la conversation elle-même, réponds directement sans tool."""

PROMPT_NOTEUR = """Tu évalues si des passages retrouvés permettent de répondre à une question.
Question : {question}

Passages :
{passages}

Réponds « oui » seulement si les passages contiennent de quoi répondre directement à la question
(le sujet précis de la question doit y être traité), sinon « non »."""

PROMPT_REFORMULATION = """La recherche documentaire n'a rien donné d'utile pour cette question :
« {question} »
Reformule-la en une requête de recherche plus précise pour un support de cours sur LangChain, LangGraph,
les agents IA et le protocole MCP (mots-clés techniques, éventuellement en anglais). Donne uniquement la requête."""

PROMPT_GENERATION = """Tu réponds à la question d'un étudiant à partir des passages du cours ci-dessous.
Règles :
1. Réponds en français, de façon claire et structurée.
2. Appuie-toi uniquement sur les passages ; n'invente rien.
3. Cite les pages utilisées sous la forme [p. N].
4. Si les passages ne suffisent pas, dis-le clairement.

Question : {question}

Passages du cours :
{passages}"""


class Pertinence(BaseModel):
    """Verdict sur la pertinence des passages retrouvés."""
    pertinent: Literal["oui", "non"] = Field(description="Les passages permettent-ils de répondre ?")
    raison: str = Field(description="Justification en une phrase")


class EtatRAG(MessagesState):
    reformulations: int


# ---------------------------------------------------------------- graphe

def _derniere_question(etat: EtatRAG) -> str:
    return next(m.content for m in reversed(etat["messages"]) if isinstance(m, HumanMessage))


def _derniers_passages(etat: EtatRAG) -> str:
    return next(m.content for m in reversed(etat["messages"]) if isinstance(m, ToolMessage))


def construire_graphe(checkpointer=None, index: FAISS | None = None):
    index = index or charger_index()
    llm = creer_llm()

    @tool
    def rechercher_cours(requete: str) -> str:
        """Recherche les passages les plus pertinents dans le support de cours « Agentic AI et MCP »
        (agents, pattern ReAct, LangChain, middlewares, guardrails, RAG, LangGraph, MCP). Renvoie les passages avec leur page."""
        documents = index.similarity_search(requete, k=6)
        return "\n\n".join(f"[p. {d.metadata.get('page_label', d.metadata.get('page', '?'))}] {d.page_content}"
                           for d in documents)

    llm_avec_outil = llm.bind_tools([rechercher_cours])
    noteur = llm.with_structured_output(Pertinence)

    def agent(etat: EtatRAG) -> dict:
        """Décide : répondre directement ou lancer une recherche dans le cours."""
        return {"messages": [llm_avec_outil.invoke([SystemMessage(PROMPT_AGENT)] + etat["messages"])]}

    def evaluer_pertinence(etat: EtatRAG) -> Literal["generer", "reformuler"]:
        """Arête conditionnelle : les passages retrouvés sont-ils pertinents ?"""
        if etat.get("reformulations", 0) >= MAX_REFORMULATIONS:
            return "generer"
        verdict = noteur.invoke(PROMPT_NOTEUR.format(question=_derniere_question(etat),
                                                     passages=_derniers_passages(etat)))
        return "generer" if verdict.pertinent == "oui" else "reformuler"

    def reformuler(etat: EtatRAG) -> dict:
        """Réécrit la question pour une nouvelle recherche."""
        nouvelle = llm.invoke(PROMPT_REFORMULATION.format(question=_derniere_question(etat))).content
        return {"messages": [HumanMessage(nouvelle, name="reformulation")],
                "reformulations": etat.get("reformulations", 0) + 1}

    def generer(etat: EtatRAG) -> dict:
        """Rédige la réponse finale sourcée à partir des passages retrouvés."""
        question = next(m.content for m in reversed(etat["messages"])
                        if isinstance(m, HumanMessage) and m.name != "reformulation")
        reponse = llm.invoke(PROMPT_GENERATION.format(question=question, passages=_derniers_passages(etat)))
        return {"messages": [AIMessage(reponse.content)], "reformulations": 0}

    workflow = StateGraph(EtatRAG)
    workflow.add_node("agent", agent)
    workflow.add_node("recuperer", ToolNode([rechercher_cours]))
    workflow.add_node("reformuler", reformuler)
    workflow.add_node("generer", generer)

    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", tools_condition, {"tools": "recuperer", END: END})
    workflow.add_conditional_edges("recuperer", evaluer_pertinence)
    workflow.add_edge("reformuler", "agent")
    workflow.add_edge("generer", END)
    return workflow.compile(checkpointer=checkpointer)


# Graphe exposé à LangGraph Studio (la persistance est fournie par le serveur `langgraph dev`)
graph = construire_graphe()
