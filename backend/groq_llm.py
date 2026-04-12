from groq import Groq
from config import GROQ_MODEL, SYSTEM_PROMPT

class GroqFormatter:
    """Formats answers using Groq LLM."""
    
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("api_key is required.")
        self.api_key = api_key
        # We instantiate the client per request or maintain it if it's the same
        self.client = Groq(api_key=self.api_key)

    def _generate(self, user_prompt: str) -> str:
        try:
            completion = self.client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Error generating response: {e}"

    def format_from_documents(self, query: str, context: str) -> str:
        prompt = f"Context from documents:\n{context}\n\nUser Query: {query}"
        return self._generate(prompt)

    def format_from_web(self, query: str, web_context: str) -> str:
        prompt = f"Context from web search:\n{web_context}\n\nUser Query: {query}"
        return self._generate(prompt)
    
    def generate_sql(self, query: str, schema: str) -> str:
        prompt = f"You are an expert SQL generator. Respond ONLY with the valid SQL query, nothing else, no markdown block.\nDatabase Schema:\n{schema}\n\nUser Question: {query}"
        return self._generate(prompt)
