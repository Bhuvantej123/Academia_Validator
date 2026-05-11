"""
scoring_engine/calculator.py
Fuses module scores into a final Authenticity Score.
"""

from typing import Dict, Any
from config import SCORE_WEIGHTS
from logger import get_logger

log = get_logger(__name__)


class ScoringEngine:
    
    def calculate_authenticity(
        self,
        plagiarism_res: Dict[str, Any],
        ai_res: Dict[str, Any],
        authorship_res: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Calculates the final authenticity score (0-100, where 100 is fully authentic).
        
        plagiarism_score is 0-100 (100 = 100% plagiarised)
        ai_probability is 0-100 (100 = 100% AI generated)
        authorship_consistency is 0-100 (100 = 100% consistent)
        """
        p_score = plagiarism_res.get("plagiarism_score", 0.0)
        a_score = ai_res.get("ai_probability", 0.0)
        c_score = authorship_res.get("authorship_consistency", 100.0)
        
        # Convert plagiarism and AI to 'authenticity' dimensions (invert them)
        # 100% plagiarised -> 0% authentic
        p_auth = max(0.0, 100.0 - p_score)
        a_auth = max(0.0, 100.0 - a_score)
        
        # Consistency is already in the right direction
        c_auth = c_score
        
        w_p = SCORE_WEIGHTS["plagiarism"]
        w_a = SCORE_WEIGHTS["ai_detection"]
        w_c = SCORE_WEIGHTS["authorship"]
        
        final_score = (p_auth * w_p) + (a_auth * w_a) + (c_auth * w_c)
        final_score = round(final_score, 2)
        
        log.info(f"Final Authenticity Score: {final_score}/100")
        
        return {
            "authenticity_score": final_score,
            "components": {
                "plagiarism_score": p_score,
                "ai_probability": a_score,
                "authorship_consistency": c_score,
            },
            "interpretation": self._interpret_score(final_score)
        }
        
    def _interpret_score(self, score: float) -> str:
        if score >= 90:
            return "Highly authentic. Minimal risks detected."
        elif score >= 75:
            return "Likely authentic. Minor issues flagged for review."
        elif score >= 50:
            return "Moderate risk. Significant portions are flagged as potentially unoriginal or AI-generated."
        else:
            return "High risk. The document shows strong evidence of plagiarism, AI generation, or inconsistent authorship."


# ─── Singleton ────────────────────────────────────────────────────
scoring_engine = ScoringEngine()
