from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from datetime import datetime, timedelta
from src.models.appointment import Appointment, AppointmentStatus
from src.schemas import AppointmentCreate, AppointmentUpdate, AppointmentResponse


def _verificar_24h(appointment_datetime: datetime) -> None:
    """Lanza 400 si la cita es en menos de 24 horas."""
    # MySQL devuelve datetime naive (UTC); usamos utcnow() para comparar consistentemente
    ahora = datetime.utcnow()
    appt  = appointment_datetime.replace(tzinfo=None) if appointment_datetime.tzinfo else appointment_datetime
    horas_restantes = (appt - ahora).total_seconds() / 3600
    if horas_restantes < 24:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo puede cancelar o reagendar con al menos 24 horas de anticipación."
        )

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
    ).with_for_update()
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
        query = select(Appointment).options(selectinload(Appointment.patient))
    elif role == "doctor":
        from src.models.doctor import Doctor
        doctor_res = await db.execute(select(Doctor).where(Doctor.user_id == user_id))
        doctor = doctor_res.scalars().first()
        if not doctor:
            return []
        query = select(Appointment).where(Appointment.doctor_id == doctor.id).options(
            selectinload(Appointment.patient)
        )
    else:
        query = select(Appointment).where(Appointment.patient_id == user_id).options(
            selectinload(Appointment.patient)
        )

    result = await db.execute(query)
    appointments = result.scalars().all()

    responses = []
    for appt in appointments:
        r = AppointmentResponse(
            id=appt.id,
            patient_id=appt.patient_id,
            doctor_id=appt.doctor_id,
            appointment_datetime=appt.appointment_datetime,
            status=appt.status,
            notes=appt.notes,
            patient_full_name=appt.patient.full_name if appt.patient else None,
        )
        responses.append(r)
    return responses

async def update_appointment_status(db: AsyncSession, appointment_id: int, update_data: AppointmentUpdate, user_id: int, role: str):
    query = select(Appointment).where(Appointment.id == appointment_id)
    result = await db.execute(query)
    db_appointment = result.scalars().first()
    
    if not db_appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Permissions check
    if role == "patient" and db_appointment.patient_id != user_id:
        raise HTTPException(status_code=403, detail="No autorizado.")
    # Pacientes solo pueden modificar con 24h de anticipación
    if role == "patient":
        _verificar_24h(db_appointment.appointment_datetime)
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


async def reschedule_appointment(db: AsyncSession, appointment_id: int, new_datetime: datetime, patient_id: int):
    """Reagenda una cita existente respetando la regla de 24h y validando colisiones."""
    result = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
    appt = result.scalars().first()

    if not appt:
        raise HTTPException(status_code=404, detail="Cita no encontrada.")
    if appt.patient_id != patient_id:
        raise HTTPException(status_code=403, detail="No autorizado.")
    if appt.status == AppointmentStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="No se puede reagendar una cita cancelada.")

    # Regla de 24h sobre la cita ACTUAL
    _verificar_24h(appt.appointment_datetime)

    # Verificar colisión en el nuevo horario (ignorando la cita actual)
    colision = await check_appointment_collision(db, appt.doctor_id, new_datetime)
    if colision and colision.id != appointment_id:
        raise HTTPException(
            status_code=400,
            detail="El médico ya tiene una cita en ese horario o cerca de él."
        )

    appt.appointment_datetime = new_datetime
    appt.status = AppointmentStatus.SCHEDULED
    await db.commit()
    await db.refresh(appt)
    return appt
