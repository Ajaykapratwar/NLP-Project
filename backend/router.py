from config import RELEVANCE_THRESHOLD

class QueryRouter:
    """Routes query based on BM25 max score."""
    
    def route(self, max_score: float, chunks: list[str]) -> str:
        if not chunks:
            return "web"
        if max_score < RELEVANCE_THRESHOLD:
            return "web"
        return "document"

    def explain(self, max_score: float, chunks: list[str]) -> str:
        route = self.route(max_score, chunks)
        return f"Route: {route} (Max Score: {max_score:.4f}, Threshold: {RELEVANCE_THRESHOLD})"
