"""Télécharge tous les fichiers postés sur Google Classroom vers le Bureau.

Parcourt chaque cours (devoirs, supports de cours, annonces), télécharge les
pièces jointes Google Drive et range tout dans Bureau/Classroom/<cours>/<post>/.
Les fichiers déjà présents sont ignorés : relancer le script ne télécharge
que les nouveautés.

Usage :
    python download_classroom.py                    # tous les cours actifs
    python download_classroom.py --cours "IA"       # cours dont le nom contient "IA"
    python download_classroom.py --archives         # inclut les cours archivés
    python download_classroom.py --dest D:/Cours    # autre dossier de destination
"""

import argparse
import io
import os
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

SCOPES = [
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/classroom.coursework.me.readonly",
    "https://www.googleapis.com/auth/classroom.courseworkmaterials.readonly",
    "https://www.googleapis.com/auth/classroom.announcements.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

HERE = Path(__file__).resolve().parent
CREDENTIALS_FILE = HERE / "credentials.json"
TOKEN_FILE = HERE / "token.json"

# Les fichiers Google natifs (Docs, Slides...) doivent être exportés.
EXPORTS = {
    "application/vnd.google-apps.document": ("application/pdf", ".pdf"),
    "application/vnd.google-apps.presentation": ("application/pdf", ".pdf"),
    "application/vnd.google-apps.spreadsheet": (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xlsx",
    ),
    "application/vnd.google-apps.drawing": ("application/pdf", ".pdf"),
}

_local = threading.local()


def get_credentials():
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        if not CREDENTIALS_FILE.exists():
            raise SystemExit(
                f"Fichier {CREDENTIALS_FILE} introuvable. "
                "Voir le README pour créer l'identifiant OAuth."
            )
        flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
        creds = flow.run_local_server(port=0)
    TOKEN_FILE.write_text(creds.to_json())
    return creds


def default_desktop():
    home = Path.home()
    candidates = [
        Path(os.environ["OneDrive"]) / "Desktop" if "OneDrive" in os.environ else None,
        Path(os.environ["OneDrive"]) / "Bureau" if "OneDrive" in os.environ else None,
        home / "Desktop",
        home / "Bureau",
    ]
    for path in candidates:
        if path and path.is_dir():
            return path
    return home


def safe_name(name, max_len=120):
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name or "sans_titre")
    name = re.sub(r"\s+", " ", name).strip(" .")
    return name[:max_len] or "sans_titre"


def list_all(method, key, **kwargs):
    items, token = [], None
    while True:
        resp = method(pageToken=token, **kwargs).execute()
        items.extend(resp.get(key, []))
        token = resp.get("nextPageToken")
        if not token:
            return items


def collect_posts(classroom, course_id):
    """Renvoie [(titre du post, liste de materials)] pour un cours."""
    posts = []
    sources = [
        (classroom.courses().courseWork().list, "courseWork"),
        (classroom.courses().courseWorkMaterials().list, "courseWorkMaterial"),
        (classroom.courses().announcements().list, "announcements"),
    ]
    for method, key in sources:
        try:
            items = list_all(method, key, courseId=course_id)
        except HttpError as e:
            print(f"  ! Impossible de lire {key} : {e.reason}")
            continue
        for item in items:
            title = item.get("title") or "Annonce - " + (item.get("text") or "")[:50]
            posts.append((title, item.get("materials", [])))
    return posts


def drive_service(creds):
    # Les objets service ne sont pas thread-safe : un par thread.
    if not hasattr(_local, "drive"):
        _local.drive = build("drive", "v3", credentials=creds, cache_discovery=False)
    return _local.drive


def download_file(creds, file_id, folder):
    drive = drive_service(creds)
    meta = drive.files().get(fileId=file_id, fields="name,mimeType", supportsAllDrives=True).execute()
    name, mime = safe_name(meta["name"], 150), meta["mimeType"]

    if mime in EXPORTS:
        export_mime, ext = EXPORTS[mime]
        if not name.lower().endswith(ext):
            name += ext
        request = drive.files().export_media(fileId=file_id, mimeType=export_mime)
    elif mime.startswith("application/vnd.google-apps."):
        return f"ignoré (type non exportable) : {name}"
    else:
        request = drive.files().get_media(fileId=file_id, supportsAllDrives=True)

    target = folder / name
    if target.exists():
        return None
    folder.mkdir(parents=True, exist_ok=True)
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request, chunksize=8 * 1024 * 1024)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    tmp = target.with_suffix(target.suffix + ".part")
    tmp.write_bytes(buffer.getvalue())
    tmp.replace(target)
    return f"OK {target.relative_to(folder.parent.parent)}"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dest", type=Path, help="dossier de destination (défaut : Bureau/Classroom)")
    parser.add_argument("--cours", help="ne garder que les cours dont le nom contient ce texte")
    parser.add_argument("--archives", action="store_true", help="inclure les cours archivés")
    parser.add_argument("--threads", type=int, default=8, help="téléchargements en parallèle (défaut : 8)")
    args = parser.parse_args()

    dest = args.dest or default_desktop() / "Classroom"
    creds = get_credentials()
    classroom = build("classroom", "v1", credentials=creds, cache_discovery=False)

    states = ["ACTIVE", "ARCHIVED"] if args.archives else ["ACTIVE"]
    courses = list_all(classroom.courses().list, "courses", courseStates=states, studentId="me")
    if args.cours:
        courses = [c for c in courses if args.cours.lower() in c["name"].lower()]
    print(f"{len(courses)} cours trouvé(s). Destination : {dest}")

    jobs, links, seen = [], {}, set()
    for course in courses:
        course_dir = dest / safe_name(course["name"])
        print(f"- {course['name']}")
        for title, materials in collect_posts(classroom, course["id"]):
            post_dir = course_dir / safe_name(title, 80)
            for m in materials:
                if "driveFile" in m:
                    file_id = m["driveFile"]["driveFile"]["id"]
                    if file_id not in seen:
                        seen.add(file_id)
                        jobs.append((file_id, post_dir, m["driveFile"]["driveFile"].get("title", file_id)))
                elif "link" in m:
                    links.setdefault(course_dir, []).append(f"{title} : {m['link']['url']}")
                elif "youtubeVideo" in m:
                    links.setdefault(course_dir, []).append(
                        f"{title} : {m['youtubeVideo'].get('alternateLink', '')}"
                    )

    for course_dir, lines in links.items():
        course_dir.mkdir(parents=True, exist_ok=True)
        (course_dir / "liens.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"{len(jobs)} fichier(s) à vérifier, téléchargement...")
    new, errors = 0, 0
    with ThreadPoolExecutor(max_workers=args.threads) as pool:
        futures = {pool.submit(download_file, creds, fid, folder): title for fid, folder, title in jobs}
        for future in as_completed(futures):
            try:
                msg = future.result()
            except HttpError as e:
                errors += 1
                print(f"  ! {futures[future]} : {e.reason}")
                continue
            if msg:
                new += msg.startswith("OK")
                print(f"  {msg}")

    print(f"Terminé : {new} nouveau(x) fichier(s), {errors} erreur(s). Dossier : {dest}")


if __name__ == "__main__":
    main()
