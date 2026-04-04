import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

class TextPreprocessor:
    """Preprocesses text for BM25 retrieval."""
    
    def __init__(self):
        self._download_nltk_data()
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words("english"))

    def _download_nltk_data(self):
        for pkg in ["punkt", "punkt_tab", "stopwords", "wordnet", "omw-1.4"]:
            try:
                nltk.download(pkg, quiet=True)
            except Exception as e:
                print(f"Error downloading NLTK package {pkg}: {e}")

    def clean(self, text: str) -> str:
        """Remove noise and collapse whitespace."""
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r"[^\x20-\x7E₹€£¥]", " ", text)
        return text.strip()

    def tokenize(self, text: str) -> list[str]:
        """Tokenize to lowercase words."""
        try:
            return word_tokenize(text.lower())
        except Exception as e:
            print(f"Error tokenizing text: {e}")
            return text.lower().split()

    def remove_stopwords(self, tokens: list[str]) -> list[str]:
        return [t for t in tokens if t not in self.stop_words and (t.isalnum() or any(c.isdigit() or c in '₹€£¥' for c in t))]

    def lemmatize(self, tokens: list[str]) -> list[str]:
        return [self.lemmatizer.lemmatize(t) for t in tokens]

    def preprocess_tokens(self, text: str) -> list[str]:
        """Full pipeline returning list of optimized tokens."""
        text = self.clean(text)
        tokens = self.tokenize(text)
        tokens = self.remove_stopwords(tokens)
        tokens = self.lemmatize(tokens)
        return tokens

    def chunk_text(self, text: str, chunk_size: int = 150, overlap: int = 2) -> list[str]:
        """Fast overlapping chunks using Langchain's RecursiveCharacterTextSplitter."""
        try:
            from langchain_text_splitters import RecursiveCharacterTextSplitter
            # Approximate characters (assume avg 5 chars per word)
            char_chunk_size = chunk_size * 5
            char_overlap = overlap * 25
            
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=char_chunk_size,
                chunk_overlap=char_overlap,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
            return splitter.split_text(text)
        except ImportError:
            # Fallback if langchain isn't installed
            sentences = text.split(". ")
            chunks = []
            
            # Simplified fallback chunker
            current_chunk = []
            current_length = 0
            for sentence in sentences:
                sentence_words = sentence.split()
                sentence_len = len(sentence_words)
                if current_length + sentence_len <= chunk_size:
                    current_chunk.append(sentence)
                    current_length += sentence_len
                else:
                    if current_chunk:
                        chunks.append(" ".join(current_chunk))
                    current_chunk = [sentence]
                    current_length = sentence_len
            if current_chunk:
                chunks.append(" ".join(current_chunk))
            return chunks
