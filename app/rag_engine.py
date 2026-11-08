"""
app/rag_engine.py

Core RAG engine: document loading, chunking, embedding, indexing, and retrieval.
Uses sentence-transformers (all-MiniLM-L6-v2) for embeddings and faiss-cpu for
the vector index.  All computation is CPU-only.
"""

import os
import sys
import glob
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from typing import List, Tuple, Optional

# ---------------------------------------------------------------------------
# Add project root to sys.path so we can import defense/
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from defense.filters import ingestion_check, retrieval_filter


# ---------------------------------------------------------------------------
# Embedding model (loaded once, cached)
# ---------------------------------------------------------------------------
_model: Optional[SentenceTransformer] = None

def get_embedding_model() -> SentenceTransformer:
    """Load and cache the sentence-transformer model (CPU-only)."""
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
    return _model


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50) -> List[str]:
    """
    Split text into overlapping chunks by character count.
    Simple character-based chunking — sufficient for short docs in this demo.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


# ---------------------------------------------------------------------------
# RAG Knowledge Base
# ---------------------------------------------------------------------------

class RAGKnowledgeBase:
    """
    Manages the document store, FAISS index, and retrieval pipeline.
    """

    def __init__(self):
        self.model = get_embedding_model()
        self.embedding_dim = self.model.get_sentence_embedding_dimension()

        # Parallel lists — index i in each corresponds to the same chunk.
        self.chunks: List[str] = []        # chunk text
        self.sources: List[str] = []       # source filename
        self.doc_names: List[str] = []     # all unique document names loaded

        # FAISS index (Inner Product for cosine similarity on normalized vecs)
        self.index = faiss.IndexFlatIP(self.embedding_dim)

    # ----- Embedding helper ------------------------------------------------

    def _embed(self, texts: List[str]) -> np.ndarray:
        """Embed a list of texts and L2-normalize for cosine similarity."""
        embeddings = self.model.encode(texts, show_progress_bar=False)
        faiss.normalize_L2(embeddings)
        return embeddings.astype("float32")

    # ----- Ingestion -------------------------------------------------------

    def add_document(self, text: str, source: str) -> bool:
        """
        Chunk, embed, and add a single document to the index.
        Returns True if the document was accepted, False if rejected by the
        ingestion defense hook.
        """
        # =================================================================
        # DEFENSE HOOK — INGESTION-TIME CHECK
        # See defense/filters.py → ingestion_check()
        # =================================================================
        if not ingestion_check(text, source, metadata={}):
            return False  # Document rejected by defense

        doc_chunks = chunk_text(text)
        if not doc_chunks:
            return False

        embeddings = self._embed(doc_chunks)

        self.chunks.extend(doc_chunks)
        self.sources.extend([source] * len(doc_chunks))
        if source not in self.doc_names:
            self.doc_names.append(source)

        self.index.add(embeddings)
        return True

    def load_directory(self, directory: str) -> int:
        """Load all .txt files from a directory. Returns count of files loaded."""
        count = 0
        for filepath in sorted(glob.glob(os.path.join(directory, "*.txt"))):
            filename = os.path.basename(filepath)
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
            if self.add_document(text, filename):
                count += 1
        return count

    # ----- Retrieval -------------------------------------------------------

    def retrieve(
        self, query: str, top_k: int = 3
    ) -> List[Tuple[str, str, float]]:
        """
        Retrieve the top-k most similar chunks to the query.

        Returns:
            List of (chunk_text, source_file, cosine_similarity) tuples,
            sorted by descending similarity.
        """
        if self.index.ntotal == 0:
            return []

        query_embedding = self._embed([query])
        scores, indices = self.index.search(query_embedding, min(top_k, self.index.ntotal))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            results.append((self.chunks[idx], self.sources[idx], float(score)))

        # =================================================================
        # DEFENSE HOOK — RETRIEVAL-TIME FILTER
        # See defense/filters.py → retrieval_filter()
        # This is where you can filter, re-rank, or flag suspicious chunks
        # BEFORE they are sent to the LLM.
        # =================================================================
        results = retrieval_filter(results)

        return results

    # ----- Reset -----------------------------------------------------------

    def reset(self):
        """Clear the entire index and all stored chunks."""
        self.chunks.clear()
        self.sources.clear()
        self.doc_names.clear()
        self.index.reset()

    # ----- Info ------------------------------------------------------------

    def document_count(self) -> int:
        return len(self.doc_names)

    def chunk_count(self) -> int:
        return self.index.ntotal

