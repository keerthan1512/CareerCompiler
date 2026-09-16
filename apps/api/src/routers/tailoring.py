from typing import Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel, Field

from ..database import get_db
from ..models.tailoring_plan import TailoringPlan
from ..celery_app import task_generate_tailoring_plan

router = APIRouter(prefix="/tailoring-plans", tags=["Tailoring Plans"])

class CreateTailoringPlanRequest(BaseModel):
    job_id: UUID
    master_resume_id: UUID
    mode: str = "review"

class UpdatePlanItem(BaseModel):
    id: UUID
    status: str = Field(..., description="approved, rejected, edited")
    user_edited_text: Optional[str] = None

class UpdateTailoringPlanRequest(BaseModel):
    items: List[UpdatePlanItem]

@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def create_tailoring_plan(
    req: CreateTailoringPlanRequest,
    session: AsyncSession = Depends(get_db),
    x_dev_user_id: Optional[str] = Header(None, alias="X-Dev-User-Id"),
):
    plan = TailoringPlan(
        job_id=req.job_id,
        master_resume_id=req.master_resume_id,
        mode=req.mode,
        status="pending"
    )
    session.add(plan)
    await session.commit()
    await session.refresh(plan)
    
    # Trigger background task
    task_generate_tailoring_plan.delay(str(plan.id))
    
    return {
        "id": plan.id,
        "status": plan.status
    }

@router.get("/{plan_id}")
async def get_tailoring_plan(
    plan_id: UUID,
    session: AsyncSession = Depends(get_db),
    x_dev_user_id: Optional[str] = Header(None, alias="X-Dev-User-Id"),
):
    plan = await session.get(TailoringPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Tailoring plan not found")
        
    return {
        "id": plan.id,
        "job_id": plan.job_id,
        "master_resume_id": plan.master_resume_id,
        "status": plan.status,
        "items": plan.items,
        "metadata": plan.metadata_obj,
        "created_at": plan.created_at,
        "updated_at": plan.updated_at
    }

@router.put("/{plan_id}/items")
async def update_tailoring_plan_items(
    plan_id: UUID,
    req: UpdateTailoringPlanRequest,
    session: AsyncSession = Depends(get_db),
    x_dev_user_id: Optional[str] = Header(None, alias="X-Dev-User-Id"),
):
    plan = await session.get(TailoringPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Tailoring plan not found")
        
    if not plan.items:
        raise HTTPException(status_code=400, detail="Plan has no items yet")
        
    update_map = {str(item.id): item for item in req.items}
    
    updated = False
    for item in plan.items:
        if item.get("id") in update_map:
            update_req = update_map[item["id"]]
            item["status"] = update_req.status
            if update_req.user_edited_text is not None:
                item["user_edited_text"] = update_req.user_edited_text
            updated = True
            
    if updated:
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(plan, "items")
        await session.commit()
        await session.refresh(plan)
        
    return {"status": "success", "message": "Items updated"}
