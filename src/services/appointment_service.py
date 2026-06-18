from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from fastapi import HTTPException, status
from datetime import datetime, timedelta
from src.models.appointment import Appointment, AppointmentStatus
from src.schemas import AppointmentCreate, AppointmentUpdate

async def check_appointment_collision(db: AsyncSession, doctor_id: int, appointment_datetime: datetime):
    # Assume appointments are 30 minutes long for collision check
    start_time = appointment_datetime - timedelta(minutes=29)
    end_time = appointment_datetime + timedelta(minutes=29)
    
    query = select(Appointment).where(
        and_(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_datetime.between(start_time, end_time),
            Appointment.status != AppointmentStatus.CANCELLED
        )
    )
    result = await db.execute(query)
    return result.scalars().first()

async def create_appointment(db: AsyncSession, appointment: AppointmentCreate, patient_id: int):
    # Check for collisions
    collision = await check_appointment_collision(db, appointment.doctor_id, appointment.appointment_datetime)
    if collision:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Doctor is already booked at this time or near this time."
        )
    
    new_appointment = Appointment(
        patient_id=patient_id,
        doctor_id=appointment.doctor_id,
        appointment_datetime=appointment.appointment_datetime,
        notes=appointment.notes
    )
    db.add(new_appointment)
    await db.commit()
    await db.refresh(new_appointment)
    return new_appointment

async def get_appointments(db: AsyncSession, user_id: int, role: str):
    if role == "admin":
        query = select(Appointment)
    elif role == "doctor":
        # First get doctor id for this user
        from src.models.doctor import Doctor
        doctor_res = await db.execute(select(Doctor).where(Doctor.user_id == user_id))
        doctor = doctor_res.scalars().first()
        if not doctor:
            return []
        query = select(Appointment).where(Appointment.doctor_id == doctor.id)
    else:
        query = select(Appointment).where(Appointment.patient_id == user_id)
    
    result = await db.execute(query)
    return result.scalars().all()

async def update_appointment_status(db: AsyncSession, appointment_id: int, update_data: AppointmentUpdate, user_id: int, role: str):
    query = select(Appointment).where(Appointment.id == appointment_id)
    result = await db.execute(query)
    db_appointment = result.scalars().first()
    
    if not db_appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Permissions check
    if role == "patient" and db_appointment.patient_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    # Doctors can only update their own appointments
    if role == "doctor":
        from src.models.doctor import Doctor
        doctor_res = await db.execute(select(Doctor).where(Doctor.user_id == user_id))
        doctor = doctor_res.scalars().first()
        if not doctor or db_appointment.doctor_id != doctor.id:
            raise HTTPException(status_code=403, detail="Not authorized")

    if update_data.status:
        db_appointment.status = update_data.status
    if update_data.notes:
        db_appointment.notes = update_data.notes
        
    await db.commit()
    await db.refresh(db_appointment)
    return db_appointment
