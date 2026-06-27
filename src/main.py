from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from src.api import auth, doctors, appointments, analytics, admin
from src.api import patients
from src.core.database import Base, engine
# Importar todos los modelos para que Base.metadata los registre al iniciar
import src.models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="Medical Appointment Management System", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:3000", "http://localhost:5500", "http://localhost:8000", "null", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(doctors.router)
app.include_router(appointments.router)
app.include_router(analytics.router)
app.include_router(admin.router)
app.include_router(patients.router)

@app.get("/api")
async def root():
    return {"message": "Welcome to the Medical Appointment Management System API"}

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
