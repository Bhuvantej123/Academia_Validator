# Authenticity Validator of Academia

A complete Python backend system designed to analyze academic documents and determine their authenticity by combining Plagiarism Detection, AI-Generated Content Detection, and Stylometric Authorship Verification.

## 🌟 Project Overview

This project provides a robust FastAPI-based REST API that accepts document uploads (PDF, DOCX, TXT) and asynchronously processes them through an NLP pipeline. The final output is an **Authenticity Score (0-100)** and a detailed structured report highlighting flagged sections and explaining the rationale behind the scores.

### Core Modules

1. **Input Handler & Preprocessing**: Extracts text gracefully from multiple formats and cleans/normalizes the text into overlapping chunks and sentences.
2. **Plagiarism Module**: Uses `Sentence-BERT` (or a TF-IDF fallback) to perform semantic similarity matching against a reference corpus.
3. **AI Detection Module**: Connects to HuggingFace classification models (e.g., `roberta-base-openai-detector`) to flag sentences that show patterns of AI-generation.
4. **Authorship Module**: Uses stylometry (character n-grams and cosine similarity) to identify abrupt shifts in writing style across the document.
5. **Scoring Engine**: Fuses the sub-scores together via configurable weighting to produce the final `authenticity_score`.
6. **Report Generator**: Outputs a detailed JSON response, including full explanations of flagged sentences, and can optionally generate a PDF report summary.

## 🏗️ Architecture & Folder Structure

```text
academia_validator/
├── config.py                       # Centralised configuration (thresholds, weights)
├── logger.py                       # Custom colored logger
├── main.py                         # FastAPI Application Entrypoint
├── requirements.txt                # Python dependencies
├── database/
│   ├── db.py                       # Async SQLAlchemy connection
│   └── models.py                   # ORM Models (AnalysisJob)
├── input_handler/
│   └── extractor.py                # PDF, DOCX, TXT text extraction
├── preprocessing/
│   └── cleaner.py                  # Sentence splitting and text normalisation
├── plagiarism_module/
│   └── detector.py                 # Semantic Plagiarism Detection
├── ai_detection_module/
│   └── detector.py                 # AI Probability classification
├── authorship_module/
│   └── stylometry.py               # Stylometric analysis for consistency
├── scoring_engine/
│   └── calculator.py               # Score fusion logic
├── report_generator/
│   └── generator.py                # JSON & PDF report generation
├── tests/                          # Unit tests
└── uploads/ & reports/             # Local storage directories
```

## 🚀 How to Run Locally

### 1. Set Up Environment

Ensure you have Python 3.10+ installed.

```bash
# Navigate to the project directory
cd "academia_validator"

# (Optional but recommended) Create a virtual environment
python -m venv venv
venv\Scripts\activate  # On Windows
# source venv/bin/activate  # On Mac/Linux

# Install all dependencies
pip install -r requirements.txt
```

> **Note on Heavy ML Dependencies:** 
> The application uses heavy machine learning libraries (`torch`, `transformers`, `sentence-transformers`, `spacy`). If these fail to install or load, the modules are designed to **gracefully fallback to lightweight heuristics or standard TF-IDF algorithms**. This ensures the pipeline runs end-to-end even on limited hardware!

### 2. Run the Server

Start the FastAPI application:

```bash
uvicorn main:app --reload
```

The server will start at `http://127.0.0.1:8000`. 
You can view the interactive API documentation at `http://127.0.0.1:8000/docs`.

### 3. Test the Pipeline

A `test_client.py` script is provided to simulate an API client. While the server is running, open a new terminal and run:

```bash
python test_client.py
```

This script will:
1. Generate a dummy text file with a mix of original, plagiarized, and "AI-like" sentences.
2. Upload the file to the `/api/v1/upload` endpoint.
3. Receive a `job_id`.
4. Poll the `/api/v1/status/{job_id}` endpoint until processing is done.
5. Fetch and print the final structured JSON report from `/api/v1/report/{job_id}`.

## 🔧 Future Improvements (Production Scale)

- **Database**: Swap `SQLite` with `PostgreSQL` by changing `DATABASE_URL` in `config.py`.
- **Message Broker**: For heavy concurrent workloads, move the background tasks from FastAPI's native `BackgroundTasks` to **Celery + Redis/RabbitMQ**.
- **External Corpora**: Hook up the Plagiarism detector to an external web-search API (e.g., Google Custom Search / Bing Search API) or an ElasticSearch vector database holding actual academic papers.
- **Frontend Integration**: Build a React/Next.js dashboard that visualizes the `flagged_sections` JSON output with highlighted text over the document.
