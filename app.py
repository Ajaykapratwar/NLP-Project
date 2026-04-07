import sys
import os
import streamlit as st

# 1. Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import GROQ_API_KEY, CHUNK_SIZE, CHUNK_OVERLAP
from backend.loader import DocumentLoader
from backend.preprocessing import TextPreprocessor
from backend.vector_store import DocumentStore
from backend.retriever import BM25Retriever
from backend.router import QueryRouter
from backend.web_search import WebSearcher
from backend.groq_llm import GroqFormatter
from frontend.ui import (
    setup_page, render_sidebar, show_doc_stats,
    init_chat_history, render_chat_history,
    get_user_query, append_message
)
from utils.helpers import save_uploaded_file, parse_urls, build_context, unique_sources

# 2. Use @st.cache_resource to initialize components
@st.cache_resource
def init_components():
    store = DocumentStore()
    
    # Clear store on server startup (once per server lifetime)
    store.clear()
    
    retriever = BM25Retriever(store)
    retriever.build_index()
    loader = DocumentLoader()
    preprocessor = TextPreprocessor()
    router = QueryRouter()
    web_searcher = WebSearcher()
    groq_formatter = GroqFormatter()
    
    return {
        "store": store,
        "retriever": retriever,
        "loader": loader,
        "preprocessor": preprocessor,
        "router": router,
        "web_searcher": web_searcher,
        "llm": groq_formatter
    }


# 3. Process documents
def process_documents(components, uploaded_files, urls):
    store = components["store"]
    loader = components["loader"]
    preprocessor = components["preprocessor"]
    retriever = components["retriever"]
    
    processed_count = 0
    
    for uploaded_file in uploaded_files:
        tmp_path = save_uploaded_file(uploaded_file)
        if tmp_path:
            text = loader.load_file(tmp_path)
            if text:
                chunks = preprocessor.chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
                if chunks:
                    store.add_documents(chunks, uploaded_file.name)
                    processed_count += 1
            try:
                os.unlink(tmp_path)
            except Exception as e:
                print(f"Error removing temp file: {e}")
                
    for url in urls:
        text = loader.load_url(url)
        if text:
            chunks = preprocessor.chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
            if chunks:
                store.add_documents(chunks, url)
                processed_count += 1
                
    if processed_count > 0:
        retriever.build_index()
        
    return processed_count

# 4. Answer query
def answer_query(components, query):
    store = components["store"]
    retriever = components["retriever"]
    router = components["router"]
    llm = components["llm"]
    web = components["web_searcher"]
    
    if store.is_empty():
        return "⚠️ Store is empty. Please upload documents or add URLs first.", "none", [], []
        
    with st.spinner("🔍 Searching documents…"):
        chunks, metadata, max_score = retriever.retrieve(query)
        
    route = router.route(max_score, chunks)
    
    if route == "document":
        context = build_context(chunks, metadata)
        with st.spinner("✍️ Formatting answer…"):
            answer = llm.format_from_documents(query, context)
            
        fallback_phrases = [
            "answer not found", "not available in",
            "not found in", "insufficient", "not provided"
        ]
        if any(p in answer.lower() for p in fallback_phrases):
            st.info("📭 Answer not found in documents. Searching the web…")
            with st.spinner("🌐 Searching the web…"):
                web_context = web.search(query)
            with st.spinner("✍️ Formatting web answer…"):
                answer = llm.format_from_web(query, web_context)
            return f"🌐 **[Web Search Result]**\n\n{answer}", "web", [], [{"source": "Web Search (Tavily)"}]

        sources = unique_sources(metadata)
        source_str = "\n\n**Sources:**\n" + "\n".join([f"- {s}" for s in sources])
        return answer + source_str, route, chunks, metadata
        
    elif route == "web":
        st.info("📭 Answer not found in documents. Searching the web…")
        with st.spinner("🌐 Searching the web…"):
            web_context = web.search(query)
            
        with st.spinner("✍️ Formatting web answer…"):
            answer = llm.format_from_web(query, web_context)
            
        return answer + "\n\n**Source:** Web Search", route, [], [{"source": "Web Search (Tavily)"}]
        
    return "Could not determine route.", "none", [], []

# 5. main()
def main():
    setup_page()
    
    if not GROQ_API_KEY and not os.environ.get("GROQ_API_KEY"):
        st.error("🚨 GROQ_API_KEY is missing! Please configure it in the .env file.")
        st.info("Check .env.example for formatting.")
        st.stop()
        
    components = init_components()
    
    uploaded_files, url_text, process_btn, clear_btn = render_sidebar()
    
    if clear_btn:
        components["store"].clear()
        components["retriever"].build_index()
        st.session_state.messages = []
        st.rerun()
        
    if process_btn:
        urls = parse_urls(url_text)
        if not uploaded_files and not urls:
            st.sidebar.warning("Please upload a file or enter a valid URL.")
        else:
            with st.sidebar:
                with st.spinner("Processing..."):
                    count = process_documents(components, uploaded_files, urls)
                    if count > 0:
                        st.success(f"Processed {count} sources successfully!")
                    else:
                        st.error("Failed to extract text from provided sources.")
                        
    store = components["store"]
    if not store.is_empty():
        show_doc_stats(store.count(), store.get_sources())
        
    init_chat_history()
    render_chat_history()
    
    query = get_user_query()
    if query:
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)
            
        answer, route, chunks, metadata = answer_query(components, query)
        
        append_message("assistant", answer, chunks=chunks, metadata=metadata)

if __name__ == "__main__":
    main()
