"""Serveur MCP de la partie C : expose deux tools via le transport streamable-http.

Lancement, depuis le dossier de l'AP5 :
    uv run python mcp_demo/serveur_mcp.py
Point d'accès MCP : http://127.0.0.1:24000/mcp

Pour N8N lancé dans Docker, le serveur doit écouter sur toutes les interfaces :
    $env:MCP_HOST="0.0.0.0"; uv run python mcp_demo/serveur_mcp.py
puis utiliser l'URL http://host.docker.internal:24000/mcp dans N8N.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_tavily import TavilySearch
from mcp.server.fastmcp import FastMCP

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

HOTE = os.getenv("MCP_HOST", "127.0.0.1")
PORT = int(os.getenv("MCP_PORT", "24000"))

mcp = FastMCP(name="mcp-server-ap5", host=HOTE, port=PORT)
recherche_web = TavilySearch(max_results=3)

EMPLOYES = {
    "hassan": {"nom": "Hassan", "poste": "Data Scientist", "salaire": 23000, "anciennete": 12},
    "salma": {"nom": "Salma", "poste": "Ingénieure MLOps", "salaire": 19500, "anciennete": 4},
    "yassine": {"nom": "Yassine", "poste": "Chef de projet IA", "salaire": 27000, "anciennete": 15},
}


@mcp.tool()
def get_employee_infos(name: str) -> dict:
    """Donne les informations RH d'un employé de l'entreprise : poste, salaire mensuel en MAD et ancienneté en années."""
    return EMPLOYES.get(name.strip().lower(), {"erreur": f"Aucun employé nommé {name}"})


@mcp.tool()
def search(query: str) -> dict:
    """Recherche des informations récentes sur le web (Tavily). Renvoie les 3 meilleurs résultats avec titre, URL et extrait."""
    resultats = recherche_web.invoke({"query": query})
    return {"query": query,
            "results": [{"title": r["title"], "url": r["url"], "content": r["content"][:500]}
                        for r in resultats.get("results", [])]}


if __name__ == "__main__":
    print(f"Serveur MCP sur http://{HOTE}:{PORT}/mcp", flush=True)
    mcp.run(transport="streamable-http")
