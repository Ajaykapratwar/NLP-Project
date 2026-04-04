import pandas as pd
import pdfplumber
import requests
from bs4 import BeautifulSoup
import os

class DocumentLoader:
    """Loads text from various sources."""
    
    @staticmethod
    def load_pdf(path: str) -> str:
        text = []
        try:
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text.append(page_text)
            return "\n".join(text)
        except Exception as e:
            print(f"Error loading PDF {path}: {e}")
            return ""

    @staticmethod
    def load_txt(path: str) -> str:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"Error loading TXT {path}: {e}")
            return ""

    @staticmethod
    def load_csv(path: str) -> str:
        try:
            df = pd.read_csv(path)
            rows = []
            for _, row in df.iterrows():
                row_str = ", ".join([f"{col}: {val}" for col, val in row.items()])
                rows.append(row_str)
            return "\n".join(rows)
        except Exception as e:
            print(f"Error loading CSV {path}: {e}")
            return ""

    @staticmethod
    def load_url(url: str) -> str:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            for script_or_style in soup(["script", "style", "nav", "footer", "header"]):
                script_or_style.decompose()
            text = soup.get_text(separator=" ")
            return text
        except Exception as e:
            print(f"Error loading URL {url}: {e}")
            return ""

    @staticmethod
    def load_file(path: str) -> str:
        ext = os.path.splitext(path)[1].lower()
        if ext == '.pdf':
            return DocumentLoader.load_pdf(path)
        elif ext == '.txt':
            return DocumentLoader.load_txt(path)
        elif ext == '.csv':
            return DocumentLoader.load_csv(path)
        else:
            print(f"Unsupported file extension: {ext}")
            return ""
