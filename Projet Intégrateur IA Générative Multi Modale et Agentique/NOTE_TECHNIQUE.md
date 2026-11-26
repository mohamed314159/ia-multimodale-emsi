# Note technique — MaintiDoc, Partie 1 : RAG multimodal agentique

## 1. Objectif

Application de question-réponse sur un PDF contenant du texte, des images et des tableaux. Les contenus sont indexés de manière multimodale dans PGVector ; un agent LangChain choisit ses outils de recherche et produit des réponses fondées sur le contexte retrouvé, avec les pages sources.

Document de démonstration : *Attention is all you need* (Vaswani et al., 2017), recommandé pour commencer.

## 2. Modèles choisis

| Rôle | Modèle | Justification |
|---|---|---|
| Embeddings texte | `intfloat/multilingual-e5-small` (384 dim.) | Open source, léger, multilingue : questions en français sur un document en anglais |
| Embeddings images | CLIP `clip-ViT-B-32` (512 dim.) | Image et texte dans le même espace latent : recherche texte → image et image → image |
| Requêtes CLIP | `clip-ViT-B-32-multilingual-v1` | Encodeur texte multilingue aligné sur l'encodeur image de CLIP |
| Description des images | Azure OpenAI `gpt-4.1-mini` | Modèle multimodal : les descriptions rendent les figures interrogeables comme du texte |
| LLM (génération, agent) | Azure OpenAI `gpt-4.1-mini` | Bon appel d'outils et bonne qualité en français |
| Option open source | Qwen `qwen2.5:7b` / `qwen2.5vl:3b` via Ollama | Exécution locale, comme suggéré dans l'énoncé (`LLM_PROVIDER=ollama`) |

## 3. Outils et architecture

| Brique | Outil |
|---|---|
| Lecture et découpage du PDF | LlamaIndex `PyMuPDFReader` + `SentenceSplitter` (512 tokens, chevauchement 64) |
| Tableaux | PyMuPDF `find_tables()` → Markdown → nœuds LlamaIndex |
| Images | PyMuPDF : images intégrées + rendu des figures vectorielles |
| Base vectorielle | PostgreSQL + pgvector (Docker), via LlamaIndex `PGVectorStore` |
| Agent | LangChain `create_agent`, mémoire par fil (`InMemorySaver`) |
| Interface | Streamlit |

Métadonnées stockées avec chaque vecteur : `type` (texte, tableau, image), `fichier`, `page`, `chemin` (images). Elles servent aux citations et au filtrage (outil `rechercher_tableaux`).

Outils de l'agent :
- `rechercher_documentation` : recherche sémantique sur le texte et les descriptions d'images ;
- `rechercher_tableaux` : même recherche, filtrée sur `type = tableau` ;
- `rechercher_figures` : recherche CLIP texte → image.

Une photo jointe à la question est décrite par le modèle vision et comparée aux figures du document (CLIP image → image) avant l'appel à l'agent.

## 4. Limites

- Une seule base, réinitialisée à chaque indexation : un seul document actif à la fois.
- Détection des tableaux et des figures vectorielles heuristique : certains tableaux sans bordures ou certaines figures peuvent être manqués ou mal découpés.
- CLIP `ViT-B-32` est un modèle généraliste : la recherche par image est approximative sur des schémas techniques.
- Le LLM par défaut (Azure) n'est pas open source ; l'option Ollama l'est, mais elle est plus lente sur CPU.
- Les citations indiquent la page, pas la position exacte dans la page.
- Pas encore de reranking, de contrôle d'accès ni d'évaluation chiffrée (prévus aux étapes 2 à 4).

## 5. Exemples de questions / réponses

*À compléter après exécution du notebook ou de l'interface (copier la réponse obtenue et les pages citées).*

| Question | Outils utilisés | Réponse obtenue (résumé) | Pages citées |
|---|---|---|---|
| Qu'est-ce que le multi-head attention et pourquoi l'utiliser ? | | | |
| Quel score BLEU le Transformer obtient-il en anglais-allemand ? | | | |
| Compare les scores BLEU du Transformer base et big. | | | |
| Montre-moi le schéma de l'attention multi-têtes et explique-le. | | | |
| (photo d'une figure) Que représente cette image ? | | | |
