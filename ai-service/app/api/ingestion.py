from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from app.ingestion.indexing import IngestionPipeline
from app.ingestion.detector import DocumentMetadataDetector

router = APIRouter(prefix="/internal/documents", tags=["Ingestion"])
pipeline = IngestionPipeline()
detector = DocumentMetadataDetector()


class ProcessDocumentRequest(BaseModel):
    file_path: str = Field(..., description="Absolute or relative path to PDF")
    company_id: str
    fiscal_year: int
    document_id: Optional[str] = None
    period_type: str = "FY"
    document_type: str = "annual_report"


class DetectDocumentRequest(BaseModel):
    file_path: str = Field(..., description="Absolute or relative path to PDF")
    original_filename: Optional[str] = None
    known_companies: Optional[list] = None


@router.post("/process")
def process_document(req: ProcessDocumentRequest) -> Dict[str, Any]:
    try:
        result = pipeline.process_document(
            file_path=req.file_path,
            company_id=req.company_id,
            fiscal_year=req.fiscal_year,
            document_id=req.document_id,
            period_type=req.period_type,
            document_type=req.document_type,
        )
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.post("/detect")
def detect_document(req: DetectDocumentRequest) -> Dict[str, Any]:
    try:
        result = detector.detect_metadata(
            file_path=req.file_path,
            original_filename=req.original_filename,
            known_companies=req.known_companies,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")

