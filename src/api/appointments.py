from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from src.core.database import get_db
from src.schemas import AppointmentCreate, AppointmentResponse, AppointmentUpdate, RescheduleRequest
from src.services import appointment_service
from src.api.auth import get_current_user
from src.models.user import User, UserRole

router = APIRouter(prefix="/appointments", tags=["appointments"])

@router.post("/", response_model=AppointmentResponse)
async def book_appointment(
    appointment: AppointmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Staff (admin/doctor) puede especificar patient_id; pacientes usan su propia cuenta
    if current_user.role == UserRole.PATIENT:
        patient_id = current_user.id
    else:
        patient_id = appointment.patient_id or current_user.id
    return await appointment_service.create_appointment(db, appointment, patient_id)

@router.get("/", response_model=List[AppointmentResponse])
async def list_appointments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await appointment_service.get_appointments(db, current_user.id, current_user.role)

@router.post("/{appointment_id}/reschedule", response_model=AppointmentResponse)
async def reschedule_appointment(
    appointment_id: int,
    data: RescheduleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.PATIENT:
        raise HTTPException(status_code=403, detail="Solo los pacientes pueden reagendar sus citas.")
    return await appointment_service.reschedule_appointment(
        db, appointment_id, data.new_datetime, current_user.id
    )


@router.patch("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: int,
    update_data: AppointmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await appointment_service.update_appointment_status(
        db, appointment_id, update_data, current_user.id, current_user.role
    )
