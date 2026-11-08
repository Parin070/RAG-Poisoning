"""
app/ui.py

Streamlit UI for the RAG Poisoning Demo.
Run with:  streamlit run app/ui.py
"""

import os
import sys
import streamlit as st

# ---------------------------------------------------------------------------
# Project root on sys.path
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Load .env before anything else
from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from app.rag_engine import RAGKnowledgeBase
from app.llm_client import ask_llm, get_model_name

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
CLEAN_DIR = os.path.join(PROJECT_ROOT, "data", "clean")
POISON_DIR = os.path.join(PROJECT_ROOT, "data", "poison")

# ---------------------------------------------------------------------------
# Session State — persist the knowledge base across Streamlit reruns
# ---------------------------------------------------------------------------
if "kb" not in st.session_state:
    st.session_state.kb = RAGKnowledgeBase()
    st.session_state.kb.load_directory(CLEAN_DIR)
    st.session_state.kb_status = "clean"

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

kb: RAGKnowledgeBase = st.session_state.kb

# ---------------------------------------------------------------------------
# Page Config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Acme Corp AI Assistant — RAG Poisoning Demo",
    page_icon="🏢",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("🏢 Acme Corp Assistant")
    st.caption("RAG Knowledge Base Poisoning Demo")
    st.divider()

    # --- Knowledge Base Info ---
    st.subheader("📚 Knowledge Base")
    st.metric("Documents", kb.document_count())
    st.metric("Chunks indexed", kb.chunk_count())

    with st.expander("Documents in index", expanded=False):
        if kb.doc_names:
            for name in kb.doc_names:
                st.text(f"• {name}")
        else:
            st.info("No documents loaded.")

    st.divider()

    # --- Retrieval Settings ---
    st.subheader("⚙️ Retrieval Settings")
    top_k = st.slider("Top-K chunks to retrieve", min_value=1, max_value=10, value=3)
    st.caption(f"LLM model: `{get_model_name()}`")

    st.divider()

    # --- Upload Document ---
    st.subheader("📤 Add Document")
    uploaded_file = st.file_uploader(
        "Upload a .txt document",
        type=["txt"],
        help="The document will be chunked, embedded, and added to the live index.",
    )
    if uploaded_file is not None:
        content = uploaded_file.read().decode("utf-8")
        filename = uploaded_file.name
        if filename not in kb.doc_names:
            accepted = kb.add_document(content, filename)
            if accepted:
                st.success(f"✅ Added **{filename}** ({kb.chunk_count()} total chunks)")
            else:
                st.error(f"❌ **{filename}** was rejected by the ingestion defense filter.")
        else:
            st.warning(f"**{filename}** is already in the index.")

    # --- Paste document ---
    with st.expander("Or paste text directly"):
        paste_name = st.text_input("Document name", placeholder="my_document.txt")
        paste_text = st.text_area("Document content", height=120)
        if st.button("Add pasted document") and paste_name and paste_text:
            if paste_name not in kb.doc_names:
                accepted = kb.add_document(paste_text, paste_name)
                if accepted:
                    st.success(f"✅ Added **{paste_name}**")
                else:
                    st.error(f"❌ **{paste_name}** was rejected by ingestion filter.")
            else:
                st.warning(f"**{paste_name}** is already in the index.")

    st.divider()

    # --- Reset ---
    st.subheader("🔄 Reset")
    if st.button("Reset to clean knowledge base", type="primary"):
        kb.reset()
        kb.load_directory(CLEAN_DIR)
        st.session_state.chat_history = []
        st.session_state.kb_status = "clean"
        st.success("Knowledge base reset to clean state.")
        st.rerun()


# ---------------------------------------------------------------------------
# Main Area
# ---------------------------------------------------------------------------
st.title("🏢 Acme Corp Internal AI Assistant")
st.markdown(
    "Ask a question about Acme Corp policies, IT procedures, or anything "
    "in the knowledge base. This demo shows how RAG retrieval works — and "
    "how it can be poisoned."
)

# --- Chat Input ---
query = st.chat_input("Ask a question (e.g., 'How do I reset my VPN password?')")

if query:
    # 1. Retrieve relevant chunks
    retrieved = kb.retrieve(query, top_k=top_k)

    # 2. Ask the LLM
    answer = ask_llm(query, retrieved)

    # 3. Store in history
    st.session_state.chat_history.append({
        "query": query,
        "answer": answer,
        "retrieved": retrieved,
    })

# --- Display Chat History ---
for i, entry in enumerate(st.session_state.chat_history):
    # User message
    with st.chat_message("user"):
        st.write(entry["query"])

    # Assistant message
    with st.chat_message("assistant"):
        st.write(entry["answer"])

    # Transparency panel for the most recent question
    if i == len(st.session_state.chat_history) - 1:
        with st.expander("🔍 Transparency Panel — Retrieved Chunks", expanded=True):
            if not entry["retrieved"]:
                st.warning("No chunks were retrieved for this query.")
            else:
                for rank, (chunk_text, source, score) in enumerate(entry["retrieved"], 1):
                    # Color-code by score: green (>0.5), yellow (0.3-0.5), red (<0.3)
                    if score > 0.5:
                        score_color = "🟢"
                    elif score > 0.3:
                        score_color = "🟡"
                    else:
                        score_color = "🔴"

                    st.markdown(
                        f"**Rank {rank}** | {score_color} Similarity: **{score:.4f}** "
                        f"| Source: `{source}`"
                    )
                    st.code(chunk_text, language=None)
    else:
        # Collapsed transparency for older messages
        with st.expander(f"🔍 Retrieved Chunks (Q{i+1})", expanded=False):
            for rank, (chunk_text, source, score) in enumerate(entry["retrieved"], 1):
                st.markdown(
                    f"**Rank {rank}** | Similarity: **{score:.4f}** | Source: `{source}`"
                )
                st.code(chunk_text, language=None)

# --- Demo Tip ---
if not st.session_state.chat_history:
    st.info(
        "💡 **Demo steps:**\n"
        "1. Ask: *\"How do I reset my VPN password?\"* — observe the clean answer.\n"
        "2. Upload `data/poison/vpn_password_reset_poison.txt` via the sidebar.\n"
        "3. Ask the same question again — observe how the poison chunk appears "
        "in the retrieved results and corrupts the answer.\n"
        "4. Check the Transparency Panel to see *why* the attack worked.\n"
        "5. Click **Reset to clean knowledge base** to restore the original state."
    )

