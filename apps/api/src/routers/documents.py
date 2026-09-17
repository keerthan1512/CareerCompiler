import uuid
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..database import get_db
from ..models import CompiledResume, TailoringPlan, User
from ..routers.auth import get_current_user
from ..celery_app import task_compile_latex

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/compile", status_code=202)
async def compile_document(
    tailoring_plan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    FR-014, FR-015: Triggers a sandboxed compilation task for a given tailoring plan.
    """
    plan = await db.get(TailoringPlan, tailoring_plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="TailoringPlan not found")
        
    doc = CompiledResume(
        tailoring_plan_id=tailoring_plan_id,
        user_id=str(user.id),
        latex_content="", # populated by task
        status="pending"
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    
    # Trigger background task
    task_compile_latex.delay(str(doc.id))
    
    return {"id": str(doc.id), "status": doc.status}

@router.get("/{document_id}")
async def get_document_status(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Poll compilation status and validation results.
    """
    doc = await db.get(CompiledResume, document_id)
    if not doc or doc.user_id != str(user.id):
        raise HTTPException(status_code=404, detail="Document not found")
        
    return {
        "id": str(doc.id),
        "status": doc.status,
        "validation_results": doc.validation_results
    }

@router.get("/{document_id}/download")
async def download_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Download the compiled PDF file.
    """
    doc = await db.get(CompiledResume, document_id)
    if not doc or doc.user_id != str(user.id):
        raise HTTPException(status_code=404, detail="Document not found")
        
    if doc.status != "complete" or not doc.pdf_file_path:
        raise HTTPException(status_code=400, detail="Document is not complete")
        
    return FileResponse(
        path=doc.pdf_file_path,
        media_type="application/pdf",
        filename="tailored_resume.pdf"
    )
