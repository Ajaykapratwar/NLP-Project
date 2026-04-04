import os
import tempfile
import re

def save_uploaded_file(uploaded_file) -> str:
    """Save an uploaded file to a temporary location and return the path."""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{uploaded_file.name}") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            return tmp_file.name
    except Exception as e:
        print(f"Error saving uploaded file: {e}")
        return ""

def parse_urls(url_text: str) -> list[str]:
    """Extract valid http/https URLs from a newline-separated string."""
    urls = []
    for line in url_text.splitlines():
        line = line.strip()
        if re.match(r'^https?://', line):
            urls.append(line)
    return urls

def build_context(chunks: list[str], metadata: list[dict]) -> str:
    """Format chunks into a single context string with sources."""
    context_parts = []
    for chunk, meta in zip(chunks, metadata):
        source = meta.get("source", "Unknown")
        context_parts.append(f"[Source: {source}]\n{chunk}\n")
    full_context = "\n".join(context_parts)
    if len(full_context) > 2500:
        return full_context[:2500] + "\n...[context truncated for length]"
    return full_context

def unique_sources(metadata: list[dict]) -> list[str]:
    """Get a de-duplicated list of sources from metadata."""
    sources = set()
    for meta in metadata:
        if "source" in meta:
            sources.add(meta["source"])
    return list(sources)

def truncate(text: str, max_chars: int = 3000) -> str:
    """Truncate text to a maximum number of characters."""
    if len(text) > max_chars:
        return text[:max_chars] + "..."
    return text
