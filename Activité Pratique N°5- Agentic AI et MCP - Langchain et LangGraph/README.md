# Activité Pratique N°5 — Agentic AI et MCP : LangChain et LangGraph

IA Générative Multi Modale — 5IAD G1, EMSI · BENHAYOUN SADAFI Mohamed

Agents IA avec LangChain, workflows LangGraph, protocole MCP et un cas de synthèse multi-agents,
avec Azure OpenAI (`gpt-4.1-mini`, embeddings `text-embedding-3-small`) et Tavily.

## Notebooks

Un notebook par partie de l'énoncé, exécuté et enregistré avec ses sorties.

| Notebook | Partie de l'énoncé |
|---|---|
| `Etape A.ipynb` | **A — LangChain** : agent simple, configuration du modèle, mémoire, tools, tools prédéfinis (DuckDuckGo, Tavily, PythonREPLTool), middlewares (dynamic_model, dynamic_prompt, tool_error_handling, guardrails, Human in the Loop), chatbot RAG agentique |
| `Etape B1 - Bases LangGraph.ipynb` | **B partie 1** : state, nodes, edges, arêtes conditionnelles, boucle, reducers et parallélisme, agent ReAct construit à la main, streaming, mémoire, `interrupt` |
| `Etape B2 - Agentic RAG LangGraph.ipynb` | **B partie 2** : chatbot Agentic RAG (décision, évaluation de la pertinence, reformulation), test avec LangGraph Studio, interface Streamlit |
| `Etape C - MCP.ipynb` | **C — MCP** : serveur MCP à deux tools, test avec MCP Inspector, agents LangChain et LangGraph clients en streamable-http, agent N8N |
| `Etape D - Synthèse SAV.ipynb` | **D — Synthèse** : orchestrateur LangGraph, agent documentaire (tool distant `rag_multimodal` via MCP, RAG multimodal), agent garantie (tool local en lecture seule) |

Ordre d'exécution : A crée l'index FAISS du cours (`index_faiss_cours.bin`) réutilisé par B2 (il est reconstruit s'il manque).

## Fichiers

| Dossier / fichier | Contenu |
|---|---|
| `rag_agentique/graphe.py` | Graphe Agentic RAG (variable `graph`) utilisé par LangGraph Studio et Streamlit |
| `rag_agentique/app_streamlit.py` | Interface web du chatbot |
| `langgraph.json` | Configuration de `langgraph dev` / LangGraph Studio |
| `mcp_demo/serveur_mcp.py` | Serveur MCP (`get_employee_infos`, `search`), port 24000 |
| `mcp_demo/agent_mcp.py` | Agent LangChain en ligne de commande, client du serveur MCP |
| `mcp_demo/n8n_agent_mcp.json` | Workflow N8N à importer (Chat Trigger → AI Agent + Azure OpenAI + mémoire + MCP Client Tool) |
| `sav/` | Cas de synthèse : données (manuels, figures, photo client, registre des garanties), RAG multimodal, serveur MCP `rag_multimodal` (port 24001) |
| `verifier_env.py` | Vérifie les clés du `.env` (Azure chat, embeddings, Tavily) |

## Configuration

Créer `.env` à partir de `.env.example` (Azure OpenAI + Tavily), puis :

```bash
uv sync
uv run python verifier_env.py
```

Ouvrir les notebooks avec le noyau `.venv` de ce dossier.

## Commandes utiles

```bash
uv run langgraph dev                                  # LangGraph Studio (graphe rag_agentique)
uv run streamlit run rag_agentique/app_streamlit.py   # interface web du chatbot Agentic RAG
uv run python mcp_demo/serveur_mcp.py                 # serveur MCP de la partie C
uv run python mcp_demo/agent_mcp.py                   # agent client en ligne de commande
uv run python sav/serveur_mcp_rag.py                  # serveur MCP du SAV (partie D)
```

MCP Inspector : `npx @modelcontextprotocol/inspector` (ou l'image Docker `ghcr.io/modelcontextprotocol/inspector`),
transport **Streamable HTTP**, URL `http://127.0.0.1:24000/mcp`.

N8N : voir la section 6 de `Etape C - MCP.ipynb` (lancer le serveur MCP avec `MCP_HOST=0.0.0.0` si N8N tourne dans Docker).
