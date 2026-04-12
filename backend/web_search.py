import os
import warnings
from config import WEB_SEARCH_MAX_RESULTS

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from langchain_community.tools.tavily_search import TavilySearchResults

class WebSearcher:
    """Searches the web using Tavily Search."""
    
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("api_key is required for Tavily.")
        os.environ["TAVILY_API_KEY"] = api_key
            
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            # Will pick up the newly set os.environ["TAVILY_API_KEY"]
            self.tavily_tool = TavilySearchResults(max_results=WEB_SEARCH_MAX_RESULTS)

    def search(self, query: str) -> str:
        try:
            results = self.tavily_tool.invoke({"query": query})
            
            if not results:
                return "No web results found."
                
            formatted_results = []
            for res in results:
                # Tavily typically returns a list of dicts with 'title', 'url', and 'content'
                title = res.get('title', 'Unknown Title')
                url = res.get('url', 'Unknown URL')
                content = res.get('content', '')
                
                formatted_results.append(f"Title: {title}\nURL: {url}\nContent: {content}\n")
                
            return "\n---\n".join(formatted_results)
        except Exception as e:
            return f"Error during web search: {e}"
