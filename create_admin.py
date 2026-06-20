"""
Uso:
    python create_admin.py
    python create_admin.py --email admin@umedic.com --nombre "Admin Principal" --password admin1234
"""
import asyncio
import argparse
import os

# Asegura que el .env se lea correctamente
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from src.core.database import engine, Base, SessionLocal
from src.core.security import get_password_hash
from src.models.user import User, UserRole
from sqlalchemy.future import select


async def crear_admin(email: str, nombre: str, password: str):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        # Verificar si ya existe
        result = await db.execute(select(User).where(User.email == email))
        existente = result.scalars().first()

        if existente:
            if existente.role == UserRole.ADMIN:
                print(f"\n[!] El usuario '{email}' ya es administrador.\n")
                return
            # Promover a admin si ya existe con otro rol
            existente.role = UserRole.ADMIN
            await db.commit()
            print(f"\n[OK] Usuario '{email}' promovido a administrador.\n")
            return

        # Crear nuevo usuario admin
        nuevo = User(
            email=email,
            full_name=nombre,
            hashed_password=get_password_hash(password),
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(nuevo)
        await db.commit()
        print(f"\n[OK] Administrador creado exitosamente.")
        print(f"     Correo   : {email}")
        print(f"     Nombre   : {nombre}")
        print(f"     Rol      : admin\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crear administrador del sistema UMEDIC")
    parser.add_argument("--email",    default="admin@umedic.com",   help="Correo del admin")
    parser.add_argument("--nombre",   default="Administrador",      help="Nombre completo")
    parser.add_argument("--password", default="Admin1234!",         help="Contraseña")
    args = parser.parse_args()

    asyncio.run(crear_admin(args.email, args.nombre, args.password))
