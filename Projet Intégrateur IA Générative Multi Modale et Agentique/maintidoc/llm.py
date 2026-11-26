"""Choix du modèle de chat : Azure OpenAI (par défaut) ou Qwen via Ollama (open source).

Le fournisseur se règle dans .env avec LLM_PROVIDER=azure ou LLM_PROVIDER=ollama.
Le même modèle sert à la génération (étape 4), à l'agent (étape 6) et, comme
gpt-4.1-mini accepte les images, à la description des figures (étape 3).
"""

from langchain_core.language_models import BaseChatModel
from langchain_ollama import ChatOllama
from langchain_openai import AzureChatOpenAI

from . import config


def chat_model(vision: bool = False, temperature: float = 0) -> BaseChatModel:
    if config.LLM_PROVIDER == "azure":
        return AzureChatOpenAI(
            azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
            api_key=config.AZURE_OPENAI_API_KEY,
            azure_deployment=config.AZURE_OPENAI_DEPLOYMENT,
            api_version=config.AZURE_OPENAI_API_VERSION,
            temperature=temperature,
            timeout=60,
        )
    return ChatOllama(
        model=config.VISION_MODEL if vision else config.LLM_MODEL,
        base_url=config.OLLAMA_BASE_URL,
        temperature=temperature,
    )


def nom_modele(vision: bool = False) -> str:
    """Nom lisible du modèle utilisé (affichage)."""
    if config.LLM_PROVIDER == "azure":
        return f"Azure OpenAI {config.AZURE_OPENAI_DEPLOYMENT}"
    return f"Ollama {config.VISION_MODEL if vision else config.LLM_MODEL}"
