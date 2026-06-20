from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from src.models.user import UserRole
from src.models.appointment import AppointmentStatus

# ── User Schemas ────────────────────────────────────────────
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

# ── Token Schemas ────────────────────────────────────────────
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[UserRole] = None

# ── Doctor Schemas ───────────────────────────────────────────
class DoctorBase(BaseModel):
    specialty: str
    bio: Optional[str] = None

class DoctorCreate(DoctorBase):
    user_id: int

class DoctorResponse(DoctorBase):
    id: int
    user: UserResponse
    model_config = ConfigDict(from_attributes=True)

# ── Appointment Schemas ──────────────────────────────────────
class AppointmentBase(BaseModel):
    doctor_id: int
    appointment_datetime: datetime
    notes: Optional[str] = None

class AppointmentCreate(AppointmentBase):
    patient_id: Optional[int] = None   # Staff puede especificar el paciente

class AppointmentUpdate(BaseModel):
    status: Optional[AppointmentStatus] = None
    notes: Optional[str] = None

class AppointmentResponse(AppointmentBase):
    id: int
    patient_id: int
    status: AppointmentStatus
    patient_full_name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

# ── Auth de paciente con verificación de correo ──────────────
class SendCodeRequest(BaseModel):
    email: EmailStr
    password: str

class VerifyCodeRequest(BaseModel):
    email: EmailStr
    code: str

# ── Reagendar cita ───────────────────────────────────────────
class RescheduleRequest(BaseModel):
    new_datetime: datetime

# ── Admin — gestión de usuarios ──────────────────────────────
class UserAdminUpdate(BaseModel):
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

class PasswordReset(BaseModel):
    new_password: str

# ── Admin — crear médico completo (usuario + perfil) ─────────
class DoctorFullCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    specialty: str
    bio: Optional[str] = None

# ── Perfil de Paciente ───────────────────────────────────────
class PatientProfileBase(BaseModel):
    cedula: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    sexo: Optional[str] = None
    telefono: Optional[str] = None
    tipo_seguro: Optional[str] = None
    grupo_sanguineo: Optional[str] = None
    direccion: Optional[str] = None
    ciudad: Optional[str] = None
    ocupacion: Optional[str] = None
    empresa: Optional[str] = None
    hc_numero: Optional[str] = None

class PatientProfileCreate(PatientProfileBase):
    pass

class PatientProfileResponse(PatientProfileBase):
    id: int
    user_id: int
    user: UserResponse
    model_config = ConfigDict(from_attributes=True)

# ── Crear paciente completo (usuario + perfil) ───────────────
class PatientFullCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    cedula: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    sexo: Optional[str] = None
    telefono: Optional[str] = None
    tipo_seguro: Optional[str] = None
    grupo_sanguineo: Optional[str] = None

# ── Historia Clínica: Consulta ───────────────────────────────
class ConsultaRecordCreate(BaseModel):
    motivo: str
    diagnostico: Optional[str] = None
    tratamiento: Optional[str] = None
    examenes_lab: Optional[str] = None
    tipo_imagen: Optional[str] = None
    observaciones_imagen: Optional[str] = None
    appointment_id: Optional[int] = None

class DocumentoResponse(BaseModel):
    id: int
    consulta_id: int
    patient_id: int
    tipo: str
    nombre_archivo: str
    drive_file_id: Optional[str] = None
    drive_url: Optional[str] = None
    subido_por: Optional[int] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ConsultaRecordResponse(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    appointment_id: Optional[int] = None
    motivo: str
    diagnostico: Optional[str] = None
    tratamiento: Optional[str] = None
    examenes_lab: Optional[str] = None
    tipo_imagen: Optional[str] = None
    observaciones_imagen: Optional[str] = None
    fecha_consulta: datetime
    created_at: datetime
    documentos: List[DocumentoResponse] = []
    doctor_name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)
