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

## Installation (une seule fois, ~5 minutes) — gratuit, sans carte bancaire

Utilisez partout **le compte Google avec lequel vous ouvrez Classroom**
(vérifiable sur classroom.google.com → photo en haut à droite).
Ignorez toute bannière « Essai gratuit » / « Activer la facturation ».

### 1. Créer le projet
1. Ouvrir <https://console.cloud.google.com/> avec ce compte → accepter les conditions.
2. En haut à gauche : **sélecteur de projet** → **Nouveau projet** → nom `classroom-dl` → **Créer**.
3. Notification → **Sélectionner le projet**.

### 2. Activer les API
1. Barre de recherche : **Google Classroom API** → **Activer**.
2. Barre de recherche : **Google Drive API** → **Activer**.

### 3. Écran de consentement
1. Barre de recherche : **Google Auth Platform** → **Commencer**.
2. Nom `classroom-dl`, e-mail d'assistance = votre e-mail → **Suivant**.
3. Audience : **Externe** → **Suivant**.
4. Coordonnées : votre e-mail → **Suivant** → cocher l'acceptation → **Continuer** → **Créer**.
5. Menu **Audience** → **Utilisateurs test** → **+ Add users** → votre adresse → **Enregistrer**.

### 4. Créer l'identifiant
1. Menu **Clients** → **+ Créer un client**.
2. Type : **Application de bureau**, nom `classroom-dl`.
3. **Laisser décochée** la case « Use this client for an AI-powered agent »
   (elle concerne les agents IA ; ce script est un programme classique).
4. **Créer** → **Télécharger le fichier JSON**.
5. Renommer le fichier en **`credentials.json`** et le placer dans ce dossier
   `classroom_download/`, à côté du script.

### 5. Installer et lancer
Depuis le dossier du dépôt :
```bash
pip install -r classroom_download/requirements.txt
python classroom_download/download_classroom.py
```
Le navigateur s'ouvre :
1. Choisir le compte Google de Classroom.
2. « Google n'a pas validé cette application » → **Paramètres avancés** → **Accéder à classroom-dl**.
3. Cocher toutes les autorisations → **Continuer**.

Les fichiers arrivent dans **Bureau/Classroom**. En mode test, la connexion
expire après 7 jours : le navigateur se rouvrira simplement.

## Options

```bash
python classroom_download/download_classroom.py --cours "IA"      # seulement les cours contenant "IA"
python classroom_download/download_classroom.py --archives        # inclut les cours archivés
python classroom_download/download_classroom.py --dest "D:/Cours" # autre dossier
```

`credentials.json` et `token.json` sont dans le `.gitignore`. **Ne partagez
jamais `token.json`** : il donne accès à votre Classroom et à votre Drive.

## Si l'école bloque l'accès

Certains comptes Google Workspace scolaires interdisent les applications non
validées par l'administrateur (erreur « Accès bloqué »). Solution de repli sans code :
dans Classroom, ouvrez **Google Drive** depuis le cours, sélectionnez les fichiers
(Ctrl+A) dans le dossier partagé par l'enseignant puis **Télécharger** : Drive
génère une archive `.zip` à décompresser sur le Bureau.
