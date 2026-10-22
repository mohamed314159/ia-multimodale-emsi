# Télécharger tous les fichiers Google Classroom

Le script `download_classroom.py` récupère toutes les pièces jointes (PDF, Docs,
Slides, etc.) postées dans vos cours Classroom — devoirs, supports et annonces —
et les range sur votre Bureau :

```
Bureau/Classroom/
├── IA Générative Multi-Modale - 5eme annee EMSI/
│   ├── TP 1 - PyTorch/
│   │   └── lab1.pdf
│   ├── Cours - Introduction/
│   │   └── Part 1 - Support.pdf
│   └── liens.txt          # liens web et vidéos YouTube postés
└── ...
```

- Les dossiers de cours sont renommés : le code « 5IAD G1 » est retiré et
  « - 5eme annee EMSI » est ajouté à la fin (modifiable via `COURSE_SUFFIX`).
- Les Google Docs/Slides sont exportés en PDF, les Sheets en `.xlsx`.
- Les fichiers déjà téléchargés sont ignorés : relancez le script après chaque
  nouveau post, il ne récupère que les nouveautés.
- 8 téléchargements en parallèle (réglable avec `--threads`).

## Installation (une seule fois, ~5 minutes)

1. **Créer un identifiant Google** :
   1. Ouvrez <https://console.cloud.google.com/> et créez un projet (ex. « classroom-dl »).
   2. *API et services → Bibliothèque* : activez **Google Classroom API** et **Google Drive API**.
   3. *API et services → Écran de consentement OAuth* : type « Externe », remplissez
      le nom de l'app et votre e-mail, puis ajoutez votre adresse EMSI dans
      **Utilisateurs test**.
   4. *API et services → Identifiants → Créer des identifiants → ID client OAuth*,
      type **Application de bureau**. Téléchargez le JSON et enregistrez-le sous
      `classroom_download/credentials.json`.
2. **Installer les dépendances** :
   ```bash
   pip install -r requirements.txt
   ```

## Utilisation

```bash
python download_classroom.py                   # tous les cours actifs
python download_classroom.py --cours "IA"      # seulement les cours contenant "IA"
python download_classroom.py --archives        # inclut les cours archivés
python download_classroom.py --dest "D:/Cours" # autre dossier
```

Au premier lancement, le navigateur s'ouvre pour vous connecter avec votre compte
Classroom ; un fichier `token.json` est ensuite créé pour ne plus redemander.
`credentials.json` et `token.json` sont dans le `.gitignore` : ne les publiez pas.

## Si l'école bloque l'accès

Certains comptes Google Workspace scolaires interdisent les applications non
validées par l'administrateur (erreur « Accès bloqué »). Solution de repli sans code :
dans Classroom, ouvrez **Google Drive** depuis le cours, sélectionnez les fichiers
(Ctrl+A) dans le dossier partagé par l'enseignant puis **Télécharger** : Drive
génère une archive `.zip` à décompresser sur le Bureau.
