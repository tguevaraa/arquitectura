from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from src.models.doctor import Doctor
from src.models.user import User, UserRole
from src.schemas import DoctorCreate

async def get_all_doctors(db: AsyncSession):
    result = await db.execute(select(Doctor).join(User))
    return result.scalars().all()

async def create_doctor_profile(db: AsyncSession, doctor_data: DoctorCreate):
    # Check if user exists and is a doctor
    user_query = await db.execute(select(User).where(User.id == doctor_data.user_id))
    user = user_query.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role != UserRole.DOCTOR:
        raise HTTPException(status_code=400, detail="User must have 'doctor' role")
    
    # Check if profile already exists
    existing_profile = await db.execute(select(Doctor).where(Doctor.user_id == doctor_data.user_id))
    if existing_profile.scalars().first():
        raise HTTPException(status_code=400, detail="Doctor profile already exists")
    
    new_doctor = Doctor(
        user_id=doctor_data.user_id,
        specialty=doctor_data.specialty,
        bio=doctor_data.bio
    )
    db.add(new_doctor)
    await db.commit()
    await db.refresh(new_doctor)
    return new_doctor
