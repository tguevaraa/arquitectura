from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List

from src.core.database import get_db
from src.core.security import get_password_hash
from src.api.auth import get_current_user
from src.models.user import User, UserRole
from src.models.doctor import Doctor
from src.schemas import UserResponse, UserAdminUpdate, PasswordReset, DoctorFullCreate, DoctorResponse
from src.services import auth_service

router = APIRouter(prefix="/admin", tags=["admin"])


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Acceso restringido a administradores.")
    return current_user


# ── Usuarios ──────────────────────────────────────────────────

@router.get("/users", response_model=List[UserResponse])
async def listar_usuarios(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    result = await db.execute(select(User).order_by(User.id))
    return result.scalars().all()


@router.patch("/users/{user_id}", response_model=UserResponse)
async def actualizar_usuario(
    user_id: int,
    data: UserAdminUpdate,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(require_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    if user.id == current.id:
        raise HTTPException(status_code=400, detail="No puede modificar su propia cuenta desde aquí.")

    if data.role is not None:
        user.role = data.role
    if data.is_active is not None:
        user.is_active = data.is_active

    await db.commit()
    await db.refresh(user)
    return user


@router.post("/users/{user_id}/reset-password")
async def cambiar_contrasena(
    user_id: int,
    data: PasswordReset,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    if not data.new_password or len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 6 caracteres.")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    user.hashed_password = get_password_hash(data.new_password)
    await db.commit()
    return {"message": f"Contraseña de '{user.full_name}' actualizada correctamente."}


# ── Médicos ───────────────────────────────────────────────────

@router.post("/doctors", response_model=DoctorResponse)
async def crear_medico(
    data: DoctorFullCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Crea el usuario con rol 'doctor' y su perfil médico en un solo paso."""
    from src.schemas import UserCreate

    # Verificar que el correo no exista
    existente = await auth_service.get_user_by_email(db, data.email)
    if existente:
        raise HTTPException(status_code=400, detail="Ya existe un usuario con ese correo.")

    # Crear usuario
    user_data = UserCreate(
        email=data.email,
        password=data.password,
        full_name=data.full_name,
        role=UserRole.DOCTOR,
    )
    user = await auth_service.create_user(db, user_data)

    # Crear perfil de médico
    doctor = Doctor(user_id=user.id, specialty=data.specialty, bio=data.bio)
    db.add(doctor)
    await db.commit()
    await db.refresh(doctor)  # recarga el id antes de usarlo en la siguiente query

    # Cargar relación para la respuesta
    result = await db.execute(
        select(Doctor).where(Doctor.id == doctor.id).options(selectinload(Doctor.user))
    )
    return result.scalars().first()
