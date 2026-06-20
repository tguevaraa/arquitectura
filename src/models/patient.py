from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey
from sqlalchemy.orm import relationship
from src.core.database import Base


class PatientProfile(Base):
    __tablename__ = "patient_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    cedula = Column(String(20), nullable=True)
    fecha_nacimiento = Column(Date, nullable=True)
    sexo = Column(String(1), nullable=True)           # M / F
    telefono = Column(String(20), nullable=True)
    tipo_seguro = Column(String(10), nullable=True)   # AG / SG / SV
    grupo_sanguineo = Column(String(5), nullable=True)
    direccion = Column(Text, nullable=True)
    ciudad = Column(String(100), nullable=True)
    ocupacion = Column(String(100), nullable=True)
    empresa = Column(String(100), nullable=True)
    hc_numero = Column(String(50), nullable=True)

    user = relationship("User", back_populates="patient_profile")
