from pathlib import Path
from uuid import uuid4

import chromadb
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from backend.app.config import settings


class ContextStore:
    def __init__(self, directory: Path) -> None:
        self.client = chromadb.PersistentClient(path=str(directory))
        self.collection = self.client.get_or_create_collection("meeting_context_gemini_embeddings")
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=settings.google_embedding_model,
            google_api_key=settings.google_api_key,
        )

    def add(self, title: str, text: str) -> None:
        vector = self.embeddings.embed_documents([text])[0]
        self.collection.add(
            ids=[str(uuid4())],
            documents=[text],
            embeddings=[vector],
            metadatas=[{"title": title}],
        )

    def search(self, query: str, limit: int = 4) -> list[str]:
        if self.collection.count() == 0:
            return []
        vector = self.embeddings.embed_query(query)
        matches = self.collection.query(query_embeddings=[vector], n_results=limit)
        return [text for text in (matches.get("documents") or [[]])[0] if text]
