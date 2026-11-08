# RAG Knowledge-Base Poisoning — Lab Write-Up

---

## 1. Setup

**Environment:**
- OS: Windows 11
- Python: 3.10+
- Embedding model: `all-MiniLM-L6-v2` (sentence-transformers, CPU-only)
- Vector index: `faiss-cpu`
- LLM: _[model name from OPENROUTER_MODEL]_ via OpenRouter
- UI: Streamlit

**Knowledge base:** 17 fictional Acme Corp documents covering IT helpdesk procedures, HR policies, security contacts, and onboarding.

---

## 2. Threat Model

**System under attack:** A RAG-based internal chatbot that retrieves company documents to answer employee questions.

**Attacker goal:** Cause the chatbot to return a wrong, attacker-chosen answer to a specific target question.

**Attacker capability:** The attacker can insert (or modify) one document in the knowledge base. This models scenarios such as:
- A compromised shared drive or wiki
- A malicious document uploaded through a ticket system
- An insider with write access to the document store

**Attacker does NOT need to:**
- Access or modify the LLM itself
- Know the LLM's weights or system prompt
- Have direct access to the FAISS index

---

## 3. Target Question

```
"How do I reset my VPN password?"
```

**Legitimate answer (from clean knowledge base):** Go to the IT Self-Service Portal at `https://itportal.acmecorp.internal`, use the VPN & Remote Access section, or contact IT Help Desk at extension 4357.

---

## 4. Poison Construction

The poison document (`data/poison/vpn_password_reset_poison.txt`) is crafted in two parts:

**Part 1 — Retrieval Bait:**
_[Describe the text you used to match the target query's embedding. Explain why it achieves high cosine similarity.]_

> _Paste the relevant lines here._

**Part 2 — Malicious Payload:**
_[Describe the fake answer the attacker wants the LLM to output.]_

> _Paste the relevant lines here._

---

## 5. Injection Steps

1. Started the app with the clean knowledge base (17 documents).
2. Asked the target question: _"How do I reset my VPN password?"_
3. Recorded the clean answer and retrieved chunks.
4. Uploaded `vpn_password_reset_poison.txt` via the sidebar.
5. Confirmed the document was chunked and indexed (check document count).
6. Asked the same target question again.

---

## 6. Observed Result

### Before Poisoning

**Answer:**
_[Paste the clean answer here]_

**Retrieved Chunks (Transparency Panel):**

| Rank | Source | Similarity | Content (first 50 chars) |
|------|--------|-----------|--------------------------|
| 1 | _____  | _____     | ________________________ |
| 2 | _____  | _____     | ________________________ |
| 3 | _____  | _____     | ________________________ |

_[Screenshot placeholder: clean_answer.png]_

### After Poisoning

**Answer:**
_[Paste the poisoned answer here]_

**Retrieved Chunks (Transparency Panel):**

| Rank | Source | Similarity | Content (first 50 chars) |
|------|--------|-----------|--------------------------|
| 1 | _____  | _____     | ________________________ |
| 2 | _____  | _____     | ________________________ |
| 3 | _____  | _____     | ________________________ |

_[Screenshot placeholder: poisoned_answer.png]_

---

## 7. Why It Worked

**Retrieval condition:** The poison document's embedding is close to the target query because _[explain — the bait text closely paraphrases the target question, so `all-MiniLM-L6-v2` maps them to nearby points in the embedding space]_.

**Generation condition:** Once the poison chunk is retrieved, the LLM includes it in the context window. Because the prompt instructs the LLM to "answer using ONLY the context provided," the LLM treats the malicious text as authoritative and _[explain — the fake answer is written in a confident, official tone that the LLM has no reason to doubt]_.

**Key insight:** The attack exploits the _trust boundary_ between the retrieval system and the LLM. The retrieval system selects context purely by embedding similarity — it has no notion of document provenance, authority, or correctness.

---

## 8. Limitations

- _[Discuss limitations of this demo vs. a real-world attack]_
- The demo uses a small, controlled knowledge base.
- Real systems may have access controls on document ingestion.
- Some LLMs may exhibit more or less compliance with contradictory context.
- The attack is targeted: it only affects queries similar to the bait text.

---

## 9. Proposed Defenses

See [`defense/filters.py`](defense/filters.py) for the integration stubs.

### Ingestion-Time Defenses
- _[Describe your proposed ingestion-time defense]_
- _[Link to implementation in `defense/` if completed]_

### Retrieval-Time Defenses
- _[Describe your proposed retrieval-time defense]_
- _[Link to implementation in `defense/` if completed]_

### Other Mitigations
- _[E.g., provenance tracking, document signing, anomaly monitoring]_

---

## References

- _[Add any papers, blog posts, or resources you consulted]_

