"""
report_generator/generator.py
Generates the final structured JSON (and optionally PDF) report.
"""

import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
from config import REPORT_VERSION
from logger import get_logger

log = get_logger(__name__)


class ReportGenerator:
    
    def generate_json_report(
        self,
        job_id: str,
        filename: str,
        word_count: int,
        score_data: Dict[str, Any],
        plagiarism_res: Dict[str, Any],
        ai_res: Dict[str, Any],
        authorship_res: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Compiles all results into a standardised JSON structure."""
        
        report = {
            "metadata": {
                "report_version": REPORT_VERSION,
                "job_id": job_id,
                "filename": filename,
                "timestamp": datetime.utcnow().isoformat(),
                "word_count": word_count,
            },
            "summary": {
                "authenticity_score": score_data["authenticity_score"],
                "plagiarism_score": score_data["components"]["plagiarism_score"],
                "ai_probability": score_data["components"]["ai_probability"],
                "authorship_consistency": score_data["components"]["authorship_consistency"],
                "interpretation": score_data["interpretation"],
            },
            "details": {
                "plagiarism": {
                    "explanation": plagiarism_res["explanation"],
                    "flagged_sections": plagiarism_res["flagged_sections"],
                },
                "ai_detection": {
                    "explanation": ai_res["explanation"],
                    "flagged_sections": ai_res["flagged_sections"],
                },
                "authorship": {
                    "explanation": authorship_res["explanation"],
                    "flagged_sections": authorship_res["flagged_sections"],
                }
            }
        }
        
        log.info(f"Generated JSON report for job {job_id}")
        return report

    def generate_pdf_report(self, report_json: Dict[str, Any], output_path: Path) -> str:
        """
        Generates a basic PDF report using reportlab.
        (Placeholder for full implementation, generates text for prototype).
        """
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            
            c = canvas.Canvas(str(output_path), pagesize=letter)
            width, height = letter
            
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, height - 50, "Authenticity Validator of Academia - Report")
            
            c.setFont("Helvetica", 12)
            c.drawString(50, height - 80, f"File: {report_json['metadata']['filename']}")
            c.drawString(50, height - 100, f"Job ID: {report_json['metadata']['job_id']}")
            c.drawString(50, height - 120, f"Date: {report_json['metadata']['timestamp']}")
            
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, height - 160, "Summary Scores")
            
            c.setFont("Helvetica", 12)
            y = height - 180
            s = report_json['summary']
            c.drawString(50, y, f"Authenticity Score: {s['authenticity_score']}/100")
            c.drawString(50, y - 20, f"Plagiarism Risk: {s['plagiarism_score']}/100")
            c.drawString(50, y - 40, f"AI Probability: {s['ai_probability']}/100")
            c.drawString(50, y - 60, f"Authorship Consistency: {s['authorship_consistency']}/100")
            
            c.drawString(50, y - 100, f"Interpretation: {s['interpretation']}")
            
            c.save()
            log.info(f"Generated PDF report: {output_path}")
            return str(output_path)
            
        except Exception as e:
            log.error(f"Failed to generate PDF report: {e}")
            return ""


# ─── Singleton ────────────────────────────────────────────────────
report_generator = ReportGenerator()
