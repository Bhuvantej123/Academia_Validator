"""
ai_detection_module/detector.py
AI-generated text detection using HuggingFace models or fallback heuristics.

Strategy
--------
1. Split text into chunks (e.g. sentences or overlapping token windows).
2. Pass chunks through a binary classification model trained to detect AI text
   (e.g., roberta-base-openai-detector).
3. Aggregate chunk probabilities into an overall AI probability.
4. Flag high-probability sentences.
"""

from __future__ import annotations

import numpy as np
from typing import List, Dict, Any
from config import AI_DETECTION_THRESHOLD, AI_DETECTION_MODEL
from logger import get_logger

log = get_logger(__name__)


class AIDetector:
    """Detects AI-generated text using transformer models or heuristic fallback."""

    def __init__(self):
        self._pipeline = None
        self._fallback = False

    # ─── Public API ───────────────────────────────────────────────

    def analyse(self, sentences: List[str]) -> Dict[str, Any]:
        """
        Parameters
        ----------
        sentences : list of sentences from the submitted document

        Returns
        -------
        {
          "ai_probability": float (0–100, higher = more likely AI),
          "flagged_sections": [{"sentence": str, "ai_probability": float, "explanation": str}],
          "explanation": str
        }
        """
        if not sentences:
            return self._empty_result("No sentences provided.")

        self._load_model()

        log.info(f"Running AI detection on {len(sentences)} sentences …")
        flagged: List[Dict[str, Any]] = []
        probabilities: List[float] = []

        # Process in chunks to avoid overwhelming the model, but for sentences
        # it's usually fine to batch them directly if using pipelines.
        if self._fallback:
            probs = self._heuristic_analysis(sentences)
        else:
            probs = self._run_pipeline(sentences)

        for idx, (sent, prob) in enumerate(zip(sentences, probs)):
            probabilities.append(prob)
            if prob >= AI_DETECTION_THRESHOLD:
                flagged.append({
                    "sentence_index": idx,
                    "sentence":       sent,
                    "ai_probability": round(prob, 4),
                    "explanation": (
                        f"This sentence has a {prob * 100:.1f}% probability of being "
                        "AI-generated, based on linguistic patterns."
                    ),
                })

        overall_probability = self._compute_overall_prob(probabilities, flagged)
        log.info(f"AI detection done | prob={overall_probability:.1f}, flagged={len(flagged)}")

        return {
            "ai_probability":   round(overall_probability, 2),
            "flagged_sections": flagged,
            "explanation":      self._build_explanation(overall_probability, flagged, sentences),
        }

    # ─── Private helpers ──────────────────────────────────────────

    def _load_model(self) -> None:
        if self._pipeline is not None or self._fallback:
            return

        log.info(f"Loading AI detection model: {AI_DETECTION_MODEL}")
        try:
            from transformers import pipeline
            # Text classification pipeline
            self._pipeline = pipeline(
                "text-classification",
                model=AI_DETECTION_MODEL,
                device=-1, # CPU
                truncation=True,
                max_length=512
            )
            log.info("AI detection model loaded ✓")
        except Exception as e:
            log.warning(f"HuggingFace model unavailable ({e}). Using heuristic fallback.")
            self._fallback = True

    def _run_pipeline(self, sentences: List[str]) -> List[float]:
        try:
            results = self._pipeline(sentences)
            probs = []
            for res in results:
                # RoBERTa OpenAI detector typically outputs 'Fake' or 'Real'
                if res['label'] == 'Fake':
                    probs.append(res['score'])
                else:
                    probs.append(1.0 - res['score'])
            return probs
        except Exception as e:
            log.error(f"Pipeline inference failed: {e}. Falling back to heuristics.")
            self._fallback = True
            return self._heuristic_analysis(sentences)

    def _heuristic_analysis(self, sentences: List[str]) -> List[float]:
        """
        Simple fallback heuristic based on sentence length variation and vocabulary repetition.
        (Real AI detection requires the ML model. This is a stand-in for the prototype).
        """
        probs = []
        for sent in sentences:
            words = sent.split()
            if not words:
                probs.append(0.0)
                continue
            
            # Very simplistic heuristic: AI text often has very average sentence lengths
            # and low variance in structure. This is a dummy calculation.
            length = len(words)
            if 15 <= length <= 25:
                prob = 0.6  # Moderately suspicious length
            elif length > 40:
                prob = 0.2  # Human run-on sentence
            else:
                prob = 0.3
            
            # Jargon or lack thereof heuristic placeholder
            probs.append(prob)
        return probs

    def _compute_overall_prob(self, probabilities: List[float], flagged: List[Dict]) -> float:
        """Overall AI probability 0–100."""
        if not probabilities:
            return 0.0
        avg_prob = float(np.mean(probabilities))
        flagged_ratio = len(flagged) / max(len(probabilities), 1)
        # Blend: 50% flagged-ratio, 50% average probability
        score = (flagged_ratio * 0.50 + avg_prob * 0.50) * 100
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
            f"AI-generated content risk is {level} (probability={score:.1f}/100). "
            f"{n_flagged} of {total} sentences ({n_flagged / max(total, 1) * 100:.1f}%) "
            f"show patterns consistent with AI generation."
        )

    def _empty_result(self, reason: str) -> Dict[str, Any]:
        return {
            "ai_probability": 0.0,
            "flagged_sections": [],
            "explanation": reason,
        }


# ─── Singleton ────────────────────────────────────────────────────
ai_detector = AIDetector()
