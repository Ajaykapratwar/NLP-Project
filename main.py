import os
from fastapi import FastAPI, UploadFile, File, Form, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import shutil

from config import CHUNK_SIZE, CHUNK_OVERLAP
from backend.loader import DocumentLoader
from backend.preprocessing import TextPreprocessor
from backend.vector_store import DocumentStore
from backend.retriever import BM25Retriever
from backend.router import QueryRouter
from backend.web_search import WebSearcher
from backend.groq_llm import GroqFormatter
from backend.nlp_to_sql import NLPToSQL
from utils.helpers import parse_urls, build_context, unique_sources

app = FastAPI(title="Multi-Domain NLP AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Store
store = DocumentStore()
retriever = BM25Retriever(store)
loader = DocumentLoader()
preprocessor = TextPreprocessor()
router = QueryRouter()

class ChatRequest(BaseModel):
    query: str

class UrlUploadRequest(BaseModel):
    urls: str

class NL2SQLRequest(BaseModel):
    query: str

def get_keys(x_groq_api_key: str, x_tavily_api_key: str):
    if not x_groq_api_key:
        raise HTTPException(status_code=401, detail="Groq API Key is required")
    if not x_tavily_api_key:
        raise HTTPException(status_code=401, detail="Tavily API Key is required")
    return x_groq_api_key, x_tavily_api_key

@app.post("/api/upload_files")
async def upload_files_endpoint(files: List[UploadFile] = File(...)):
    processed_count = 0
    os.makedirs("tmp", exist_ok=True)
    for file in files:
        tmp_path = f"tmp/{file.filename}"
        with open(tmp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        text = loader.load_file(tmp_path)
        if text:
            chunks = preprocessor.chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
            if chunks:
                store.add_documents(chunks, file.filename)
                processed_count += 1
        try:
            os.unlink(tmp_path)
        except:
            pass
            
    if processed_count > 0:
        retriever.build_index()
    return {"message": f"Processed {processed_count} files successfully."}

@app.post("/api/upload_urls")
async def upload_urls_endpoint(req: UrlUploadRequest):
    urls = parse_urls(req.urls)
    processed_count = 0
    for url in urls:
        text = loader.load_url(url)
        if text:
            chunks = preprocessor.chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
            if chunks:
                store.add_documents(chunks, url)
                processed_count += 1
    if processed_count > 0:
        retriever.build_index()
    return {"message": f"Processed {processed_count} URLs successfully."}

@app.post("/api/chat")
async def chat_endpoint(
    req: ChatRequest, 
    x_groq_api_key: str = Header(None), 
    x_tavily_api_key: str = Header(None)
):
    groq_key, tavily_key = get_keys(x_groq_api_key, x_tavily_api_key)
    llm = GroqFormatter(api_key=groq_key)
    web = WebSearcher(api_key=tavily_key)
    
    if store.is_empty():
        # Fallback to web search if store is empty
        web_context = web.search(req.query)
        answer = llm.format_from_web(req.query, web_context)
        return {"answer": answer, "route": "web", "sources": [{"source": "Web Search (Tavily)"}]}

    chunks, metadata, max_score = retriever.retrieve(req.query)
    route = router.route(max_score, chunks)
    
    if route == "document":
        context = build_context(chunks, metadata)
        answer = llm.format_from_documents(req.query, context)
        fallback_phrases = ["answer not found", "not available in", "not found in", "insufficient", "not provided"]
        if any(p in answer.lower() for p in fallback_phrases):
            web_context = web.search(req.query)
            answer = llm.format_from_web(req.query, web_context)
            return {"answer": answer, "route": "web", "sources": [{"source": "Web Search (Tavily)"}]}
            
        sources = unique_sources(metadata)
        return {"answer": answer, "route": "document", "sources": [{"source": s} for s in sources]}
        
    elif route == "web":
        web_context = web.search(req.query)
        answer = llm.format_from_web(req.query, web_context)
        return {"answer": answer, "route": "web", "sources": [{"source": "Web Search (Tavily)"}]}
    
    return {"answer": "Could not determine route.", "route": "none"}

@app.post("/api/upload_sql_csv")
async def upload_sql_csv(
    file: UploadFile = File(...), 
    x_groq_api_key: str = Header(None)
):
    if not x_groq_api_key:
        raise HTTPException(status_code=401, detail="Groq API Key is required")
        
    os.makedirs("tmp", exist_ok=True)
    tmp_path = f"tmp/{file.filename}"
    with open(tmp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # We maintain a global NLPToSQL state per worker just for demo/simplicity
    global nlp_sql_instance
    nlp_sql_instance = NLPToSQL(api_key=x_groq_api_key)
    res = nlp_sql_instance.load_csv(tmp_path)
    os.unlink(tmp_path)
    return {"message": res}

@app.post("/api/nl2sql")
async def nl2sql_endpoint(
    req: NL2SQLRequest,
    x_groq_api_key: str = Header(None)
):
    if not x_groq_api_key:
        raise HTTPException(status_code=401, detail="Groq API Key is required")
    # Quick check
    if 'nlp_sql_instance' not in globals():
        return {"error": "Please upload a CSV first in the NLP2SQL tab."}
    
    # Re-inject the token just in case
    nlp_sql_instance.llm.api_key = x_groq_api_key
    res = nlp_sql_instance.query(req.query)
    return res
    

os.makedirs("frontend/public", exist_ok=True)
app.mount("/", StaticFiles(directory="frontend/public", html=True), name="static")
