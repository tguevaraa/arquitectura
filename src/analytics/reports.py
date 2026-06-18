import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.models.appointment import Appointment
from src.models.doctor import Doctor
from src.models.user import User

async def get_appointment_report(db: AsyncSession):
    # Fetch all data needed for the report
    query = select(
        Appointment.appointment_datetime,
        Appointment.status,
        Doctor.specialty,
        User.full_name.label("doctor_name")
    ).join(Doctor, Appointment.doctor_id == Doctor.id).join(User, Doctor.user_id == User.id)
    
    result = await db.execute(query)
    data = result.all()
    
    if not data:
        return {"message": "No data available"}

    # Create DataFrame
    df = pd.DataFrame(data, columns=["datetime", "status", "specialty", "doctor_name"])
    
    # Process data
    df['date'] = pd.to_datetime(df['datetime']).dt.date
    
    # Aggregations
    appointments_by_specialty = df.groupby('specialty').size().to_dict()
    appointments_by_status = df.groupby('status').size().to_dict()
    appointments_per_day = df.groupby('date').size().to_dict()
    
    # Convert date keys to strings for JSON serialization
    appointments_per_day = {str(k): v for k, v in appointments_per_day.items()}

    return {
        "summary": {
            "total_appointments": len(df),
            "by_specialty": appointments_by_specialty,
            "by_status": appointments_by_status,
            "per_day": appointments_per_day
        }
    }

async def export_to_csv(db: AsyncSession):
    query = select(Appointment)
    result = await db.execute(query)
    appointments = result.scalars().all()
    
    if not appointments:
        return ""
    
    # Simple export
    data = [{
        "id": a.id,
        "doctor_id": a.doctor_id,
        "patient_id": a.patient_id,
        "datetime": a.appointment_datetime,
        "status": a.status
    } for a in appointments]
    
    df = pd.DataFrame(data)
    return df.to_csv(index=False)
