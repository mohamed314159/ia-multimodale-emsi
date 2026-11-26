"""Génère les données du cas de synthèse (partie D) : figures des manuels et photo envoyée par le client.

Les manuels (texte) et le registre des garanties sont des fichiers écrits à la main dans sav/donnees/.
Ce script dessine les images avec Pillow pour que le jeu de données soit reproductible :
    uv run python sav/generer_donnees.py
"""

import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

DOSSIER = Path(__file__).resolve().parent / "donnees"
FIGURES = DOSSIER / "figures"
CLIENTS = DOSSIER / "images_clients"

ORANGE, VERT, BLEU, ROUGE = (245, 140, 20), (40, 170, 70), (40, 110, 220), (210, 40, 40)
GRIS_FONCE, GRIS = (60, 60, 65), (200, 200, 205)


def police(taille: int, gras: bool = False):
    for nom in (["arialbd.ttf", "DejaVuSans-Bold.ttf"] if gras else ["arial.ttf", "DejaVuSans.ttf"]):
        try:
            return ImageFont.truetype(nom, taille)
        except OSError:
            continue
    return ImageFont.load_default()


def goutte(d: ImageDraw.ImageDraw, cx: int, cy: int, r: int, couleur, contour=(0, 0, 0)):
    """Pictogramme « goutte d'encre » : un cercle surmonté d'une pointe."""
    d.polygon([(cx, cy - int(2.2 * r)), (cx - int(0.87 * r), cy - r // 2), (cx + int(0.87 * r), cy - r // 2)],
              fill=couleur, outline=contour)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=couleur, outline=contour, width=3)


def point_exclamation(d, cx, cy, h, couleur=(255, 255, 255)):
    d.rectangle([cx - h // 10, cy - h // 2, cx + h // 10, cy + h // 6], fill=couleur)
    d.ellipse([cx - h // 9, cy + h // 3 - h // 9, cx + h // 9, cy + h // 3 + h // 9], fill=couleur)


def voyant(d, cx, cy, couleur, allume=True, halo=False):
    if halo:
        for i in range(6, 0, -1):
            c = tuple(min(255, int(v + (255 - v) * i / 8)) for v in couleur)
            d.ellipse([cx - 14 - 3 * i, cy - 14 - 3 * i, cx + 14 + 3 * i, cy + 14 + 3 * i], fill=c)
    d.ellipse([cx - 14, cy - 14, cx + 14, cy + 14], fill=couleur if allume else GRIS, outline=GRIS_FONCE, width=2)


def cadre_figure(titre: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (800, 500), "white")
    d = ImageDraw.Draw(image)
    d.rectangle([0, 0, 799, 499], outline=GRIS_FONCE, width=2)
    d.text((20, 455), titre, fill=GRIS_FONCE, font=police(22, gras=True))
    return image, d


def figure_panneau():
    image, d = cadre_figure("Figure PX200-1 : panneau de commande de l'imprimante PX-200")
    d.rounded_rectangle([60, 60, 740, 400], radius=25, fill=(235, 235, 238), outline=GRIS_FONCE, width=3)
    d.rectangle([110, 110, 420, 300], fill=(25, 45, 60), outline=GRIS_FONCE, width=3)       # écran
    d.text((130, 125), "PX-200  Prête", fill="white", font=police(30))
    legendes = [("Alimentation", VERT), ("Encre", ORANGE), ("Wi-Fi", BLEU), ("Erreur papier", ROUGE)]
    for i, (nom, couleur) in enumerate(legendes):
        y = 120 + i * 62
        voyant(d, 500, y + 14, couleur)
        d.text((530, y), nom, fill=GRIS_FONCE, font=police(26))
    for i, symbole in enumerate(["ON", "OK", "STOP"]):
        d.rounded_rectangle([120 + i * 105, 320, 210 + i * 105, 375], radius=12, fill="white", outline=GRIS_FONCE, width=3)
        d.text((140 + i * 105, 332), symbole, fill=GRIS_FONCE, font=police(24, gras=True))
    image.save(FIGURES / "fig_px200_panneau.png")


def figure_encre():
    image, d = cadre_figure("Figure PX200-2 : pictogramme « niveau d'encre » et voyant Encre")
    goutte(d, 230, 250, 90, ORANGE)
    point_exclamation(d, 230, 255, 100)
    d.text((80, 50), "Écran", fill=GRIS_FONCE, font=police(26, gras=True))
    voyant(d, 520, 160, ORANGE, halo=True)
    d.text((560, 145), "clignotant", fill=GRIS_FONCE, font=police(26))
    d.text((480, 230), "= encre faible (< 10 %)", fill=GRIS_FONCE, font=police(26))
    voyant(d, 520, 320, ORANGE)
    d.text((560, 305), "fixe", fill=GRIS_FONCE, font=police(26))
    d.text((480, 365), "= cartouche vide", fill=GRIS_FONCE, font=police(26))
    image.save(FIGURES / "fig_px200_picto_encre.png")


def figure_bourrage():
    image, d = cadre_figure("Figure PX200-3 : pictogramme « bourrage papier » et voyant Erreur papier")
    d.polygon([(150, 90), (330, 90), (330, 330), (150, 330)], fill="white", outline=GRIS_FONCE)
    for i in range(5):
        d.line([(170, 120 + 40 * i), (310, 120 + 40 * i)], fill=GRIS, width=6)
    d.line([(130, 380), (190, 340), (240, 390), (290, 340), (350, 380)], fill=ROUGE, width=10)
    d.line([(390, 110), (470, 190)], fill=ROUGE, width=14)
    d.line([(470, 110), (390, 190)], fill=ROUGE, width=14)
    voyant(d, 560, 300, ROUGE, halo=True)
    d.text((600, 285), "rouge", fill=GRIS_FONCE, font=police(26))
    image.save(FIGURES / "fig_px200_picto_bourrage.png")


def figure_wifi():
    image, d = cadre_figure("Figure PX200-4 : pictogramme « Wi-Fi déconnecté » et voyant Wi-Fi")
    cx, cy = 260, 330
    for r in (60, 120, 180):
        d.arc([cx - r, cy - r, cx + r, cy + r], start=225, end=315, fill=BLEU, width=18)
    d.ellipse([cx - 18, cy - 18, cx + 18, cy + 18], fill=BLEU)
    d.line([(120, 110), (400, 380)], fill=ROUGE, width=16)
    voyant(d, 560, 250, BLEU, allume=False)
    d.text((600, 235), "éteint", fill=GRIS_FONCE, font=police(26))
    image.save(FIGURES / "fig_px200_picto_wifi.png")


def figure_scanner():
    image, d = cadre_figure("Figure SC10-1 : voyant d'état du scanner SC-10")
    d.rounded_rectangle([80, 120, 720, 340], radius=20, fill=(235, 235, 238), outline=GRIS_FONCE, width=3)
    d.rectangle([110, 150, 560, 310], fill=(170, 200, 215), outline=GRIS_FONCE, width=2)  # vitre
    voyant(d, 640, 230, ROUGE, halo=True)
    d.text((585, 280), "rouge clignotant", fill=GRIS_FONCE, font=police(20))
    image.save(FIGURES / "fig_sc10_voyant.png")


def photo_client_px200_01():
    """Photo prise par le client : écran de la PX-200, pictogramme goutte + code E-04, voyant Encre orange qui clignote."""
    random.seed(42)
    photo = Image.new("RGB", (1000, 750), (92, 84, 76))                         # bureau en arrière-plan
    d = ImageDraw.Draw(photo)
    d.polygon([(90, 120), (930, 70), (960, 650), (60, 690)], fill=(214, 214, 218))  # façade vue de biais
    d.polygon([(170, 190), (620, 165), (630, 470), (160, 495)], fill=(22, 40, 54))   # écran
    goutte(d, 330, 360, 70, ORANGE, contour=(30, 30, 30))
    point_exclamation(d, 330, 365, 80)
    d.text((440, 300), "E-04", fill="white", font=police(64, gras=True))
    d.text((200, 205), "PX-200", fill=(180, 200, 210), font=police(30))
    voyant(d, 760, 200, VERT)                                                    # Alimentation
    voyant(d, 760, 290, ORANGE, halo=True)                                       # Encre (clignote)
    voyant(d, 760, 380, BLEU)                                                    # Wi-Fi
    voyant(d, 760, 470, GRIS, allume=False)                                      # Erreur papier
    for _ in range(9000):                                                        # bruit du capteur
        x, y = random.randrange(1000), random.randrange(750)
        v = random.randint(-35, 35)
        r, g, b = photo.getpixel((x, y))
        photo.putpixel((x, y), (max(0, min(255, r + v)), max(0, min(255, g + v)), max(0, min(255, b + v))))
    photo = photo.rotate(-4, resample=Image.BICUBIC, fillcolor=(92, 84, 76)).filter(ImageFilter.GaussianBlur(1.6))
    photo.save(CLIENTS / "img_px200_01.png")


if __name__ == "__main__":
    FIGURES.mkdir(parents=True, exist_ok=True)
    CLIENTS.mkdir(parents=True, exist_ok=True)
    for fonction in [figure_panneau, figure_encre, figure_bourrage, figure_wifi, figure_scanner, photo_client_px200_01]:
        fonction()
    print("Images générées :", sorted(p.name for p in FIGURES.glob("*.png")) + ["img_px200_01.png"])
