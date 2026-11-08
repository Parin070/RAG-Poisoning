"""
defense/filters.py

Defense hook stubs for the RAG poisoning demo.
These are intentionally left as no-ops so the attack succeeds in the demo.
Implement your defenses here and wire them into app/rag_engine.py.
"""

from typing import List, Tuple


# =============================================================================
# INGESTION-TIME DEFENSE STUB
# =============================================================================
# This function is called during document ingestion, before a new document is
# added to the FAISS index. Use it to inspect and potentially reject documents
# that look suspicious.
#
# Ideas for implementation:
#   - Anomaly detection: flag documents whose embeddings are unusually close
#     to existing high-traffic query embeddings.
#   - Source verification: check that the document comes from an approved
#     source / author / upload channel.
#   - Content analysis: look for social-engineering patterns (urgency language,
#     external phone numbers, requests for PII).
#   - Duplicate / near-duplicate detection: flag documents that are
#     suspiciously similar to existing ones (possible overwrites).
# =============================================================================

def ingestion_check(text: str, source: str, metadata: dict) -> bool:
    """
    Inspect a document at ingestion time. Return True to allow it into the
    index, or False to reject it.

    Args:
        text: The full text content of the document.
        source: The filename / path of the document.
        metadata: Any additional metadata (uploader, timestamp, etc.).

    Returns:
        True if the document passes all checks; False to block ingestion.
    """
    # TODO: Implement ingestion-time defenses here.
    # For now, allow everything (no defense).
    return True


# =============================================================================
# RETRIEVAL-TIME DEFENSE STUB
# =============================================================================
# This function is called after top-k retrieval and before the retrieved chunks
# are passed to the LLM prompt. Use it to filter, re-rank, or flag suspicious
# chunks.
#
# Ideas for implementation:
#   - Similarity-score thresholding: drop chunks below a minimum score.
#   - Source-diversity filtering: ensure chunks come from multiple sources
#     rather than one suspicious document dominating results.
#   - Cross-reference check: compare the retrieved answer against a known-good
#     "golden" answer set.
#   - Consistency voting: retrieve more chunks than needed and drop outliers
#     whose content contradicts the majority.
#   - Provenance display: always show the user which documents were used
#     (already implemented in the transparency panel).
# =============================================================================

def retrieval_filter(
    chunks: List[Tuple[str, str, float]]
) -> List[Tuple[str, str, float]]:
    """
    Filter or re-rank retrieved chunks before they are sent to the LLM.

    Args:
        chunks: A list of (chunk_text, source_file, similarity_score) tuples,
                ordered by descending similarity.

    Returns:
        A (possibly filtered/re-ordered) list of the same tuple format.
    """
    # TODO: Implement retrieval-time defenses here.
    # For now, pass everything through unmodified (no defense).
    return chunks

