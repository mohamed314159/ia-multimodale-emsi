# Projet Intégrateur — MaintiDoc

Assistant documentaire pour techniciens de maintenance : il exploite des manuels, schémas et photographies pour répondre à des questions techniques **avec des références vérifiables**. Il ne pilote aucun équipement et ne remplace pas un technicien habilité.

| Étape (feuille de route) | Version | État |
|---|---|---|
| 1. RAG agentique multimodal | V1 | ✅ ce dossier |
| 2. Multimodalité et fine-tuning (reranker adapté, nDCG@5 / MRR@10) | V2 | à venir |
| 3. Orchestration agentique LangGraph et MCP (historique, tickets avec approbation) | V3 | à venir |
| 4. Bot Telegram/Discord, sécurité et déploiement | V4 | à venir |

## Partie 1 : RAG agentique multimodal

```
PDF ──► LlamaIndex (PyMuPDFReader + SentenceSplitter) ──► textes ─┐
   ├──► PyMuPDF find_tables ──► tableaux (Markdown) ──────────────┤──► embeddings e5 ──► PGVector (data_maintidoc_texte)
   └──► images PNG ──► gpt-4.1-mini (vision) ──► descriptions ────┘
                  └──► CLIP image encoder ─────────────────────────────────────────────► PGVector (data_maintidoc_images)

Question (texte + photo facultative)
   └──► Agent LangChain (Azure gpt-4.1-mini)
          ├── outil rechercher_documentation  (texte + descriptions d'images)
          ├── outil rechercher_tableaux       (filtre type = tableau)
          └── outil rechercher_figures        (CLIP texte -> image)
   └──► Réponse sourcée (pages) + figures, dans Streamlit
```

| Travail demandé | Réalisation |
|---|---|
| 1. Sélection du document | *Attention is all you need* (dans `Supports de cours/`) |
| 2. Extraction et indexation | `maintidoc/extraction.py`, `maintidoc/indexation.py` — LlamaIndex, `intfloat/multilingual-e5-small` (open source), PGVector |
| 3. Traitement des images | `maintidoc/images.py` — CLIP (`clip-ViT-B-32` + encodeur texte multilingue), descriptions par le modèle vision |
| 4. Question-réponse | `maintidoc/rag.py` — réponses avec citations de pages |
| 5. Interface | `app.py` — Streamlit |
| 6. Orchestration agentique | `maintidoc/agent.py` — LangChain `create_agent`, 3 outils, mémoire par fil |

Le notebook **`Partie 1 - RAG Multimodal Agentique.ipynb`** déroule et explique les 6 étapes. La note technique demandée est dans [`NOTE_TECHNIQUE.md`](NOTE_TECHNIQUE.md).

### Modèles

| Rôle | Par défaut | Option open source |
|---|---|---|
| LLM (génération, agent) | Azure OpenAI `gpt-4.1-mini` | Qwen `qwen2.5:7b` via Ollama |
| Description des images | Azure OpenAI `gpt-4.1-mini` | `qwen2.5vl:3b` via Ollama |
| Embeddings texte | `intfloat/multilingual-e5-small` (local) | — |
| Embeddings images | CLIP `clip-ViT-B-32` (local) | — |

Pour passer à Ollama : `LLM_PROVIDER=ollama` dans `.env`, puis `ollama pull qwen2.5:7b` et `ollama pull qwen2.5vl:3b`.

## Prérequis

- [uv](https://docs.astral.sh/uv/), Python 3.12
- Docker Desktop (pour PostgreSQL + pgvector)
- Un déploiement Azure OpenAI (`gpt-4.1-mini`), le même que pour l'AP5

## Installation

```bash
cp .env.example .env        # puis remplir les clés Azure
docker compose up -d
uv sync
```

Au premier lancement, les modèles Hugging Face (e5, CLIP) sont téléchargés automatiquement.

## Lancement

- Notebook : ouvrir `Partie 1 - RAG Multimodal Agentique.ipynb` avec le noyau `.venv` du projet.
- Interface : `uv run streamlit run app.py`

## Structure

```
├── app.py                     Interface Streamlit (étape 5)
├── Partie 1 - RAG Multimodal Agentique.ipynb
├── NOTE_TECHNIQUE.md          Modèles, outils, limites, exemples
├── maintidoc/
│   ├── config.py              Paramètres lus depuis .env
│   ├── llm.py                 Azure OpenAI ou Ollama
│   ├── extraction.py          Texte, tableaux, images du PDF (étape 2)
│   ├── images.py              CLIP + descriptions d'images (étape 3)
│   ├── indexation.py          PGVector (étapes 2 et 3)
│   ├── rag.py                 Pipeline RAG (étape 4)
│   ├── agent.py               Agent LangChain (étape 6)
│   └── pipeline.py            Enchaîne extraction + indexation
├── docker-compose.yml         PostgreSQL + pgvector (port 5433)
├── .env.example               Modèle du fichier .env (le .env n'est pas versionné)
└── data/                      Images extraites et PDF chargés (non versionnés)
```
