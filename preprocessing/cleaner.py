"""
preprocessing/cleaner.py
Text cleaning, sentence segmentation, and tokenisation.
"""

import re
import unicodedata
from typing import List
from config import MIN_SENTENCE_LENGTH
from logger import get_logger

log = get_logger(__name__)


class TextPreprocessor:
    """
    Cleans raw extracted text and segments it into sentences.
    Designed to be pipeline-safe (deterministic, no external network calls).
    """

    # ─── Public API ───────────────────────────────────────────────

    def process(self, raw_text: str) -> dict:
        """
        Full preprocessing pipeline.

        Returns
        -------
        dict with keys:
            cleaned_text   : str   — normalised full text
            sentences      : list  — list of sentence strings
            word_count     : int
            char_count     : int
            paragraphs     : list  — list of paragraph strings
        """
        cleaned = self._normalise(raw_text)
        paragraphs = self._split_paragraphs(cleaned)
        sentences = self._split_sentences(cleaned)
        sentences = [s for s in sentences if len(s) >= MIN_SENTENCE_LENGTH]

        word_count = len(cleaned.split())
        log.info(
            f"Preprocessing done | sentences={len(sentences)} words={word_count}"
        )

        return {
            "cleaned_text": cleaned,
            "sentences":    sentences,
            "paragraphs":   paragraphs,
            "word_count":   word_count,
            "char_count":   len(cleaned),
        }

    # ─── Private helpers ──────────────────────────────────────────

    def _normalise(self, text: str) -> str:
        # Unicode normalisation
        text = unicodedata.normalize("NFKC", text)
        # Remove null bytes and control chars (keep newlines/tabs)
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
        # Collapse multiple blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Collapse multiple spaces
        text = re.sub(r" {2,}", " ", text)
        # Strip trailing whitespace per line
        text = "\n".join(line.rstrip() for line in text.splitlines())
        return text.strip()

    def _split_paragraphs(self, text: str) -> List[str]:
        paras = [p.strip() for p in re.split(r"\n{2,}", text)]
        return [p for p in paras if p]

    def _split_sentences(self, text: str) -> List[str]:
        """
        Sentence splitter that avoids breaking on common abbreviations.
        Falls back to spaCy if available, otherwise uses regex.
        """
        try:
            return self._spacy_sentences(text)
        except Exception:
            return self._regex_sentences(text)

    def _spacy_sentences(self, text: str) -> List[str]:
        import spacy
        # Use the smallest English model for speed
        try:
            nlp = spacy.load("en_core_web_sm", disable=["ner", "tagger", "lemmatizer"])
        except OSError:
            raise RuntimeError("spaCy model not installed")
        # Process in chunks to avoid memory issues
        chunk_size = 100_000
        sentences: List[str] = []
        for i in range(0, len(text), chunk_size):
            doc = nlp(text[i: i + chunk_size])
            sentences.extend([sent.text.strip() for sent in doc.sents if sent.text.strip()])
        return sentences

    def _regex_sentences(self, text: str) -> List[str]:
        # Split on sentence-ending punctuation followed by a capital or end-of-string
        sentence_endings = re.compile(
            r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|!)\s+(?=[A-Z])'
        )
        parts = sentence_endings.split(text)
        return [p.strip() for p in parts if p.strip()]

    def chunk_sentences(self, sentences: List[str], chunk_size: int = 10) -> List[List[str]]:
        """Split sentence list into overlapping windows for analysis."""
        chunks = []
        step = max(1, chunk_size // 2)
        for i in range(0, len(sentences), step):
            chunk = sentences[i: i + chunk_size]
            if chunk:
                chunks.append(chunk)
        return chunks


# ─── Singleton ────────────────────────────────────────────────────
preprocessor = TextPreprocessor()
