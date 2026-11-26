"""Étape 5 : interface Streamlit de MaintiDoc.

Lancer depuis le dossier du projet :
    uv run streamlit run app.py

Les bibliothèques lourdes (torch, LlamaIndex, LangChain) ne sont chargées qu'au premier
besoin (indexation ou question) : l'interface s'affiche immédiatement.
"""

import uuid
from pathlib import Path

import streamlit as st

from maintidoc import config  # léger : lit seulement le .env

st.set_page_config(page_title="MaintiDoc", page_icon="🛠️", layout="wide")

MODELE = (f"Azure OpenAI {config.AZURE_OPENAI_DEPLOYMENT}" if config.LLM_PROVIDER == "azure"
          else f"Ollama {config.LLM_MODEL}")

st.title("🛠️ MaintiDoc")
st.caption("Assistant documentaire pour techniciens de maintenance : RAG agentique multimodal "
           f"(LlamaIndex · PGVector · CLIP · {MODELE} · LangChain)")

st.session_state.setdefault("messages", [])
st.session_state.setdefault("fil", str(uuid.uuid4()))


@st.cache_resource(show_spinner="Chargement des bibliothèques IA (1 à 2 minutes la première fois)...")
def modules():
    """Import différé des modules lourds, fait une seule fois par serveur."""
    from maintidoc import agent, pipeline, rag
    return agent, pipeline, rag


def activer(moteur, nom: str) -> None:
    agent, _, _ = modules()
    st.session_state.moteur = moteur
    st.session_state.agent = agent.construire_agent(moteur)
    st.session_state.document = nom
    st.session_state.messages = []
    st.session_state.fil = str(uuid.uuid4())


def indexer(pdf: Path, decrire: bool) -> None:
    _, pipeline, _ = modules()
    with st.status("Indexation en cours...", expanded=True) as statut:
        moteur = pipeline.ingerer_pdf(pdf, decrire=decrire, progression=statut.write)
        statut.update(label="Document indexé", state="complete", expanded=False)
    activer(moteur, pdf.name)


def afficher_sources(sources: list[dict]) -> None:
    if not sources:
        return
    with st.expander(f"Sources ({len(sources)})"):
        for s in sources:
            st.markdown(f"**{s['type']}** · page {s['page']} · score {s['score']} · _{s['outil']}_")
            if s.get("chemin") and Path(s["chemin"]).exists():
                st.image(s["chemin"], width=350)
            st.text(s["texte"])
            st.divider()


# ---------- Barre latérale : chargement et indexation ----------
with st.sidebar:
    st.header("1. Document")
    fichier = st.file_uploader("Charger un PDF", type="pdf")
    decrire = st.checkbox("Décrire les images (modèle vision, plus lent)", value=True)

    if st.button("Indexer ce PDF", type="primary", disabled=fichier is None):
        chemin = config.DOSSIER_UPLOADS / fichier.name
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_bytes(fichier.getvalue())
        indexer(chemin, decrire)

    if st.button("Indexer « Attention is all you need »"):
        indexer(config.pdf_par_defaut(), decrire)

    if st.button("Réutiliser l'index déjà dans PostgreSQL"):
        _, _, rag = modules()
        activer(rag.MoteurRAG(), "index existant")

    st.header("2. Mode")
    mode = st.radio("Mode de réponse", ["Agent LangChain", "RAG simple"],
                    help="L'agent choisit ses outils (texte, tableaux, figures) ; "
                         "le RAG simple fait une seule recherche puis génère.")

    st.header("3. Photo (facultatif)")
    photo = st.file_uploader("Joindre une photo à la prochaine question", type=["png", "jpg", "jpeg"])
    if photo is not None:
        st.image(photo, width=200)

    if "document" in st.session_state:
        st.success(f"Document actif : {st.session_state.document}")
    else:
        st.info("Aucun document indexé pour l'instant.")
    if st.button("Nouvelle conversation"):
        st.session_state.messages = []
        st.session_state.fil = str(uuid.uuid4())

# ---------- Zone de discussion ----------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        afficher_sources(message.get("sources", []))

question = st.chat_input("Posez une question sur le document...")
if question:
    if "moteur" not in st.session_state:
        st.warning("Indexez d'abord un document dans la barre latérale.")
        st.stop()

    chemin_photo = None
    if photo is not None:
        chemin_photo = config.DOSSIER_UPLOADS / f"photo_{uuid.uuid4().hex[:8]}_{photo.name}"
        chemin_photo.parent.mkdir(parents=True, exist_ok=True)
        chemin_photo.write_bytes(photo.getvalue())

    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
        if chemin_photo:
            st.image(str(chemin_photo), width=250)

    with st.chat_message("assistant"):
        with st.spinner("Recherche et génération..."):
            if mode == "Agent LangChain":
                resultat = st.session_state.agent.demander(question, fil=st.session_state.fil, image=chemin_photo)
                reponse, sources = resultat["reponse"], resultat["sources"]
                if resultat["outils"]:
                    st.caption("Outils utilisés : " + ", ".join(resultat["outils"]))
            else:
                _, _, rag = modules()
                moteur = st.session_state.moteur
                reponse, passages = moteur.repondre(question, image=chemin_photo)
                sources = rag.en_sources(passages, "rag_simple")
                sources += rag.en_sources(moteur.rechercher_images(question, k=2), "clip")
        st.markdown(reponse)
        afficher_sources(sources)

    st.session_state.messages.append({"role": "assistant", "content": reponse, "sources": sources})
