"""Serveur MCP du SAV : publie le tool distant `rag_multimodal` (transport streamable-http).

Derrière ce tool, un agent RAG multimodal (sav/rag_multimodal.py) recherche des passages et des figures
dans les manuels, puis produit une réponse sourcée.

Lancement, depuis le dossier de l'AP5 :
    uv run python sav/serveur_mcp_rag.py
Point d'accès MCP : http://127.0.0.1:24001/mcp
"""

import os
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rag_multimodal import RAGMultimodal  # noqa: E402

PORT = int(os.getenv("MCP_SAV_PORT", "24001"))
mcp = FastMCP(name="sav-rag-multimodal", host=os.getenv("MCP_HOST", "127.0.0.1"), port=PORT)
rag = RAGMultimodal()


@mcp.tool()
def rag_multimodal(question: str, image_ref: str | None = None) -> dict:
    """Assistance documentaire du SAV (imprimante PX-200, scanner SC-10) : explique un voyant, un pictogramme,
    un code d'erreur ou une procédure de dépannage à partir des manuels (passages ET figures).
    image_ref : référence facultative d'une photo envoyée par le client (ex. « img_px200_01 »), analysée par le LLM vision.
    Renvoie la réponse rédigée et la liste des sources utilisées."""
    return rag.repondre(question, image_ref)


if __name__ == "__main__":
    print(f"Serveur MCP SAV sur http://127.0.0.1:{PORT}/mcp | {rag.index.index.ntotal} éléments indexés", flush=True)
    mcp.run(transport="streamable-http")
