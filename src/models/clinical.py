from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from src.core.database import Base


class ConsultaRecord(Base):
    __tablename__ = "consulta_records"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    motivo = Column(Text, nullable=False)
    diagnostico = Column(Text, nullable=True)
    tratamiento = Column(Text, nullable=True)
    examenes_lab = Column(Text, nullable=True)
    tipo_imagen = Column(String(20), nullable=True)    # rx / eco / ekg / none
    observaciones_imagen = Column(Text, nullable=True)
    fecha_consulta = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    documentos = relationship("Documento", back_populates="consulta", cascade="all, delete-orphan")


class Documento(Base):
    __tablename__ = "documentos"

    id = Column(Integer, primary_key=True, index=True)
    consulta_id = Column(Integer, ForeignKey("consulta_records.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # historia_clinica / orden_lab / orden_imagen / resultado_lab / resultado_imagen
    tipo = Column(String(30), nullable=False)
    nombre_archivo = Column(String(255), nullable=False)
    drive_file_id = Column(String(255), nullable=True)
    drive_url = Column(String(500), nullable=True)
    subido_por = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    consulta = relationship("ConsultaRecord", back_populates="documentos")
