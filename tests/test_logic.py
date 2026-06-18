import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta
from src.services.appointment_service import check_appointment_collision
from src.models.appointment import Appointment, AppointmentStatus
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_appointment_collision():
    db_session = AsyncMock(spec=AsyncSession)
    
    # Mock the return value of db_session.execute().scalars().first()
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = Appointment(id=1, doctor_id=1, appointment_datetime=datetime(2026, 6, 15, 10, 0))
    mock_result.scalars.return_value = mock_scalars
    db_session.execute.return_value = mock_result

    doctor_id = 1
    base_time = datetime(2026, 6, 15, 10, 0)
    
    # Call the service function
    collision = await check_appointment_collision(db_session, doctor_id, base_time)
    
    # Verify the collision is detected
    assert collision is not None
    assert collision.doctor_id == 1
    db_session.execute.assert_called_once()

@pytest.mark.asyncio
async def test_appointment_no_collision():
    db_session = AsyncMock(spec=AsyncSession)
    
    # Mock the return value of db_session.execute().scalars().first() -> None for no collision
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = None
    mock_result.scalars.return_value = mock_scalars
    db_session.execute.return_value = mock_result

    doctor_id = 1
    base_time = datetime(2026, 6, 15, 10, 0)
    
    # Call the service function
    collision = await check_appointment_collision(db_session, doctor_id, base_time)
    
    # Verify no collision
    assert collision is None
    db_session.execute.assert_called_once()
