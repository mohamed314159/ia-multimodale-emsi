"""Étape 2 : extraction du texte, des tableaux et des images d'un PDF.

- Texte    : lecteur PyMuPDFReader de LlamaIndex (un Document par page),
             puis découpage en morceaux (chunks) avec SentenceSplitter.
- Tableaux : détection par PyMuPDF (page.find_tables), convertis en Markdown
             et transformés en nœuds LlamaIndex.
- Images   : images matricielles intégrées au PDF, plus les figures vectorielles
             (schémas dessinés) rendues en PNG.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

import fitz  # PyMuPDF
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import TextNode
from llama_index.readers.file import PyMuPDFReader

# Les métadonnées servent aux citations mais ne doivent pas polluer les embeddings
CLES_METADONNEES = ["type", "fichier", "page", "chemin"]


@dataclass
class ImageExtraite:
    chemin: Path
    page: int
    fichier: str
    description: str = ""


@dataclass
class ContenuPDF:
    pdf: Path
    textes: list[TextNode] = field(default_factory=list)
    tableaux: list[TextNode] = field(default_factory=list)
    images: list[ImageExtraite] = field(default_factory=list)

    def resume(self) -> str:
        return (f"{self.pdf.name} : {len(self.textes)} morceaux de texte, "
                f"{len(self.tableaux)} tableaux, {len(self.images)} images")


def _noeud(texte: str, type_: str, fichier: str, page: int, **extra) -> TextNode:
    return TextNode(
        text=texte,
        metadata={"type": type_, "fichier": fichier, "page": page, **extra},
        excluded_embed_metadata_keys=CLES_METADONNEES,
    )


def extraire_textes(pdf: Path, taille: int = 512, chevauchement: int = 64) -> list[TextNode]:
    """Lit le PDF avec LlamaIndex et le découpe en morceaux de ~`taille` tokens."""
    documents = PyMuPDFReader().load_data(file_path=pdf, metadata=True)
    for doc in documents:
        doc.metadata = {"type": "texte", "fichier": pdf.name, "page": int(doc.metadata.get("source", 0))}
        doc.excluded_embed_metadata_keys = CLES_METADONNEES
    decoupeur = SentenceSplitter(chunk_size=taille, chunk_overlap=chevauchement)
    return decoupeur.get_nodes_from_documents(documents)


def extraire_tableaux(pdf: Path) -> list[TextNode]:
    """Détecte les tableaux de chaque page et les convertit en Markdown."""
    noeuds = []
    with fitz.open(pdf) as doc:
        for num, page in enumerate(doc, start=1):
            try:
                tableaux = page.find_tables().tables
            except Exception:
                continue
            for i, tableau in enumerate(tableaux, start=1):
                markdown = tableau.to_markdown().strip()
                if markdown:
                    noeuds.append(_noeud(f"Tableau {i} de la page {num} :\n{markdown}", "tableau", pdf.name, num))
    return noeuds


def _nom_sur(texte: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", texte).strip("_")


def extraire_images(pdf: Path, dossier: Path, taille_min: int = 100,
                    seuil_dessins: int = 50) -> list[ImageExtraite]:
    """Enregistre en PNG les images du PDF.

    1. Images matricielles intégrées (photos, captures...).
    2. Si une page n'en contient pas mais comporte beaucoup de tracés vectoriels
       (schéma dessiné), la zone des tracés est rendue en image.
    """
    dossier.mkdir(parents=True, exist_ok=True)
    prefixe = _nom_sur(pdf.stem)
    images = []
    with fitz.open(pdf) as doc:
        for num, page in enumerate(doc, start=1):
            trouvees = 0
            for idx, info in enumerate(page.get_images(full=True), start=1):
                try:
                    pix = fitz.Pixmap(doc, info[0])
                    if pix.colorspace is None or pix.width < taille_min or pix.height < taille_min:
                        continue
                    if pix.n - pix.alpha >= 4:  # CMJN -> RVB
                        pix = fitz.Pixmap(fitz.csRGB, pix)
                    chemin = dossier / f"{prefixe}_p{num}_img{idx}.png"
                    pix.save(chemin)
                except Exception:
                    continue
                images.append(ImageExtraite(chemin, num, pdf.name))
                trouvees += 1

            if trouvees == 0:
                dessins = page.get_drawings()
                if len(dessins) >= seuil_dessins:
                    zone = fitz.Rect(dessins[0]["rect"])
                    for d in dessins[1:]:
                        zone |= d["rect"]
                    zone &= page.rect
                    if zone.width >= taille_min and zone.height >= taille_min:
                        chemin = dossier / f"{prefixe}_p{num}_figure.png"
                        page.get_pixmap(clip=zone, dpi=150).save(chemin)
                        images.append(ImageExtraite(chemin, num, pdf.name))
    return images


def extraire_contenu(pdf: Path, dossier_images: Path) -> ContenuPDF:
    """Extrait d'un coup le texte, les tableaux et les images du PDF."""
    pdf = Path(pdf)
    return ContenuPDF(
        pdf=pdf,
        textes=extraire_textes(pdf),
        tableaux=extraire_tableaux(pdf),
        images=extraire_images(pdf, dossier_images),
    )


def noeuds_descriptions(images: list[ImageExtraite]) -> list[TextNode]:
    """Transforme les descriptions d'images en nœuds texte interrogeables (étape 3)."""
    return [
        _noeud(f"Description de la figure de la page {img.page} : {img.description}",
               "image", img.fichier, img.page, chemin=str(img.chemin))
        for img in images if img.description
    ]
