"""
main.py — FastAPI Application Entrypoint
Authenticity Validator of Academia
"""

import json
import uuid
import asyncio
import os
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, Depends, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from config import (
    API_TITLE, API_VERSION, API_DESCRIPTION, 
    UPLOAD_DIR, ALLOWED_EXTENSIONS, MAX_FILE_SIZE_BYTES, REPORT_DIR
)
from logger import get_logger
from database.db import init_db, get_db
from database.models import AnalysisJob

from input_handler.extractor import extractor
from preprocessing.cleaner import preprocessor
from plagiarism_module.detector import plagiarism_detector
from ai_detection_module.detector import ai_detector
from authorship_module.stylometry import authorship_validator
from scoring_engine.calculator import scoring_engine
from report_generator.generator import report_generator

from fastapi.responses import HTMLResponse
from fastapi import Request
from fastapi.templating import Jinja2Templates

log = get_logger(__name__)

app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION,
)

templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
async def startup_event():
    try:
        log.info("FORCING DB INIT...")
        await init_db()
        log.info("DB INIT SUCCESSFUL")
    except Exception as e:
        log.error(f"FATAL: Database failed to initialize: {e}")
        # We don't exit, but this will cause later requests to fail visibly

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/v1/health")
async def health_check():
    """Verify backend and filesystem health."""
    health = {
        "status": "online",
        "uploads_dir": UPLOAD_DIR.exists(),
        "reports_dir": REPORT_DIR.exists(),
        "writable": os.access(Path("."), os.W_OK)
    }
    return health

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.error(f"GLOBAL ERROR: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error", "detail": str(exc)}
    )

# ─── Background Processing Pipeline ────────────────────────────────

async def process_document(job_id: str, file_path: Path, db: AsyncSession):
    """
    Core pipeline execution.
    Runs asynchronously in the background so the API returns quickly.
    """
    log.info(f"Starting pipeline for job: {job_id}")
    
    # 1. Fetch job from DB
    result = await db.execute(select(AnalysisJob).where(AnalysisJob.job_id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        log.error(f"Job {job_id} not found in DB")
        return

    try:
        # Update status
        job.status = "running"
        await db.commit()

        # Offload blocking ML models and PDF generation to a worker thread
        def run_heavy_computation():
            raw_text = extractor.extract(file_path)
            prep_data = preprocessor.process(raw_text)
            
            if len(prep_data["sentences"]) < 5:
                raise ValueError("Document is too short for meaningful analysis (< 5 sentences).")
                
            plag = plagiarism_detector.analyse(prep_data["sentences"])
            ai = ai_detector.analyse(prep_data["sentences"])
            auth = authorship_validator.analyse(prep_data["sentences"])
            
            score = scoring_engine.calculate_authenticity(plag, ai, auth)
            
            report = report_generator.generate_json_report(
                job_id, job.filename, prep_data["word_count"],
                score, plag, ai, auth
            )
            
            pdf = REPORT_DIR / f"{job_id}.pdf"
            report_generator.generate_pdf_report(report, pdf)
            
            return prep_data, plag, ai, auth, score, report, pdf

        log.info(f"[{job_id}] Running heavy analysis in background thread...")
        prep_data, plag_res, ai_res, auth_res, score_data, report_data, pdf_path = await asyncio.to_thread(run_heavy_computation)
        
        job.word_count = prep_data["word_count"]

        # 7. Update DB with final results
        job.status = "done"
        job.authenticity_score = score_data["authenticity_score"]
        job.plagiarism_score = score_data["components"]["plagiarism_score"]
        job.ai_probability = score_data["components"]["ai_probability"]
        job.authorship_consistency = score_data["components"]["authorship_consistency"]
        job.report_json = json.dumps(report_data)
        job.report_pdf = str(pdf_path)
        from datetime import datetime
        job.completed_at = datetime.utcnow()
        
        await db.commit()
        log.info(f"Pipeline completed successfully for job: {job_id}")

    except Exception as e:
        log.exception(f"Pipeline failed for job {job_id}: {e}")
        job.status = "error"
        job.error_msg = str(e)
        await db.commit()
    finally:
        # Cleanup uploaded file if desired
        # if file_path.exists():
        #     file_path.unlink()
        pass


# ─── API Endpoints ────────────────────────────────────────────────

@app.post("/api/v1/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a document (.pdf, .docx, .txt) for authenticity analysis.
    Returns a Job ID to poll for results.
    """
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: {ALLOWED_EXTENSIONS}")
    
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File size exceeds the 20MB limit.")

    job_id = str(uuid.uuid4())
    save_path = UPLOAD_DIR / f"{job_id}{ext}"
    
    with open(save_path, "wb") as buffer:
        buffer.write(await file.read())

    # Create DB record
    try:
        job = AnalysisJob(
            job_id=job_id,
            filename=file.filename,
            file_type=ext,
            status="pending"
        )
        db.add(job)
        await db.commit()
    except Exception as e:
        log.error(f"DB Error during upload: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    # Dispatch background task
    # Note: we need a separate session for the background task
    from database.db import AsyncSessionLocal
    async def run_pipeline_with_session():
        async with AsyncSessionLocal() as session:
            await process_document(job_id, save_path, session)

    background_tasks.add_task(run_pipeline_with_session)

    return JSONResponse(status_code=202, content={
        "message": "File uploaded successfully and analysis started.",
        "job_id": job_id
    })


@app.get("/api/v1/status/{job_id}")
async def get_status(job_id: str, db: AsyncSession = Depends(get_db)):
    """Check the status of an analysis job."""
    result = await db.execute(select(AnalysisJob).where(AnalysisJob.job_id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job.to_dict()


@app.get("/api/v1/report/{job_id}")
async def get_report(job_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve the full JSON report for a completed job."""
    result = await db.execute(select(AnalysisJob).where(AnalysisJob.job_id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    if job.status != "done":
        raise HTTPException(status_code=400, detail=f"Report not ready. Status: {job.status}")

    return json.loads(job.report_json)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
