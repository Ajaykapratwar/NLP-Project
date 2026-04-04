import streamlit as st

def setup_page():
    st.set_page_config(
        page_title="Intelligent QA System",
        page_icon="📚",
        layout="wide"
    )
    st.title("📚 Multi-Domain Intelligent QA System")
    st.subheader("Powered by NLP and RAG")

def render_sidebar():
    with st.sidebar:
        st.header("📄 Document Upload")
        uploaded_files = st.file_uploader(
            "Upload PDF, TXT, or CSV files",
            type=["pdf", "txt", "csv"],
            accept_multiple_files=True
        )
        
        st.header("🌐 Web Links")
        url_text = st.text_area(
            "Enter URLs (one per line)",
            height=100,
            placeholder="https://example.com"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            process_btn = st.button("Process", type="primary", use_container_width=True)
        with col2:
            clear_btn = st.button("Clear", type="secondary", use_container_width=True)
            
        with st.expander("💡 How to use"):
            st.markdown("""
            1. Upload documents or paste URLs
            2. Click **Process** to index
            3. Ask questions in the chat!
            
            The system uses **BM25 lexical search** to find relevant chunks.
            If the confidence is low, it falls back to a **Web Search**.
            """)
            
        return uploaded_files, url_text, process_btn, clear_btn

def show_doc_stats(chunk_count: int, sources: list[str]):
    with st.sidebar:
        if chunk_count > 0:
            st.success(f"✅ Indexed {chunk_count} chunks")
            with st.expander("📑 Indexed Sources", expanded=False):
                for src in sources:
                    st.markdown(f"- {src}")

def init_chat_history():
    if "messages" not in st.session_state:
        st.session_state.messages = []

def render_chat_history():
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "chunks" in msg and msg["chunks"]:
                with st.expander("Show Retrieved Evidence", expanded=False):
                    metadata_list = msg.get("metadata") or []
                    for chunk, meta in zip(msg["chunks"], metadata_list + [{}] * (len(msg["chunks"]) - len(metadata_list))):
                        source = meta.get("source", "Unknown") if meta else "Unknown"
                        st.markdown(f"**Source**: {source}")
                        st.info(chunk)

def get_user_query() -> str:
    return st.chat_input("Ask a question about your documents…")

def append_message(role: str, content: str, chunks: list = None, metadata: list = None):
    msg_data = {"role": role, "content": content}
    if chunks:
        msg_data["chunks"] = chunks
        msg_data["metadata"] = metadata or []
        
    st.session_state.messages.append(msg_data)
    
    with st.chat_message(role):
        st.markdown(content)
        if chunks:
            with st.expander("Show Retrieved Evidence", expanded=False):
                metadata_list = metadata or []
                for chunk, meta in zip(chunks, metadata_list + [{}] * (len(chunks) - len(metadata_list))):
                    source = meta.get("source", "Unknown") if meta else "Unknown"
                    st.markdown(f"**Source**: {source}")
                    st.info(chunk)
