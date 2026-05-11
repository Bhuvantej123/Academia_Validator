import pytest
from preprocessing.cleaner import preprocessor

def test_cleaner_normalisation():
    raw = "This is  a   test. \n\n\n It has multiple   spaces."
    res = preprocessor.process(raw)
    assert "  " not in res["cleaned_text"]
    assert "\n\n\n" not in res["cleaned_text"]

def test_cleaner_sentence_splitting():
    raw = "Dr. Smith went to the store. He bought an apple! What else did he buy? Nothing."
    res = preprocessor.process(raw)
    # At least 4 sentences
    assert len(res["sentences"]) >= 3
