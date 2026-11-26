"""MaintiDoc - assistant documentaire pour techniciens de maintenance.

Partie 1 du projet intégrateur : RAG agentique multimodal.

Modules :
- config     : paramètres (lus depuis .env)
- extraction : étape 2, extraction du texte, des tableaux et des images du PDF
- images     : étape 3, embeddings CLIP et descriptions des images
- indexation : étape 2/3, stockage des vecteurs dans PGVector (PostgreSQL)
- llm        : modèle de chat, Azure OpenAI (défaut) ou Qwen via Ollama
- rag        : étape 4, recherche + génération
- agent      : étape 6, agent LangChain qui choisit ses outils de recherche
- pipeline   : enchaîne les étapes 2 et 3 en une seule fonction
"""
