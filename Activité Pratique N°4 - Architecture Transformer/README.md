# Activité Pratique N°4 — Architecture Transformer

IA Générative Multi Modale — 5IAD G1, EMSI · BENHAYOUN SADAFI Mohamed

Chaque étape et chaque exercice a son propre notebook. Chaque notebook est indépendant :
le code dont il a besoin (dataset, fonctions d'entraînement…) y est refait et signalé par une cellule « 🔁 Code refait ».

## Partie 1 — `Partie 1/`

| Notebook | Travail demandé |
|---|---|
| `1 - Dataset serie temporelle.ipynb` | Générer la série `s = sin(x)` (200 valeurs entre 0 et 20) et la ranger en séquences de 10 valeurs |
| `2 - Modele RNN.ipynb` | Créer, entraîner et tester un RNN (16 unités) qui prédit la valeur suivante |
| `3 - Modele LSTM.ipynb` | Même chose avec un LSTM (16 unités) |
| `4 - Modele Transformer.ipynb` | Même chose avec un Transformer (projection 1→16, positions apprises, attention 2 têtes, FFN 16→32→16) + comparaison des trois modèles |
| `5 - Modele GPT.ipynb` | GPT-2 préentraîné : prédire la suite de « Artificial intelligence can… » |
| `6 - Modele BERT.ipynb` | BERT multilingue : prédire le mot masqué de « Rabat est [MASK] du Maroc » |

Exécuter les notebooks 2 et 3 avant le 4 : la comparaison relit leurs résultats dans `resultats_partie1.json`.

## Partie 2 — `Partie 2/` (exercices de la fin du notebook du cours)

| Notebook | Exercice |
|---|---|
| `Exercice 1 - Consommation electrique Transformer.ipynb` | `EnergyTransformer` : 24 h de consommation → heure suivante, comparé à la persistance et à la référence journalière (+ fenêtre de 168 h) |
| `Exercice 2 - Mini GPT.ipynb` | Mini-GPT par caractères entraîné sur `corpus.txt`, masque causal, températures 0.5 / 1.0 / 1.5 |
| `Exercice 3 - Mini BERT.ipynb` | Mini-BERT par mots : masquage 15 % (80/10/10), masque de padding, exactitude et top-3 |

Le jeu de données de l'exercice 1 est lu directement dans le zip de `Supports de cours/` (pas besoin de le décompresser).

## Lancer les notebooks

```bash
uv sync
```

Puis ouvrir un notebook dans VS Code / Jupyter avec le noyau `.venv` de ce dossier.
PyTorch est installé avec CUDA 12.6 (GPU utilisé s'il est disponible, sinon CPU).
