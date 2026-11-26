"""Interface web Streamlit du chatbot Agentic RAG (LangGraph).

Lancement, depuis le dossier de l'AP5 :
    uv run streamlit run rag_agentique/app_streamlit.py
"""

import re
import sys
import uuid
from pathlib import Path

import streamlit as st
from langchain.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver

sys.path.insert(0, str(Path(__file__).resolve().parent))
from graphe import construire_graphe  # noqa: E402

st.set_page_config(page_title="Chatbot Agentic RAG", page_icon="🤖")


@st.cache_resource(show_spinner="Chargement de l'index du cours...")
def obtenir_graphe():
    # Un seul graphe pour toute l'application ; chaque conversation a son propre thread_id
    return construire_graphe(checkpointer=InMemorySaver())


def nouvelle_conversation():
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.historique = []


if "thread_id" not in st.session_state:
    nouvelle_conversation()

with st.sidebar:
    st.header("Agentic RAG")
    st.write("Questions sur le support de cours **Agentic AI et MCP** (LangChain, LangGraph, MCP).")
    st.write("L'agent décide de chercher dans le cours, évalue la pertinence des passages, "
             "reformule sa recherche si besoin, puis répond en citant les pages.")
    st.button("Nouvelle conversation", on_click=nouvelle_conversation, use_container_width=True)
    st.caption(f"Conversation : `{st.session_state.thread_id[:8]}`")

st.title("🤖 Chatbot Agentic RAG")

for message in st.session_state.historique:
    with st.chat_message(message["role"]):
        st.markdown(message["contenu"])
        if message.get("etapes"):
            with st.expander("Étapes de l'agent"):
                st.markdown(message["etapes"])

question = st.chat_input("Posez une question sur le cours...")
if question:
    st.session_state.historique.append({"role": "user", "contenu": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        etapes, reponse = [], ""
        with st.status("L'agent réfléchit...", expanded=False) as statut:
            config = {"configurable": {"thread_id": st.session_state.thread_id}}
            for mise_a_jour in obtenir_graphe().stream({"messages": [HumanMessage(question)]}, config=config,
                                                       stream_mode="updates"):
                for noeud, valeur in mise_a_jour.items():
                    dernier = (valeur or {}).get("messages", [None])[-1]
                    if isinstance(dernier, AIMessage) and dernier.tool_calls:
                        requetes = ", ".join(f"« {tc['args'].get('requete', '')} »" for tc in dernier.tool_calls)
                        etapes.append(f"- **{noeud}** : recherche dans le cours {requetes}")
                    elif isinstance(dernier, ToolMessage):
                        pages = sorted(set(re.findall(r"\[p\. (\d+)\]", dernier.content)), key=int)
                        etapes.append(f"- **{noeud}** : passages des pages {', '.join(pages)}")
                    elif isinstance(dernier, HumanMessage):
                        etapes.append(f"- **{noeud}** : nouvelle requête « {dernier.content} »")
                    elif isinstance(dernier, AIMessage):
                        etapes.append(f"- **{noeud}** : réponse rédigée")
                        reponse = dernier.content
                    statut.update(label=f"Étape : {noeud}")
            statut.update(label="Réponse prête", state="complete")
        st.markdown(reponse)
        texte_etapes = "\n".join(etapes)
        with st.expander("Étapes de l'agent"):
            st.markdown(texte_etapes)

    st.session_state.historique.append({"role": "assistant", "contenu": reponse, "etapes": texte_etapes})
