# Medical Appointment Management System Design

## 1. Database Schema (MySQL)

### Users Table
- `id` (INT, PK, AI)
- `email` (VARCHAR, UNIQUE, INDEX)
- `hashed_password` (VARCHAR)
- `full_name` (VARCHAR)
- `role` (ENUM: 'patient', 'doctor', 'admin')
- `is_active` (BOOLEAN)

### Doctors Table
- `id` (INT, PK, AI)
- `user_id` (INT, FK -> Users.id)
- `specialty` (VARCHAR)
- `bio` (TEXT)

### Appointments Table
- `id` (INT, PK, AI)
- `patient_id` (INT, FK -> Users.id)
- `doctor_id` (INT, FK -> Doctors.id)
- `appointment_datetime` (DATETIME, INDEX)
- `status` (ENUM: 'scheduled', 'completed', 'cancelled')
- `notes` (TEXT)

## 2. Key Features

### Concurrency Management
- Use database transactions with appropriate isolation levels (Repeatable Read) to prevent double-booking.
- Implementation of a service-layer check for overlapping slots before insertion.

### Analytics (Pandas)
- Route to export appointment data to CSV/Excel.
- Dashboard stats (appointments per day, most requested doctors, cancellation rate) processed in-memory via Pandas.

### Security
- JWT for stateless authentication.
- Scoped access (RBAC): Patients can only book for themselves, doctors see their schedule, admins see everything.

## 3. API Endpoints

- `POST /auth/register`: Create user.
- `POST /auth/token`: Login and get JWT.
- `GET /doctors`: List available doctors.
- `GET /appointments`: List user's appointments.
- `POST /appointments`: Book a new appointment.
- `GET /analytics/reports`: Admin report (Pandas processed).

## 4. Frontend Structure
- `index.html`: Login/Register.
- `dashboard.html`: Main view (Patient/Doctor/Admin).
- `app.js`: API consumption and state management.
