from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
import mimetypes

from src.core.database import get_db
from src.core.security import get_password_hash
from src.api.auth import get_current_user
from src.models.user import User, UserRole
from src.models.patient import PatientProfile
from src.models.clinical import ConsultaRecord, Documento
from src.models.doctor import Doctor
from src.schemas import (
    PatientProfileResponse,
    PatientProfileCreate,
    PatientFullCreate,
    ConsultaRecordCreate,
    ConsultaRecordResponse,
    DocumentoResponse,
    UserCreate,
)
from src.services import auth_service
from src.services.drive_service import subir_archivo

router = APIRouter(prefix="/patients", tags=["patients"])


def _require_staff(current_user: User):
    if current_user.role == UserRole.PATIENT:
        raise HTTPException(status_code=403, detail="Acceso restringido al personal médico.")
    return current_user


# ── Pacientes ──────────────────────────────────────────────────

@router.get("/", response_model=List[PatientProfileResponse])
async def listar_pacientes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_staff(current_user)
    result = await db.execute(
        select(PatientProfile).options(selectinload(PatientProfile.user)).order_by(PatientProfile.id)
    )
    return result.scalars().all()


@router.post("/", response_model=PatientProfileResponse)
async def crear_paciente(
    data: PatientFullCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Crea el usuario con rol 'paciente' y su perfil en un solo paso."""
    _require_staff(current_user)

    existente = await auth_service.get_user_by_email(db, data.email)
    if existente:
        raise HTTPException(status_code=400, detail="Ya existe un usuario con ese correo.")

    user_data = UserCreate(
        email=data.email,
        password=data.password,
        full_name=data.full_name,
        role=UserRole.PATIENT,
    )
    user = await auth_service.create_user(db, user_data)

    profile = PatientProfile(
        user_id=user.id,
        cedula=data.cedula,
        fecha_nacimiento=data.fecha_nacimiento,
        sexo=data.sexo,
        telefono=data.telefono,
        tipo_seguro=data.tipo_seguro,
        grupo_sanguineo=data.grupo_sanguineo,
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)

    result = await db.execute(
        select(PatientProfile)
        .where(PatientProfile.id == profile.id)
        .options(selectinload(PatientProfile.user))
    )
    return result.scalars().first()


@router.get("/{patient_id}", response_model=PatientProfileResponse)
async def obtener_paciente(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # El propio paciente puede ver su perfil; el personal también
    if current_user.role == UserRole.PATIENT and current_user.id != patient_id:
        raise HTTPException(status_code=403, detail="No autorizado.")

    result = await db.execute(
        select(PatientProfile)
        .where(PatientProfile.user_id == patient_id)
        .options(selectinload(PatientProfile.user))
    )
    profile = result.scalars().first()
    if not profile:
        # Crear perfil vacío si el usuario existe pero no tiene perfil
        user_res = await db.execute(select(User).where(User.id == patient_id))
        user = user_res.scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail="Paciente no encontrado.")
        profile = PatientProfile(user_id=patient_id)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
        result2 = await db.execute(
            select(PatientProfile)
            .where(PatientProfile.id == profile.id)
            .options(selectinload(PatientProfile.user))
        )
        return result2.scalars().first()
    return profile


@router.put("/{patient_id}", response_model=PatientProfileResponse)
async def actualizar_paciente(
    patient_id: int,
    data: PatientProfileCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.PATIENT and current_user.id != patient_id:
        raise HTTPException(status_code=403, detail="No autorizado.")

    result = await db.execute(
        select(PatientProfile).where(PatientProfile.user_id == patient_id)
    )
    profile = result.scalars().first()
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil no encontrado.")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(profile, field, value)

    await db.commit()
    await db.refresh(profile)

    result2 = await db.execute(
        select(PatientProfile)
        .where(PatientProfile.id == profile.id)
        .options(selectinload(PatientProfile.user))
    )
    return result2.scalars().first()


# ── Consultas clínicas ─────────────────────────────────────────

@router.get("/{patient_id}/consultas", response_model=List[ConsultaRecordResponse])
async def listar_consultas(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.PATIENT and current_user.id != patient_id:
        raise HTTPException(status_code=403, detail="No autorizado.")

    result = await db.execute(
        select(ConsultaRecord)
        .where(ConsultaRecord.patient_id == patient_id)
        .options(selectinload(ConsultaRecord.documentos))
        .order_by(ConsultaRecord.fecha_consulta.desc())
    )
    consultas = result.scalars().all()

    # Enriquecer con nombre del médico
    responses = []
    for c in consultas:
        doc_res = await db.execute(
            select(Doctor).where(Doctor.id == c.doctor_id).options(selectinload(Doctor.user))
        )
        doctor = doc_res.scalars().first()
        cr = ConsultaRecordResponse(
            id=c.id,
            patient_id=c.patient_id,
            doctor_id=c.doctor_id,
            appointment_id=c.appointment_id,
            motivo=c.motivo,
            diagnostico=c.diagnostico,
            tratamiento=c.tratamiento,
            examenes_lab=c.examenes_lab,
            tipo_imagen=c.tipo_imagen,
            observaciones_imagen=c.observaciones_imagen,
            fecha_consulta=c.fecha_consulta,
            created_at=c.created_at,
            documentos=c.documentos,
            doctor_name=doctor.user.full_name if doctor and doctor.user else None,
        )
        responses.append(cr)
    return responses


@router.post("/{patient_id}/consultas", response_model=ConsultaRecordResponse)
async def crear_consulta(
    patient_id: int,
    data: ConsultaRecordCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_staff(current_user)

    # Verificar que el paciente existe
    user_res = await db.execute(select(User).where(User.id == patient_id))
    if not user_res.scalars().first():
        raise HTTPException(status_code=404, detail="Paciente no encontrado.")

    # Obtener doctor_id del médico logueado (si es doctor), sino doctor_id=1 como fallback
    if current_user.role == UserRole.DOCTOR:
        doc_res = await db.execute(select(Doctor).where(Doctor.user_id == current_user.id))
        doctor = doc_res.scalars().first()
        doctor_id = doctor.id if doctor else 1
    else:
        doctor_id = 1  # Admin crea consulta; se puede mejorar con un campo adicional

    consulta = ConsultaRecord(
        patient_id=patient_id,
        doctor_id=doctor_id,
        appointment_id=data.appointment_id,
        motivo=data.motivo,
        diagnostico=data.diagnostico,
        tratamiento=data.tratamiento,
        examenes_lab=data.examenes_lab,
        tipo_imagen=data.tipo_imagen,
        observaciones_imagen=data.observaciones_imagen,
    )
    db.add(consulta)
    await db.commit()
    await db.refresh(consulta)

    doc_res = await db.execute(
        select(Doctor).where(Doctor.id == consulta.doctor_id).options(selectinload(Doctor.user))
    )
    doctor = doc_res.scalars().first()

    return ConsultaRecordResponse(
        id=consulta.id,
        patient_id=consulta.patient_id,
        doctor_id=consulta.doctor_id,
        appointment_id=consulta.appointment_id,
        motivo=consulta.motivo,
        diagnostico=consulta.diagnostico,
        tratamiento=consulta.tratamiento,
        examenes_lab=consulta.examenes_lab,
        tipo_imagen=consulta.tipo_imagen,
        observaciones_imagen=consulta.observaciones_imagen,
        fecha_consulta=consulta.fecha_consulta,
        created_at=consulta.created_at,
        documentos=[],
        doctor_name=doctor.user.full_name if doctor and doctor.user else None,
    )


# ── Documentos ─────────────────────────────────────────────────

@router.post("/{patient_id}/consultas/{consulta_id}/documentos", response_model=DocumentoResponse)
async def subir_documento(
    patient_id: int,
    consulta_id: int,
    tipo: str = Form(...),
    archivo: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_staff(current_user)

    # Verificar que la consulta existe y pertenece al paciente
    result = await db.execute(
        select(ConsultaRecord).where(
            ConsultaRecord.id == consulta_id,
            ConsultaRecord.patient_id == patient_id,
        )
    )
    consulta = result.scalars().first()
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta no encontrada.")

    file_bytes = await archivo.read()
    mimetype = archivo.content_type or mimetypes.guess_type(archivo.filename)[0] or "application/octet-stream"

    drive_info = await subir_archivo(file_bytes, archivo.filename, mimetype)

    doc = Documento(
        consulta_id=consulta_id,
        patient_id=patient_id,
        tipo=tipo,
        nombre_archivo=archivo.filename,
        drive_file_id=drive_info["drive_file_id"],
        drive_url=drive_info["drive_url"],
        subido_por=current_user.id,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc


@router.get("/{patient_id}/documentos", response_model=List[DocumentoResponse])
async def listar_documentos(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.PATIENT and current_user.id != patient_id:
        raise HTTPException(status_code=403, detail="No autorizado.")

    result = await db.execute(
        select(Documento)
        .where(Documento.patient_id == patient_id)
        .order_by(Documento.created_at.desc())
    )
    return result.scalars().all()
