import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
GROQ_MODEL = "llama-3.1-8b-instant"
TOP_K = 3
RELEVANCE_THRESHOLD = 0.3
CHUNK_SIZE = 80
CHUNK_OVERLAP = 1
STORE_PATH = "data/document_store.json"
WEB_SEARCH_MAX_RESULTS = 4
SYSTEM_PROMPT = """You are an intelligent QA assistant.
You MUST ONLY use the provided context to answer the user's query.
You MUST NOT use any of your own underlying knowledge.
If the provided context does not contain the answer, state that the information is not available in the provided context.
"""
