"""
database/models.py — SQLAlchemy ORM models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id           = Column(Integer, primary_key=True, index=True)
    job_id       = Column(String(64), unique=True, nullable=False, index=True)
    filename     = Column(String(256), nullable=False)
    file_type    = Column(String(16))
    status       = Column(String(32), default="pending")   # pending | running | done | error
    word_count   = Column(Integer, default=0)
    created_at   = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Scores
    authenticity_score       = Column(Float, nullable=True)
    plagiarism_score         = Column(Float, nullable=True)
    ai_probability           = Column(Float, nullable=True)
    authorship_consistency   = Column(Float, nullable=True)

    # Full JSON report
    report_json  = Column(Text, nullable=True)
    report_pdf   = Column(String(512), nullable=True)
    error_msg    = Column(Text, nullable=True)

    def to_dict(self) -> dict:
        return {
            "job_id":                  self.job_id,
            "filename":                self.filename,
            "status":                  self.status,
            "word_count":              self.word_count,
            "created_at":              self.created_at.isoformat() if self.created_at else None,
            "completed_at":            self.completed_at.isoformat() if self.completed_at else None,
            "authenticity_score":      self.authenticity_score,
            "plagiarism_score":        self.plagiarism_score,
            "ai_probability":          self.ai_probability,
            "authorship_consistency":  self.authorship_consistency,
        }
