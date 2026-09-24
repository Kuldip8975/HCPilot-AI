"""
Retrieval step of the RAG pipeline.

"RAG" = Retrieval-Augmented Generation: instead of asking the LLM to
answer purely from what it memorized during training (which for a niche,
just-built product like this one is nothing at all), we first RETRIEVE the
most relevant pieces of our own knowledge base for the user's question,
then hand those pieces to the LLM as context and ask it to GENERATE an
answer grounded in them.

This module is the "R" - retrieval. We use TF-IDF (Term Frequency -
Inverse Document Frequency) + cosine similarity, a classic, entirely
local information-retrieval technique from scikit-learn:

  - TF-IDF turns each chunk of text into a vector of word-importance
    scores (words that are common across every chunk score low; words
    that are distinctive to a particular chunk score high).
  - Cosine similarity then measures how "aligned" the query's vector is
    with each chunk's vector - the closer to 1.0, the more relevant.

Why TF-IDF instead of neural embeddings (e.g. sentence-transformers or an
embeddings API)? For a small, fixed knowledge base like this one (a dozen
short FAQ paragraphs), TF-IDF retrieves accurately, needs no GPU/model
download, and has zero extra runtime dependencies beyond scikit-learn -
which keeps this demo fast to set up and easy to run anywhere. The
retrieval step is a swappable component: for a much larger or more
free-form knowledge base you'd reach for embeddings + a vector database
(e.g. Chroma/FAISS/pgvector) instead, but the RAG *pattern* - retrieve,
then generate grounded on what was retrieved - is exactly the same either
way.
"""

import logging
import re
from typing import Any, Dict, List

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

_WORD_RE = re.compile(r"[a-zA-Z]+")

# Suffixes to strip, longest first, so plain TF-IDF (which only matches
# identical tokens) treats "feature"/"features", "visit"/"visiting", and
# "doctor"/"doctors" as the same word. This is a deliberately crude
# suffix-stripping stemmer (not a real linguistic stemmer like Porter/
# Snowball) - it's a handful of lines with zero extra dependencies, and
# for a small, curated knowledge base like this one it's enough to stop
# "what features does it have" from missing a chunk that only says
# "feature" in the singular.
_SUFFIXES = ("'s", "ing", "edly", "ed", "s")


def _stem(word: str) -> str:
    for suffix in _SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[: -len(suffix)]
    return word


def _stemmed_analyzer(text: str) -> List[str]:
    """Tokenize, drop stopwords, and lightly stem - used as the TF-IDF
    vectorizer's analyzer so retrieval isn't thrown off by singular vs.
    plural or a trailing -ing/-ed."""
    words = _WORD_RE.findall(text.lower())
    return [_stem(w) for w in words if w not in ENGLISH_STOP_WORDS and len(w) > 1]


class TfidfRetriever:
    """Simple local TF-IDF retriever over a fixed set of text chunks."""

    def __init__(self, documents: List[Dict[str, str]]):
        """
        Args:
            documents: list of {"id": ..., "title": ..., "text": ...} dicts.
        """
        self.documents = documents
        self.vectorizer = TfidfVectorizer(analyzer=_stemmed_analyzer)
        # Fit the vectorizer on all chunk texts once at startup, and cache
        # the resulting matrix - this is the "index" a real vector DB would
        # persist to disk; here it just lives in memory since the knowledge
        # base is small and static.
        self.matrix = self.vectorizer.fit_transform(
            [doc["text"] for doc in documents]
        )
        logger.info(f"TF-IDF retriever built over {len(documents)} knowledge base chunks")

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Return the top_k most relevant chunks for `query`, each with a
        similarity score in [0, 1] (higher = more relevant).
        """
        if not query or not query.strip():
            return []

        query_vector = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vector, self.matrix)[0]

        ranked = sorted(
            zip(self.documents, scores), key=lambda pair: pair[1], reverse=True
        )

        return [
            {
                "id": doc["id"],
                "title": doc["title"],
                "text": doc["text"],
                "score": float(score),
            }
            for doc, score in ranked[:top_k]
        ]