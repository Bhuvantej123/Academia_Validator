"""
plagiarism_module/detector.py
Semantic plagiarism detection using Sentence-BERT embeddings.

Strategy
--------
1. Embed all sentences from the submitted document.
2. Compare each sentence against an internal reference corpus
   (loaded from the database / reference files).
3. Flag sentences whose cosine similarity exceeds THRESHOLD.
4. Return a plagiarism_score (0–100) and list of flagged sections.

For a working prototype without a live corpus, we use a built-in
sample reference corpus so the pipeline runs end-to-end.
"""

from __future__ import annotations

import numpy as np
from typing import List, Dict, Any, Tuple
from config import PLAGIARISM_SIMILARITY_THRESHOLD, PLAGIARISM_MODEL
from logger import get_logger

log = get_logger(__name__)


# ─── Sample reference corpus (prototype) ──────────────────────────
# Replace with database-backed or web-search-backed corpus in production.
SAMPLE_REFERENCE_CORPUS: List[str] = [
    "The theory of relativity was proposed by Albert Einstein in 1905.",
    "Machine learning is a subset of artificial intelligence.",
    "Neural networks are inspired by the structure of the human brain.",
    "Climate change refers to long-term shifts in global temperatures.",
    "The water cycle describes how water evaporates, condenses, and precipitates.",
    "Photosynthesis is the process by which plants convert sunlight into food.",
    "The French Revolution began in 1789 and transformed French society.",
    "DNA carries the genetic instructions for the development of all living organisms.",
    "The internet has revolutionised communication and access to information.",
    "Quantum mechanics describes the behaviour of particles at the atomic scale.",
    "Plagiarism is the act of presenting someone else's work as your own.",
    "Academic integrity is essential for maintaining trust in scholarship.",
    "Natural language processing enables computers to understand human language.",
    "Deep learning models require large amounts of labelled training data.",
    "The supply and demand curve determines the equilibrium price in a market.",
]


class PlagiarismDetector:
    """Sentence-level semantic plagiarism detector."""

    def __init__(self):
        self._model = None
        self._ref_embeddings: np.ndarray | None = None
        self._reference_sentences: List[str] = []

    # ─── Public API ───────────────────────────────────────────────

    def analyse(
        self,
        sentences: List[str],
        reference_corpus: List[str] | None = None,
    ) -> Dict[str, Any]:
        """
        Parameters
        ----------
        sentences        : list of sentences from the submitted document
        reference_corpus : optional custom corpus; defaults to sample corpus

        Returns
        -------
        {
          "plagiarism_score": float (0–100, lower = more authentic),
          "flagged_sections": [{"sentence": str, "similarity": float,
                                "matched_reference": str, "explanation": str}],
          "explanation":  str
        }
        """
        if not sentences:
            return self._empty_result("No sentences provided.")

        corpus = reference_corpus or SAMPLE_REFERENCE_CORPUS
        self._load_model_and_corpus(corpus)

        log.info(f"Running plagiarism detection on {len(sentences)} sentences …")
        doc_embeddings = self._model.encode(sentences, convert_to_numpy=True, show_progress_bar=False)

        flagged: List[Dict[str, Any]] = []
        similarities: List[float] = []

        for idx, (sent, emb) in enumerate(zip(sentences, doc_embeddings)):
            sim, best_ref = self._best_match(emb)
            similarities.append(sim)
            if sim >= PLAGIARISM_SIMILARITY_THRESHOLD:
                flagged.append({
                    "sentence_index": idx,
                    "sentence":       sent,
                    "similarity":     round(float(sim), 4),
                    "matched_reference": best_ref,
                    "explanation": (
                        f"This sentence is {sim * 100:.1f}% semantically similar "
                        f"to a reference text, suggesting potential plagiarism."
                    ),
                })

        plagiarism_score = self._compute_score(similarities, flagged)
        log.info(f"Plagiarism detection done | score={plagiarism_score:.1f}, flagged={len(flagged)}")

        return {
            "plagiarism_score": round(plagiarism_score, 2),
            "flagged_sections": flagged,
            "explanation":      self._build_explanation(plagiarism_score, flagged, sentences),
        }

    # ─── Private helpers ──────────────────────────────────────────

    def _load_model_and_corpus(self, corpus: List[str]) -> None:
        if self._model is None:
            log.info(f"Loading Sentence-BERT model: {PLAGIARISM_MODEL}")
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(PLAGIARISM_MODEL)
                log.info("Sentence-BERT model loaded ✓")
            except Exception as e:
                log.warning(f"Sentence-BERT unavailable ({e}). Using TF-IDF fallback.")
                self._model = _TFIDFFallbackModel()

        if self._reference_sentences != corpus:
            log.debug("Encoding reference corpus …")
            self._reference_sentences = corpus
            self._ref_embeddings = self._model.encode(
                corpus, convert_to_numpy=True, show_progress_bar=False
            )

    def _best_match(self, embedding: np.ndarray) -> Tuple[float, str]:
        """Returns (max_cosine_similarity, best_matching_reference_sentence)."""
        sims = self._cosine_similarities(embedding, self._ref_embeddings)
        best_idx = int(np.argmax(sims))
        return float(sims[best_idx]), self._reference_sentences[best_idx]

    @staticmethod
    def _cosine_similarities(vec: np.ndarray, matrix: np.ndarray) -> np.ndarray:
        vec_norm = vec / (np.linalg.norm(vec) + 1e-10)
        mat_norm = matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-10)
        return mat_norm @ vec_norm

    def _compute_score(self, similarities: List[float], flagged: List[Dict]) -> float:
        """Plagiarism score 0–100; higher = more plagiarised."""
        if not similarities:
            return 0.0
        avg_sim = float(np.mean(similarities))
        flagged_ratio = len(flagged) / max(len(similarities), 1)
        # Blend: 60% flagged-ratio, 40% average similarity
        score = (flagged_ratio * 0.60 + avg_sim * 0.40) * 100
        return min(score, 100.0)

    def _build_explanation(
        self, score: float, flagged: List[Dict], sentences: List[str]
    ) -> str:
        total = len(sentences)
        n_flagged = len(flagged)
        if score < 10:
            level = "very low"
        elif score < 30:
            level = "low"
        elif score < 55:
            level = "moderate"
        elif score < 75:
            level = "high"
        else:
            level = "very high"

        return (
            f"Plagiarism risk is {level} (score={score:.1f}/100). "
            f"{n_flagged} of {total} sentences ({n_flagged / max(total, 1) * 100:.1f}%) "
            f"exceeded the similarity threshold of {PLAGIARISM_SIMILARITY_THRESHOLD * 100:.0f}%."
        )

    def _empty_result(self, reason: str) -> Dict[str, Any]:
        return {
            "plagiarism_score": 0.0,
            "flagged_sections": [],
            "explanation": reason,
        }


# ─── TF-IDF Fallback (no HuggingFace) ────────────────────────────

class _TFIDFFallbackModel:
    """Lightweight TF-IDF based embedding fallback when Sentence-BERT is unavailable."""

    def __init__(self):
        from sklearn.feature_extraction.text import TfidfVectorizer
        self._vectorizer = TfidfVectorizer(max_features=5000)
        self._fitted = False

    def encode(self, texts: List[str], **kwargs) -> np.ndarray:
        if not self._fitted:
            self._vectorizer.fit(texts)
            self._fitted = True
        matrix = self._vectorizer.transform(texts).toarray()
        return matrix.astype(np.float32)


# ─── Singleton ────────────────────────────────────────────────────
plagiarism_detector = PlagiarismDetector()
