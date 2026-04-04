from groq import Groq
from config import GROQ_MODEL, SYSTEM_PROMPT, GROQ_API_KEY
import os

class GroqFormatter:
    """Formats answers using Groq LLM."""
    
    def __init__(self):
        key = GROQ_API_KEY or os.environ.get("GROQ_API_KEY")
        if not key:
            raise ValueError("GROQ_API_KEY is not set.")
        self.client = Groq(api_key=key)

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
