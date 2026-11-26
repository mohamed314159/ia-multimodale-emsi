"""Agent LangChain en ligne de commande, client du serveur MCP de la partie C (transport streamable-http).

Lancement, depuis le dossier de l'AP5 (le serveur doit tourner dans un autre terminal) :
    uv run python mcp_demo/serveur_mcp.py
    uv run python mcp_demo/agent_mcp.py
Tapez « exit » pour quitter.
"""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import AzureChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

client_mcp = MultiServerMCPClient({
    "mcp_server": {"transport": "streamable_http", "url": os.getenv("MCP_URL", "http://127.0.0.1:24000/mcp")},
})


async def main():
    outils = await client_mcp.get_tools()
    print("Tools découverts sur le serveur MCP :", [o.name for o in outils])
    llm = AzureChatOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        temperature=0,
    )
    agent = create_agent(
        model=llm,
        tools=outils,
        system_prompt="Réponds en français en utilisant les tools fournis. Cite les URL des sources web.",
        checkpointer=InMemorySaver(),
    )
    config = {"configurable": {"thread_id": "terminal"}}
    while True:
        question = input("\nQuestion : ").strip()
        if question.lower() in {"exit", "quit"}:
            break
        if question:
            reponse = await agent.ainvoke({"messages": [HumanMessage(question)]}, config=config)
            print("Agent :", reponse["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())
