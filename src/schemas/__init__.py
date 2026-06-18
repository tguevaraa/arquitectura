from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime
from src.models.user import UserRole
from src.models.appointment import AppointmentStatus

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole = UserRole.PATIENT

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    model_config = ConfigDict(from_attributes=True)

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[UserRole] = None

# Doctor Schemas
class DoctorBase(BaseModel):
    specialty: str
    bio: Optional[str] = None

class DoctorCreate(DoctorBase):
    user_id: int

class DoctorResponse(DoctorBase):
    id: int
    user: UserResponse
    model_config = ConfigDict(from_attributes=True)

# Appointment Schemas
class AppointmentBase(BaseModel):
    doctor_id: int
    appointment_datetime: datetime
    notes: Optional[str] = None

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentUpdate(BaseModel):
    status: Optional[AppointmentStatus] = None
    notes: Optional[str] = None

class AppointmentResponse(AppointmentBase):
    id: int
    patient_id: int
    status: AppointmentStatus
    model_config = ConfigDict(from_attributes=True)
