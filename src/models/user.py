from sqlalchemy import Boolean, Column, Integer, String, Enum as SqlEnum
from sqlalchemy.orm import relationship
import enum
from src.core.database import Base

class UserRole(str, enum.Enum):
    PATIENT = "patient"
    DOCTOR = "doctor"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(SqlEnum(UserRole), default=UserRole.PATIENT)
    is_active = Column(Boolean, default=True)

    doctor_profile = relationship("Doctor", back_populates="user", uselist=False)
    patient_profile = relationship("PatientProfile", back_populates="user", uselist=False)
    appointments = relationship("Appointment", back_populates="patient")
