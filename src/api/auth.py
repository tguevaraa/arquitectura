from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from src.core.database import get_db
from src.core.config import settings
from src.core.security import create_access_token
from src.core.email import generar_codigo, guardar_codigo, verificar_codigo, enviar_codigo
from src.schemas import UserCreate, UserResponse, Token, TokenData, SendCodeRequest, VerifyCodeRequest
from src.services import auth_service
from src.models.user import User, UserRole

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = await auth_service.get_user_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    return await auth_service.create_user(db, user)

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await auth_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/patient-login")
async def patient_login(payload: SendCodeRequest, db: AsyncSession = Depends(get_db)):
    """Valida credenciales del paciente y envía código de verificación al correo."""
    user = await auth_service.authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos.")
    if user.role != UserRole.PATIENT:
        raise HTTPException(status_code=403, detail="Acceso restringido a pacientes.")

    code = generar_codigo()
    guardar_codigo(payload.email, code)
    await enviar_codigo(payload.email, code)
    return {"message": "Código de verificación enviado a su correo electrónico."}


@router.post("/verify-code", response_model=Token)
async def verify_code(payload: VerifyCodeRequest, db: AsyncSession = Depends(get_db)):
    """Verifica el código de 6 dígitos y devuelve el JWT de acceso."""
    resultado = verificar_codigo(payload.email, payload.code)
    if resultado is None:
        raise HTTPException(status_code=400, detail="No hay un código activo para este correo.")
    if resultado == "expired":
        raise HTTPException(status_code=400, detail="El código ha expirado. Solicite uno nuevo.")
    if resultado is False:
        raise HTTPException(status_code=400, detail="Código incorrecto.")

    user = await auth_service.get_user_by_email(db, payload.email)
    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}
