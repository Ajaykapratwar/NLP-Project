from rank_bm25 import BM25Okapi
from backend.vector_store import DocumentStore
from backend.preprocessing import TextPreprocessor
from config import TOP_K
import numpy as np

class BM25Retriever:
    """BM25 lexical search retriever."""
    
    def __init__(self, store: DocumentStore):
        self.store = store
        self.preprocessor = TextPreprocessor()
        self.bm25 = None
        self.chunks = []
        self.metadata = []

    def build_index(self):
        self.chunks, self.metadata = self.store.get_all()
        if not self.chunks:
            self.bm25 = None
            return
            
        tokenized_corpus = [self.preprocessor.preprocess_tokens(chunk) for chunk in self.chunks]
        if tokenized_corpus:
            self.bm25 = BM25Okapi(tokenized_corpus)

    def retrieve(self, query: str, top_k: int = TOP_K):
        if self.bm25 is None or not self.chunks:
            return [], [], 0.0
            
        query_tokens = self.preprocessor.preprocess_tokens(query)
        if not query_tokens:
            return [], [], 0.0
            
        scores = self.bm25.get_scores(query_tokens)
        max_score = float(np.max(scores)) if len(scores) > 0 else 0.0
        
        top_n = min(top_k, len(self.chunks))
        top_indices = np.argsort(scores)[::-1][:top_n]
        
        top_chunks = [self.chunks[i] for i in top_indices if scores[i] > 0]
        top_metadata = [self.metadata[i] for i in top_indices if scores[i] > 0]
        
        return top_chunks, top_metadata, max_score
