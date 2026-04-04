import json
import os
from config import STORE_PATH

class DocumentStore:
    """DocumentStore backed by a JSON file (Text-only for BM25)."""
    
    def __init__(self):
        self.store_path = STORE_PATH
        self.data = {"chunks": [], "metadata": []}
        self._load()

    def add_documents(self, chunks: list[str], source: str):
        self.data["chunks"].extend(chunks)
        self.data["metadata"].extend([{"source": source} for _ in chunks])
        self._save()

    def get_all(self):
        return self.data["chunks"], self.data["metadata"]

    def clear(self):
        self.data = {"chunks": [], "metadata": []}
        self._save()

    def is_empty(self) -> bool:
        return len(self.data["chunks"]) == 0

    def count(self) -> int:
        return len(self.data["chunks"])

    def get_sources(self) -> list[str]:
        sources = set()
        for meta in self.data["metadata"]:
            if "source" in meta:
                sources.add(meta["source"])
        return list(sources)

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self.store_path), exist_ok=True)
            with open(self.store_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving to {self.store_path}: {e}")

    def _load(self):
        if not os.path.exists(self.store_path):
            return
        try:
            with open(self.store_path, "r", encoding="utf-8") as f:
                loaded_data = json.load(f)
                if "chunks" in loaded_data and "metadata" in loaded_data:
                    self.data = loaded_data
                else:
                    print("Invalid JSON format in document store.")
        except Exception as e:
            print(f"Error loading {self.store_path}: {e}")
