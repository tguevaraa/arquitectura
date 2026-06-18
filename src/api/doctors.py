from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from src.core.database import get_db
from src.schemas import DoctorResponse, DoctorCreate
from src.services import doctor_service
from src.api.auth import get_current_user
from src.models.user import User, UserRole

router = APIRouter(prefix="/doctors", tags=["doctors"])

@router.get("/", response_model=List[DoctorResponse])
async def list_doctors(db: AsyncSession = Depends(get_db)):
    return await doctor_service.get_all_doctors(db)

@router.post("/", response_model=DoctorResponse)
async def create_doctor(
    doctor: DoctorCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can create doctor profiles")
    return await doctor_service.create_doctor_profile(db, doctor)
