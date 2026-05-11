"""
authorship_module/stylometry.py
Stylometric analysis for authorship verification.

Strategy
--------
1. Divide the document into blocks/windows of N sentences.
2. Extract stylometric features from each block (e.g., TF-IDF on character n-grams,
   average sentence length, vocabulary richness, punctuation frequencies).
3. Compute the pairwise similarity between all blocks.
4. If blocks are highly dissimilar, it suggests multiple authors or heavily
   edited/pasted content (inconsistent writing style).
"""

from __future__ import annotations

import numpy as np
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from config import AUTHORSHIP_CONSISTENCY_THRESHOLD, AUTHORSHIP_WINDOW_SIZE
from logger import get_logger

log = get_logger(__name__)


class AuthorshipValidator:
    """Verifies consistency of writing style throughout a document."""

    def __init__(self):
        # Character n-grams are excellent for capturing stylistic quirks
        # (prefixes, suffixes, punctuation usage) irrespective of topic.
        self._vectorizer = TfidfVectorizer(
            analyzer='char_wb',
            ngram_range=(3, 4),
            max_features=5000
        )

    # ─── Public API ───────────────────────────────────────────────

    def analyse(self, sentences: List[str]) -> Dict[str, Any]:
        """
        Parameters
        ----------
        sentences : list of sentences from the submitted document

        Returns
        -------
        {
          "authorship_consistency": float (0–100, higher = more consistent),
          "flagged_sections": [{"chunk_index": int, "text": str, "anomaly_score": float, ...}],
          "explanation": str
        }
        """
        if not sentences or len(sentences) < AUTHORSHIP_WINDOW_SIZE * 2:
            return self._empty_result(
                f"Not enough sentences ({len(sentences)}) for reliable stylometric analysis."
            )

        log.info(f"Running authorship validation on {len(sentences)} sentences …")
        
        # 1. Chunk sentences into blocks
        blocks = self._create_blocks(sentences, AUTHORSHIP_WINDOW_SIZE)
        
        # 2. Extract features
        block_texts = [" ".join(block) for block in blocks]
        features_matrix = self._vectorizer.fit_transform(block_texts)
        
        # 3. Compute pairwise similarities
        sim_matrix = cosine_similarity(features_matrix)
        
        # 4. Find anomalous blocks (blocks that are dissimilar to the document average)
        # We define a block's "typicality" as its average similarity to all other blocks.
        typicality_scores = []
        n_blocks = len(blocks)
        for i in range(n_blocks):
            # Exclude self-similarity
            others_sims = np.delete(sim_matrix[i], i)
            typicality_scores.append(float(np.mean(others_sims)))
            
        overall_consistency = float(np.mean(typicality_scores))
        
        # 5. Flag anomalous blocks
        flagged: List[Dict[str, Any]] = []
        for idx, score in enumerate(typicality_scores):
            if score < AUTHORSHIP_CONSISTENCY_THRESHOLD:
                # Get the sentences for this block
                start_sent_idx = idx * AUTHORSHIP_WINDOW_SIZE
                end_sent_idx = start_sent_idx + len(blocks[idx])
                
                flagged.append({
                    "chunk_index": idx,
                    "sentence_range": f"{start_sent_idx}-{end_sent_idx}",
                    "text_snippet": block_texts[idx][:200] + "...",
                    "anomaly_score": round(1.0 - score, 4),
                    "explanation": (
                        f"This section's writing style is significantly different "
                        f"(similarity={score*100:.1f}%) from the rest of the document."
                    )
                })

        consistency_score_100 = overall_consistency * 100
        log.info(f"Authorship validation done | consistency={consistency_score_100:.1f}, flagged={len(flagged)}")

        return {
            "authorship_consistency": round(consistency_score_100, 2),
            "flagged_sections":       flagged,
            "explanation":            self._build_explanation(consistency_score_100, flagged, n_blocks),
        }

    # ─── Private helpers ──────────────────────────────────────────

    def _create_blocks(self, sentences: List[str], window_size: int) -> List[List[str]]:
        blocks = []
        for i in range(0, len(sentences), window_size):
            block = sentences[i : i + window_size]
            # Discard the last block if it's too small to be representative, 
            # unless it's the only block (handled by min length check above).
            if len(block) >= max(2, window_size // 2):
                blocks.append(block)
        return blocks

    def _build_explanation(
        self, score: float, flagged: List[Dict], total_blocks: int
    ) -> str:
        n_flagged = len(flagged)
        if score > 85:
            level = "very consistent"
        elif score > 70:
            level = "mostly consistent"
        elif score > 50:
            level = "somewhat inconsistent"
        else:
            level = "highly inconsistent"

        return (
            f"Writing style consistency is {level} (score={score:.1f}/100). "
            f"{n_flagged} of {total_blocks} sections showed significant stylistic deviations."
        )

    def _empty_result(self, reason: str) -> Dict[str, Any]:
        return {
            "authorship_consistency": 100.0, # Default to fully consistent if unanalysable
            "flagged_sections": [],
            "explanation": reason,
        }


# ─── Singleton ────────────────────────────────────────────────────
authorship_validator = AuthorshipValidator()
