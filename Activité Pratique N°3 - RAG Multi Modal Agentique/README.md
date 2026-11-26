# Activité Pratique N°3 — RAG Multi Modal Agentique

IA Générative Multi Modale — 5IAD G1, EMSI · BENHAYOUN SADAFI Mohamed

Application RAG multimodale et agentique sur l'article *Attention Is All You Need* (`pdfs/`) :
extraction (PyMuPDF), embeddings communs texte/image (CLIP ViT-B-32), base vectorielle (ChromaDB),
agent ReAct (LangGraph) et LLM multimodal Azure OpenAI.

Un notebook par étape de l'énoncé. Chaque notebook est indépendant : le code des étapes précédentes
dont il a besoin y est refait et signalé par une cellule « 🔁 Code refait ».
Les fichiers produits (`resultats_pdf/`, `chroma_db/`) servent de lien entre les étapes : exécuter dans l'ordre.

| Notebook | Étape de l'énoncé |
|---|---|
| `Etape 1 - Extraction du contenu multimodal.ipynb` | Extraire le texte par page, le découper en chunks, extraire les images |
| `Etape 2 - Embeddings CLIP.ipynb` | CLIP (open_clip ViT-B-32) : texte et images dans le même espace, vecteurs normalisés |
| `Etape 3 - Indexation ChromaDB.ipynb` | ChromaDB persistant, identifiant SHA-256 du document, métadonnées (type, page, chemin) |
| `Etape 4 - Recherche multimodale.ipynb` | Recherche cosinus par texte ou par image, affichage des k meilleurs résultats, génération RAG |
| `Etape 5 - Retriever comme outil agentique.ipynb` | `retriever_tool` (+ `decrire_figure`) avec description et paramètres pour le LLM |
| `Etape 6 - Agent ReAct LangGraph.ipynb` | Agent MIND (LLM) + BODY (outils), cycle Reasoning → Action → Observation, graphe LangGraph compilé |
| `Etape 7 - Tests et validation.ipynb` | Requêtes multimodales complexes, analyse des appels d'outils, évaluation LLM-as-a-judge |

Suite demandée dans le notebook du cours (« Suite à compléter ») :

| Notebook | Contenu |
|---|---|
| `Suite 1 - Serveur MCP du RAG.ipynb` | Le RAG exposé comme serveur MCP (`consulter_pdf`, `rechercher_passages`) sur `http://127.0.0.1:8765/mcp` |
| `Suite 2 - Agent client MCP.ipynb` | Agent LangChain séparé du RAG : il découvre et appelle les outils du serveur MCP |
| `Suite 3 - Interface Streamlit.ipynb` | Génère `app_streamlit.py` et lance l'interface web (question, image facultative, sources) |

Pour la Suite 2, garder le notebook Suite 1 en cours d'exécution dans un autre onglet.

## Configuration

Les clés et modèles Azure OpenAI sont lus dans le `.env` de l'AP5
(`../Activité Pratique N°5- Agentic AI et MCP - Langchain et LangGraph/.env`, déploiement `gpt-4.1-mini`).
Un `.env` placé dans ce dossier serait prioritaire (modèle : `.env.example`). Aucun `.env` n'est versionné.

```bash
uv sync
```

Puis ouvrir les notebooks avec le noyau `.venv` de ce dossier.
