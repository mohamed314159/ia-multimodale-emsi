import os
from dotenv import load_dotenv

load_dotenv(override=True)

OK, KO, AV = "[OK]  ", "[ERREUR]", "[A FAIRE]"

# 1. Variables présentes
requises = ["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_DEPLOYMENT",
            "AZURE_OPENAI_API_VERSION", "TAVILY_API_KEY"]
print("== Variables du .env")
manquantes = [v for v in requises if not os.getenv(v)]
for v in requises:
    print(f"{KO if v in manquantes else OK} {v}")
if manquantes:
    raise SystemExit("\nRemplissez les variables manquantes puis relancez.")

azure = dict(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
)

# 2. Modèle de chat Azure
print("\n== Azure OpenAI (chat)")
try:
    from langchain_openai import AzureChatOpenAI
    llm = AzureChatOpenAI(azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"), **azure)
    print(f"{OK} réponse : {llm.invoke('Réponds juste: bonjour').content!r}")
except Exception as e:
    print(f"{KO} {type(e).__name__}: {str(e)[:200]}")

# 3. Embeddings Azure (nécessaires pour les parties RAG)
print("\n== Azure OpenAI (embeddings)")
emb = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
if not emb:
    print(f"{AV} AZURE_OPENAI_EMBEDDING_DEPLOYMENT absente (requise pour les RAG des parties A, B, D)")
else:
    try:
        from langchain_openai import AzureOpenAIEmbeddings
        vec = AzureOpenAIEmbeddings(azure_deployment=emb, **azure).embed_query("test")
        print(f"{OK} vecteur de dimension {len(vec)}")
    except Exception as e:
        print(f"{KO} {type(e).__name__}: {str(e)[:200]}")

# 4. Tavily
print("\n== Tavily")
try:
    from langchain_tavily import TavilySearch
    res = TavilySearch(max_results=1).invoke({"query": "EMSI Maroc"})
    print(f"{OK} {len(res.get('results', []))} résultat(s) reçu(s)")
except Exception as e:
    print(f"{KO} {type(e).__name__}: {str(e)[:200]}")