from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api import auth, doctors, appointments, analytics
from src.core.database import Base, engine

app = FastAPI(title="Medical Appointment Management System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:3000", "http://localhost:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(doctors.router)
app.include_router(appointments.router)
app.include_router(analytics.router)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/")
async def root():
    return {"message": "Welcome to the Medical Appointment Management System API"}
