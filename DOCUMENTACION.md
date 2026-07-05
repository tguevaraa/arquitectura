# Documentación Técnica Completa
# Sistema de Gestión Médica — Unidad Médica Central

---

## Tabla de Contenidos

1. [Descripción del Sistema](#1-descripción-del-sistema)
2. [Stack Tecnológico](#2-stack-tecnológico)
3. [Arquitectura del Sistema](#3-arquitectura-del-sistema)
4. [Estructura de Carpetas](#4-estructura-de-carpetas)
5. [Base de Datos — Modelos y Relaciones](#5-base-de-datos--modelos-y-relaciones)
6. [Schemas Pydantic (Validación)](#6-schemas-pydantic-validación)
7. [Seguridad y Autenticación](#7-seguridad-y-autenticación)
8. [API — Endpoints Completos](#8-api--endpoints-completos)
9. [Servicios (Lógica de Negocio)](#9-servicios-lógica-de-negocio)
10. [Módulo de Analytics](#10-módulo-de-analytics)
11. [Integración con Google Drive](#11-integración-con-google-drive)
12. [Frontend — Páginas y Flujos](#12-frontend--páginas-y-flujos)
13. [Bugs Encontrados y Corregidos](#13-bugs-encontrados-y-corregidos)
14. [Despliegue en Producción](#14-despliegue-en-producción)
15. [Variables de Entorno](#15-variables-de-entorno)
16. [Ejecución Local](#16-ejecución-local)
17. [Creación de la Cuenta Administrador](#17-creación-de-la-cuenta-administrador)

---

## 1. Descripción del Sistema

**Unidad Médica Central** es un sistema web de gestión médica que permite a una clínica o consultorio:

- Registrar y gestionar pacientes con sus datos demográficos y clínicos
- Agendar, modificar, cancelar y reagendar citas médicas
- Registrar la historia clínica completa por paciente (consultas, diagnósticos, tratamientos, exámenes)
- Subir documentos médicos a Google Drive y acceder a ellos desde el sistema
- Gestionar tres tipos de usuarios con permisos diferenciados: **Administrador**, **Médico** y **Paciente**
- Autenticación con doble factor para pacientes (contraseña + código por correo)

---

## 2. Stack Tecnológico

| Capa | Tecnología | Versión | Función |
|------|-----------|---------|---------|
| Backend | Python + FastAPI | 3.12 / latest | API REST asíncrona |
| ORM | SQLAlchemy (async) | 2.x | Mapeo objeto-relacional |
| Base de datos | MySQL | 8.x | Persistencia de datos |
| Driver BD | aiomysql | latest | Conexión asíncrona a MySQL |
| Validación | Pydantic v2 | 2.x | Schemas de entrada/salida |
| Autenticación | JWT (python-jose) | latest | Tokens de acceso |
| Hash contraseñas | bcrypt | latest | Seguridad de credenciales |
| Email | smtplib (stdlib) | — | Envío de códigos de verificación |
| Almacenamiento | Google Drive API v3 | latest | Archivos médicos en la nube |
| Analytics | pandas | latest | Reportes y exportación CSV |
| Frontend | HTML + CSS + JS vanilla | — | Interfaz de usuario |
| Servidor | Uvicorn (ASGI) | latest | Servidor de desarrollo local |
| Despliegue | Vercel (serverless) | — | Hosting en producción |
| BD Producción | Railway (MySQL) | — | Base de datos en la nube |
| Configuración | pydantic-settings | 2.x | Variables de entorno tipadas |

---

## 3. Arquitectura del Sistema

El sistema sigue el patrón **Layered Architecture** (arquitectura en capas):

```
┌─────────────────────────────────────────┐
│         Frontend (HTML/CSS/JS)          │
│   inicio.html  dashboard.html  etc.     │
└──────────────┬──────────────────────────┘
               │ HTTP/JSON (fetch API)
┌──────────────▼──────────────────────────┐
│          API Layer  [src/api/]          │
│  Recibe request, valida JWT, delega     │
│  auth.py  appointments.py  admin.py     │
│  doctors.py  patients.py  analytics.py │
└──────────────┬──────────────────────────┘
               │ llamadas a funciones async
┌──────────────▼──────────────────────────┐
│       Service Layer [src/services/]     │
│  Lógica de negocio, reglas, validaciones│
│  auth_service.py  appointment_service.py│
│  doctor_service.py  drive_service.py    │
└──────────────┬──────────────────────────┘
               │ SQLAlchemy ORM
┌──────────────▼──────────────────────────┐
│        Model Layer [src/models/]        │
│  Definición de tablas y relaciones      │
│  user.py  doctor.py  patient.py         │
│  appointment.py  clinical.py            │
└──────────────┬──────────────────────────┘
               │ aiomysql driver
┌──────────────▼──────────────────────────┐
│          MySQL Database                 │
│   Local: localhost:3306                 │
│   Producción: Railway                   │
└─────────────────────────────────────────┘
```

**Principio clave:** cada capa solo conoce a la inmediata inferior. El router no consulta la BD directamente, siempre lo hace a través del servicio.

---

## 4. Estructura de Carpetas

```
projecto arquitecturta/
│
├── api/
│   └── index.py                ← Entry point para Vercel (serverless)
│
├── src/
│   ├── main.py                 ← Punto de entrada FastAPI, registro de routers
│   │
│   ├── core/
│   │   ├── config.py           ← Settings con pydantic-settings (lee .env)
│   │   ├── database.py         ← Motor async, sesión, Base declarativa
│   │   ├── security.py         ← Hash bcrypt, generación/verificación JWT
│   │   └── email.py            ← Generación y envío de código de verificación
│   │
│   ├── models/
│   │   ├── __init__.py         ← Importa todos los modelos (registro en Base)
│   │   ├── user.py             ← Tabla users + enum UserRole
│   │   ├── doctor.py           ← Tabla doctors
│   │   ├── patient.py          ← Tabla patient_profiles
│   │   ├── appointment.py      ← Tabla appointments + enum AppointmentStatus
│   │   └── clinical.py         ← Tablas consulta_records y documentos
│   │
│   ├── schemas/
│   │   └── __init__.py         ← Todos los schemas Pydantic del sistema
│   │
│   ├── services/
│   │   ├── auth_service.py     ← CRUD de usuarios, autenticación
│   │   ├── appointment_service.py ← Lógica de citas (colisiones, 24h, etc.)
│   │   ├── doctor_service.py   ← Listado y creación de perfiles médicos
│   │   └── drive_service.py    ← Subida de archivos a Google Drive
│   │
│   ├── api/
│   │   ├── auth.py             ← /auth/* (login, register, 2FA paciente)
│   │   ├── appointments.py     ← /appointments/* (CRUD de citas)
│   │   ├── doctors.py          ← /doctors/* (listado y creación)
│   │   ├── patients.py         ← /patients/* (perfiles, consultas, docs)
│   │   ├── admin.py            ← /admin/* (gestión de usuarios y médicos)
│   │   └── analytics.py        ← /analytics/* (reportes, exportación CSV)
│   │
│   └── analytics/
│       └── reports.py          ← Procesamiento con pandas, agregaciones
│
├── frontend/
│   ├── index.html              ← Página de presentación pública
│   ├── inicio.html             ← Login del personal médico
│   ├── dashboard.html          ← Panel principal (admin/médico)
│   ├── admin.html              ← Panel de administración de usuarios
│   ├── paciente.html           ← Portal del paciente (2FA)
│   ├── historia.html           ← Historia clínica por paciente
│   └── js/
│       └── api.js              ← Centraliza todos los fetch al backend
│
├── create_admin.py             ← Script para crear cuenta administrador
├── run.py                      ← Arranque local con uvicorn
├── requirements.txt            ← Dependencias Python
├── vercel.json                 ← Configuración de despliegue en Vercel
├── runtime.txt                 ← Versión de Python para Vercel (3.12)
├── .vercelignore               ← Archivos excluidos del despliegue
└── .env                        ← Variables de entorno locales (no en git)
```

---

## 5. Base de Datos — Modelos y Relaciones

### 5.1 Conexión (src/core/database.py)

```python
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    poolclass=NullPool,          # Sin pool persistente (serverless)
    connect_args={"ssl": _ssl_ctx}  # SSL requerido para Railway
)
```

- `NullPool`: en entornos serverless, cada request abre y cierra su propia conexión
- `ssl`: requerido para conexiones públicas a Railway MySQL
- `get_db()`: generador inyectado como dependencia en cada endpoint

### 5.2 Tabla `users`

```
users
├── id              INT PK AUTO_INCREMENT
├── email           VARCHAR(255) UNIQUE NOT NULL
├── hashed_password VARCHAR(255) NOT NULL
├── full_name       VARCHAR(255) NOT NULL
├── role            ENUM('patient','doctor','admin') DEFAULT 'patient'
└── is_active       BOOLEAN DEFAULT TRUE
```

Todos los usuarios del sistema —sin importar su rol— viven en esta tabla. El campo `role` determina sus permisos.

### 5.3 Tabla `doctors`

```
doctors
├── id         INT PK AUTO_INCREMENT
├── user_id    INT FK → users.id (UNIQUE)
├── specialty  VARCHAR(255) NOT NULL
└── bio        TEXT NULL
```

Extiende a un `User` con rol `doctor`. Relación 1:1 con `users`.

### 5.4 Tabla `patient_profiles`

```
patient_profiles
├── id               INT PK AUTO_INCREMENT
├── user_id          INT FK → users.id (UNIQUE)
├── cedula           VARCHAR(20)
├── fecha_nacimiento DATE
├── sexo             VARCHAR(1)    ← 'M' o 'F'
├── telefono         VARCHAR(20)
├── tipo_seguro      VARCHAR(10)   ← 'AG', 'SG', 'SV'
├── grupo_sanguineo  VARCHAR(5)
├── direccion        TEXT
├── ciudad           VARCHAR(100)
├── ocupacion        VARCHAR(100)
├── empresa          VARCHAR(100)
└── hc_numero        VARCHAR(50)   ← Número de historia clínica
```

Datos demográficos y clínicos del paciente. Separados de `users` para distinguir datos de acceso de datos médicos.

### 5.5 Tabla `appointments`

```
appointments
├── id                   INT PK AUTO_INCREMENT
├── patient_id           INT FK → users.id
├── doctor_id            INT FK → doctors.id
├── appointment_datetime DATETIME INDEX NOT NULL
├── status               ENUM('scheduled','completed','cancelled') DEFAULT 'scheduled'
└── notes                TEXT NULL
```

El índice en `appointment_datetime` acelera la detección de colisiones.

### 5.6 Tabla `consulta_records`

```
consulta_records
├── id                   INT PK AUTO_INCREMENT
├── patient_id           INT FK → users.id
├── doctor_id            INT FK → doctors.id
├── appointment_id       INT FK → appointments.id NULL
├── motivo               TEXT NOT NULL
├── diagnostico          TEXT
├── tratamiento          TEXT
├── examenes_lab         TEXT
├── tipo_imagen          VARCHAR(20)   ← 'rx', 'eco', 'ekg', 'none'
├── observaciones_imagen TEXT
├── fecha_consulta       DATETIME DEFAULT utcnow
└── created_at           DATETIME DEFAULT utcnow
```

### 5.7 Tabla `documentos`

```
documentos
├── id             INT PK AUTO_INCREMENT
├── consulta_id    INT FK → consulta_records.id
├── patient_id     INT FK → users.id
├── tipo           VARCHAR(30)   ← 'historia_clinica', 'orden_lab', etc.
├── nombre_archivo VARCHAR(255)
├── drive_file_id  VARCHAR(255)  ← ID del archivo en Google Drive
├── drive_url      VARCHAR(500)  ← URL pública de visualización
├── subido_por     INT FK → users.id
└── created_at     DATETIME DEFAULT utcnow
```

### 5.8 Diagrama de Relaciones

```
users (1) ──────── (1) doctors           [user_id → users.id]
users (1) ──────── (1) patient_profiles  [user_id → users.id]
users (1) ──────── (N) appointments      [patient_id → users.id]
doctors (1) ─────── (N) appointments     [doctor_id → doctors.id]
appointments (1) ── (N) consulta_records [appointment_id → appointments.id]
consulta_records (1) ── (N) documentos  [consulta_id → consulta_records.id]
```

---

## 6. Schemas Pydantic (Validación)

Los schemas en `src/schemas/__init__.py` actúan como contrato entre el HTTP y la base de datos.

### Schemas de Usuario
| Schema | Uso |
|--------|-----|
| `UserCreate` | Registro de nuevo usuario |
| `UserResponse` | Respuesta con datos públicos del usuario |
| `UserAdminUpdate` | Admin cambia rol o estado activo |
| `PasswordReset` | Admin resetea contraseña |

### Schemas de Autenticación
| Schema | Uso |
|--------|-----|
| `Token` | Respuesta del login (access_token + token_type) |
| `TokenData` | Datos extraídos del JWT (email, role) |
| `SendCodeRequest` | Login paciente paso 1 (email + password) |
| `VerifyCodeRequest` | Login paciente paso 2 (email + código) |

### Schemas de Citas
| Schema | Uso |
|--------|-----|
| `AppointmentCreate` | Crear nueva cita (doctor_id, datetime, notes, patient_id opcional) |
| `AppointmentUpdate` | Actualizar estado o notas de una cita |
| `AppointmentResponse` | Respuesta con datos completos incluido nombre del paciente |
| `RescheduleRequest` | Reagendar (new_datetime) |

### Schemas de Médicos
| Schema | Uso |
|--------|-----|
| `DoctorCreate` | Crear perfil médico (specialty, bio, user_id) |
| `DoctorResponse` | Respuesta con perfil + datos del usuario |
| `DoctorFullCreate` | Admin crea usuario+perfil médico en un paso |

### Schemas de Pacientes
| Schema | Uso |
|--------|-----|
| `PatientFullCreate` | Crear usuario+perfil paciente en un paso |
| `PatientProfileCreate` | Actualizar datos demográficos |
| `PatientProfileResponse` | Perfil completo con datos del usuario |

### Schemas de Historia Clínica
| Schema | Uso |
|--------|-----|
| `ConsultaRecordCreate` | Nueva consulta (motivo, dx, tx, etc.) |
| `ConsultaRecordResponse` | Consulta completa con documentos y nombre del médico |
| `DocumentoResponse` | Documento con URL de Drive |

> `model_config = ConfigDict(from_attributes=True)` permite que Pydantic lea directamente desde objetos ORM de SQLAlchemy sin conversión manual.

---

## 7. Seguridad y Autenticación

### 7.1 Hash de Contraseñas (bcrypt)

```python
# Generar hash
salt = bcrypt.gensalt()
hashed = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

# Verificar
bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))
```

- Nunca se almacena la contraseña en texto plano
- El salt es aleatorio en cada hash, por lo que dos usuarios con la misma contraseña tienen hashes distintos

### 7.2 JSON Web Tokens (JWT)

```python
# Payload del token
{
    "sub": "correo@ejemplo.com",   # subject (email del usuario)
    "role": "admin",               # rol para autorización
    "exp": 1234567890              # timestamp de expiración
}
```

- Algoritmo: `HS256`
- Duración: `480 minutos` (8 horas)
- Firmado con `SECRET_KEY` del entorno

### 7.3 Flujo de Autenticación — Personal Médico

```
1. POST /auth/login
   → Envía: { username: email, password }  [form-data]
   → Backend verifica bcrypt contra BD
   → Devuelve: { access_token, token_type: "bearer" }

2. Cada request subsiguiente:
   → Header: Authorization: Bearer <token>
   → get_current_user() decodifica el JWT y devuelve el User
   → Si el token es inválido/expirado → 401 Unauthorized
```

### 7.4 Flujo de Autenticación — Pacientes (2 Factores)

```
Paso 1 — POST /auth/patient-login
   → Envía: { email, password }
   → Backend valida credenciales
   → Genera código de 6 dígitos aleatorio
   → Guarda código en memoria con TTL de 10 minutos
   → Envía código por SMTP (o imprime en consola si no hay SMTP)
   → Devuelve: { message: "Código enviado" }

Paso 2 — POST /auth/verify-code
   → Envía: { email, code }
   → Backend verifica código y TTL
   → Si válido: genera y devuelve JWT
   → Si expirado: error 400 "código expirado"
   → Si incorrecto: error 400 "código incorrecto"
```

### 7.5 Middleware de Autorización

```python
async def get_current_user(db=Depends(get_db), token=Depends(oauth2_scheme)):
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    email = payload.get("sub")
    user = await auth_service.get_user_by_email(db, email)
    return user
```

Se inyecta como dependencia en todos los endpoints protegidos. FastAPI lo ejecuta antes del handler.

### 7.6 Control de Acceso por Rol

| Acción | patient | doctor | admin |
|--------|---------|--------|-------|
| Ver sus propias citas | ✓ | — | — |
| Ver todas las citas | — | ✓ | ✓ |
| Crear cita (propia) | ✓ | — | — |
| Crear cita (para paciente) | — | ✓ | ✓ |
| Reagendar/cancelar cita | ✓ (≥24h) | — | — |
| Actualizar estado de cita | — | ✓ | ✓ |
| Ver lista de pacientes | — | ✓ | ✓ |
| Crear/editar paciente | — | ✓ | ✓ |
| Crear consulta clínica | — | ✓ | ✓ |
| Subir documentos | — | ✓ | ✓ |
| Gestionar usuarios | — | — | ✓ |
| Crear médicos | — | — | ✓ |
| Ver analytics | — | — | ✓ |

---

## 8. API — Endpoints Completos

Base URL local: `http://127.0.0.1:8000`  
Documentación interactiva: `http://127.0.0.1:8000/docs`

### 8.1 Autenticación — `/auth`

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| POST | `/auth/register` | No | Registrar nuevo usuario |
| POST | `/auth/login` | No | Login personal médico → JWT |
| POST | `/auth/patient-login` | No | Login paciente paso 1 → envía código |
| POST | `/auth/verify-code` | No | Login paciente paso 2 → JWT |

### 8.2 Médicos — `/doctors`

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/doctors/` | No | Listar todos los médicos con especialidad |
| POST | `/doctors/` | Admin | Crear perfil médico (requiere user_id existente) |

### 8.3 Citas — `/appointments`

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/appointments/` | Sí | Listar citas (filtrado por rol) |
| POST | `/appointments/` | Sí | Crear nueva cita (valida colisiones) |
| PATCH | `/appointments/{id}` | Sí | Actualizar estado o notas |
| POST | `/appointments/{id}/reschedule` | Paciente | Reagendar cita (regla 24h) |

### 8.4 Pacientes — `/patients`

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/patients/` | Staff | Listar todos los pacientes con perfil |
| POST | `/patients/` | Staff | Crear usuario + perfil en un paso |
| GET | `/patients/{id}` | Sí | Ver perfil (paciente ve el propio) |
| PUT | `/patients/{id}` | Sí | Actualizar datos del perfil |
| GET | `/patients/{id}/consultas` | Sí | Listar historial de consultas |
| POST | `/patients/{id}/consultas` | Staff | Registrar nueva consulta clínica |
| POST | `/patients/{id}/consultas/{cid}/documentos` | Staff | Subir documento a Drive |
| GET | `/patients/{id}/documentos` | Sí | Listar documentos del paciente |

### 8.5 Administración — `/admin`

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/admin/users` | Admin | Listar todos los usuarios |
| PATCH | `/admin/users/{id}` | Admin | Cambiar rol o desactivar usuario |
| POST | `/admin/users/{id}/reset-password` | Admin | Resetear contraseña |
| POST | `/admin/doctors` | Admin | Crear usuario + perfil médico completo |

### 8.6 Analytics — `/analytics`

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/analytics/summary` | Admin | Resumen de citas por estado, especialidad y día |
| GET | `/analytics/export/csv` | Admin | Exportar todas las citas como archivo CSV |

---

## 9. Servicios (Lógica de Negocio)

### 9.1 appointment_service.py — El más complejo

**Detección de colisiones:**
```python
# Ventana de ±29 minutos (asume citas de 30 min)
start_time = appointment_datetime - timedelta(minutes=29)
end_time   = appointment_datetime + timedelta(minutes=29)

query = select(Appointment).where(
    doctor_id == doctor_id,
    appointment_datetime.between(start_time, end_time),
    status != CANCELLED
).with_for_update()   # Lock de fila — evita condición de carrera
```

**Regla de 24 horas:**
```python
def _verificar_24h(appointment_datetime):
    ahora = datetime.utcnow()
    horas_restantes = (appt - ahora).total_seconds() / 3600
    if horas_restantes < 24:
        raise HTTPException(400, "Solo puede cancelar o reagendar con al menos 24 horas de anticipación.")
```

**Problema crítico resuelto — MissingGreenlet (SQLAlchemy async):**

En SQLAlchemy async, después de `await db.commit()`, todos los atributos del objeto quedan *expirados*. Acceder a `new_appointment.id` o relaciones lazy después del commit lanza `MissingGreenlet`.

Solución aplicada:
```python
db.add(new_appointment)
await db.flush()           # INSERT → obtiene ID sin hacer commit
appt_id = new_appointment.id  # Guardar ANTES del commit
await db.commit()

# Re-consultar con eager loading usando el ID guardado
result = await db.execute(
    select(Appointment)
    .where(Appointment.id == appt_id)
    .options(selectinload(Appointment.patient))
)
```

Para actualizaciones, guardar datos de relaciones antes del commit:
```python
patient_full_name = db_appointment.patient.full_name  # Antes del commit
await db.commit()
```

**Filtrado por rol:**
```python
if role in ("admin", "doctor"):
    query = select(Appointment).options(selectinload(Appointment.patient))
else:
    query = select(Appointment).where(patient_id == user_id)...
```

### 9.2 auth_service.py

```python
async def create_user(db, user):
    hashed_password = get_password_hash(user.password)
    new_user = User(email=user.email, hashed_password=hashed_password, ...)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

async def authenticate_user(db, email, password):
    user = await get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user
```

### 9.3 drive_service.py

```python
async def subir_archivo(file_bytes, filename, mimetype) -> dict:
    # Si no hay credenciales, falla silenciosamente
    if not creds_file or not os.path.exists(creds_file):
        return {"drive_file_id": None, "drive_url": None}

    def _upload():   # Síncrono — se ejecuta en thread pool
        service = build("drive", "v3", credentials=creds)
        result = service.files().create(...).execute()
        # Hacer archivo público (acceso por link)
        service.permissions().create(
            fileId=result["id"],
            body={"type": "anyone", "role": "reader"}
        ).execute()
        return {"drive_file_id": result["id"], "drive_url": result["webViewLink"]}

    return await asyncio.to_thread(_upload)  # No bloquea el event loop
```

---

## 10. Módulo de Analytics

`src/analytics/reports.py` usa **pandas** para procesar datos de citas:

**Resumen (`GET /analytics/summary`):**
- Total de citas
- Citas por especialidad médica
- Citas por estado (agendada / completada / cancelada)
- Citas por día (serie temporal)

**Exportación (`GET /analytics/export/csv`):**
- Devuelve todas las citas como archivo `.csv` descargable
- Content-Type: `text/csv`
- Content-Disposition: `attachment; filename=appointments.csv`

---

## 11. Integración con Google Drive

Para activar la subida de documentos a Google Drive:

1. Crear un proyecto en [Google Cloud Console](https://console.cloud.google.com)
2. Activar la API de Google Drive
3. Crear una **cuenta de servicio** y descargar el archivo `credentials.json`
4. Crear una carpeta en Drive y compartirla con el email de la cuenta de servicio
5. Configurar en `.env`:

```env
GOOGLE_CREDENTIALS_FILE=credentials.json
GOOGLE_DRIVE_FOLDER_ID=id_de_la_carpeta
```

Si no se configuran estas variables, el sistema sigue funcionando: los documentos se guardan en BD con `drive_url = NULL` y no se interrumpe ningún flujo.

---

## 12. Frontend — Páginas y Flujos

### Capa de comunicación: `frontend/js/api.js`

Centraliza todos los `fetch`. Ninguna página llama directamente a `fetch`. La `API_URL` es vacía (`""`) en producción para usar rutas relativas.

```javascript
const API_URL = "";  // Rutas relativas — funciona en cualquier dominio

function _handleResponse(response, data) {
    if (response.status === 401) {
        localStorage.removeItem("token");
        alert("Tu sesión ha expirado.");
        window.location.href = "inicio.html";
    }
    return data;
}
```

El token JWT se guarda en `localStorage` y se adjunta a cada request:
```javascript
headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` }
```

### 12.1 `inicio.html` — Login del personal médico

1. Usuario introduce email + contraseña
2. `api.login()` → `POST /auth/login`
3. JWT guardado en `localStorage`
4. Redirección a `dashboard.html`

### 12.2 `dashboard.html` — Panel principal

La página más compleja del sistema. Tiene dos tabs principales:

**Tab Agenda:**
- Tabla de citas con tres filtros:
  - **Hoy**: citas de la fecha actual en hora local del navegador
  - **Todas**: sin filtro de fecha
  - Búsqueda por texto + filtro por estado
- Modal para crear nueva cita (seleccionar paciente, médico, fecha, hora, notas)
- Modal para editar cita (cambiar estado a completada/cancelada, editar notas)
- Después de crear/editar, el filtro cambia a "Todas" para mostrar el resultado

**Tab Pacientes:**
- Tabla con todos los pacientes registrados
- Formulario para crear nuevo paciente
- Acceso a historia clínica de cada paciente

### 12.3 `historia.html` — Historia clínica

Recibe `?patient_id=X` por query string.

Al cargar:
1. `api.getPatient(id)` → muestra datos demográficos del paciente
2. `api.getConsultas(id)` → lista de consultas ordenadas por fecha descendente

Desde esta página se puede:
- Crear nueva consulta (motivo, diagnóstico, tratamiento, exámenes, tipo de imagen)
- Subir documentos médicos (se envían a Google Drive)
- Ver y descargar documentos anteriores

### 12.4 `paciente.html` — Portal del paciente (2FA)

**Paso 1 — Login:**
1. Paciente introduce email + contraseña
2. `api.patientLogin()` → `POST /auth/patient-login`
3. Backend valida y envía código al correo
4. Se muestra el campo de código

**Paso 2 — Verificación:**
5. Paciente introduce el código de 6 dígitos
6. `api.verifyCode()` → `POST /auth/verify-code`
7. JWT guardado → acceso al portal

**Dentro del portal:**
- Ver sus propias citas
- Reagendar cita (mínimo 24h de anticipación)
- Cancelar cita (mínimo 24h de anticipación)

### 12.5 `admin.html` — Gestión de usuarios

Solo accesible con rol `admin`:
- Listar todos los usuarios del sistema
- Cambiar rol de un usuario (patient → doctor → admin)
- Activar/desactivar cuenta
- Resetear contraseña
- Crear nuevo médico (usuario + perfil médico en un formulario)

### 12.6 `index.html` — Página pública

Página de presentación del sistema, accesible sin autenticación.

---

## 13. Bugs Encontrados y Corregidos

### Bug 1 — `MissingGreenlet` al crear cita (500)

**Causa:** En SQLAlchemy async, `expire_on_commit=True` (comportamiento por defecto) expira todos los atributos del objeto después de `await db.commit()`. Al intentar acceder a `new_appointment.id` después del commit, SQLAlchemy lanzaba un SELECT lazy que no está permitido en contexto asíncrono.

**Síntoma:** `POST /appointments/` devolvía 500. La cita SÍ se creaba en BD (demostrado porque al intentar crear la misma cita dos veces, el sistema de colisiones la detectaba), pero la respuesta fallaba.

**Solución:**
```python
await db.flush()           # INSERT sin commit → obtiene ID
appt_id = new_appointment.id  # Guardar antes del commit
await db.commit()
# Re-consultar con selectinload para eager loading
```

### Bug 2 — `MissingGreenlet` al actualizar cita (500)

**Causa:** Acceso a `db_appointment.patient.full_name` después de `await db.commit()`.

**Solución:** Guardar el valor de la relación en una variable local antes del commit.

### Bug 3 — Token JWT expiraba en 30 minutos (401)

**Causa:** `ACCESS_TOKEN_EXPIRE_MINUTES = 30`. Las operaciones POST fallaban con 401 si el usuario llevaba más de 30 minutos logueado. Las GET funcionaban (quizás por cache del navegador o respuesta diferente).

**Solución:** Aumentar a `480` minutos (8 horas). Agregar handler de 401 en el frontend que redirige al login.

### Bug 4 — Médico veía 0 citas en el dashboard (lógica incorrecta)

**Causa:** `get_appointments` filtraba por `doctor_id` buscando un perfil en la tabla `doctors` para el usuario logueado. Si el usuario tenía rol `doctor` pero su `doctor.id` no coincidía con las citas, devolvía 0.

**Solución:** Para rol `admin` o `doctor`, devolver todas las citas sin filtrar (vista administrativa).

### Bug 5 — CORS error en el navegador

**Causa aparente:** El servidor devolvía 500 antes de que el middleware CORS pudiera agregar los headers de respuesta. El navegador reportaba un error CORS cuando en realidad era un error 500.

**Solución:** Resolver los errores 500 (bugs 1 y 2). El error CORS desapareció.

### Bug 6 — Filtro "Hoy" no mostraba citas del día

**Causa:** El campo de fecha del modal se inicializaba con `new Date().toISOString().slice(0,10)`, que devuelve la fecha en UTC. En Ecuador (UTC-5), después de las 7 PM la fecha UTC ya era el día siguiente. La cita se agendaba con la fecha de "mañana" y el filtro "Hoy" no la mostraba.

**Solución:**
```javascript
const _hoy = new Date();
fFecha.value = `${_hoy.getFullYear()}-${String(_hoy.getMonth()+1).padStart(2,'0')}-${String(_hoy.getDate()).padStart(2,'0')}`;
```
`getFullYear/getMonth/getDate` devuelven la fecha en hora local del navegador.

### Bug 7 — SSL error al conectar con Railway desde Windows

**Causa:** `aiomysql` + SSL + Windows IOCP (WinError 87) son incompatibles.

**Solución para producción (Vercel/Linux):** Agregar contexto SSL al engine:
```python
import ssl
_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE
engine = create_async_engine(..., connect_args={"ssl": _ssl_ctx})
```

**Solución para crear admin desde Windows:** Insertar directamente en Railway via SQL.

---

## 14. Despliegue en Producción

### Plataformas utilizadas

| Servicio | Rol | URL |
|----------|-----|-----|
| **Vercel** | Hosting del backend (serverless) + frontend | vercel.com |
| **Railway** | Base de datos MySQL en la nube | railway.app |
| **GitHub** | Control de versiones, trigger de deploy | github.com/tguevaraa/arquitectura |

### 14.1 Flujo de Despliegue

```
git push → GitHub → Vercel detecta cambio → build automático → deploy
```

Cada push a `master` despliega automáticamente en Vercel.

### 14.2 Archivos de configuración para Vercel

**`vercel.json`:**
```json
{
  "version": 2,
  "builds": [
    { "src": "api/index.py", "use": "@vercel/python" }
  ],
  "routes": [
    { "src": "/(.*)", "dest": "/api/index.py" }
  ]
}
```

Todo el tráfico se enruta a la función Python. FastAPI sirve el frontend a través de `StaticFiles`.

**`api/index.py`:**
```python
from src.main import app
```

Entry point para Vercel. Importa la app FastAPI.

**`runtime.txt`:**
```
python-3.12
```

Declara Python 3.12 (máximo soportado por Vercel; el proyecto usa 3.13 localmente).

**`.vercelignore`:**
```
**/__pycache__
**/*.pyc
.pytest_cache
tests/
.env
run.py
create_admin.py
```

### 14.3 Inicialización de tablas en producción

El evento `lifespan` en `main.py` ejecuta `create_all` en cada cold start. SQLAlchemy crea las tablas solo si no existen, por lo que es idempotente y seguro.

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        logger.error(f"Error al inicializar la base de datos: {e}")
    yield
```

---

## 15. Variables de Entorno

### Para desarrollo local (`.env`):

```env
DATABASE_URL=mysql+aiomysql://root:contraseña@localhost:3306/umedic_db
SECRET_KEY=clave_secreta_muy_larga_min_32_caracteres
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480

# Opcionales — SMTP para envío de correos
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=correo@gmail.com
SMTP_PASSWORD=clave_de_aplicacion
SMTP_FROM=noreply@umedic.local

# Opcionales — Google Drive
GOOGLE_CREDENTIALS_FILE=credentials.json
GOOGLE_DRIVE_FOLDER_ID=id_de_la_carpeta_en_drive
```

### Para producción (Vercel — Settings → Environment Variables):

| Variable | Valor |
|----------|-------|
| `DATABASE_URL` | `mysql+aiomysql://root:PASS@acela.proxy.rlwy.net:10395/railway` |
| `SECRET_KEY` | Clave generada con `python -c "import secrets; print(secrets.token_hex(32))"` |
| `ALGORITHM` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `480` |

> Si `SMTP_HOST` no está configurado, los códigos de verificación de pacientes se imprimen en los logs del servidor (visible en Vercel → Logs).

---

## 16. Ejecución Local

```bash
# 1. Clonar el repositorio
git clone git@github.com:tguevaraa/arquitectura.git
cd arquitectura

# 2. Crear entorno virtual
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
# Crear archivo .env con las variables del apartado 15

# 5. Iniciar el servidor
python run.py
# o directamente:
uvicorn src.main:app --reload

# 6. Acceder
# API:  http://127.0.0.1:8000
# Docs: http://127.0.0.1:8000/docs
# Web:  http://127.0.0.1:8000  (sirve el frontend)
```

---

## 17. Creación de la Cuenta Administrador

### Opción A — Script local (requiere conexión a la BD)

```bash
python create_admin.py --email admin@umedic.com --nombre "Administrador" --password "Admin1234!"
```

### Opción B — SQL directo en Railway (recomendado para producción)

1. Generar el hash de la contraseña:
```bash
python -c "from src.core.security import get_password_hash; print(get_password_hash('TuContraseña'))"
```

2. Ejecutar en Railway → Database → Data → campo SQL:
```sql
INSERT INTO users (email, hashed_password, full_name, role, is_active)
VALUES (
  'correo@ejemplo.com',
  '$2b$12$hash_generado_arriba...',
  'Nombre del Admin',
  'admin',
  1
);
```

### Credenciales del administrador actual

| Campo | Valor |
|-------|-------|
| Correo | `tommylguevara@gmail.com` |
| Contraseña | `Admin1234!` |
| Rol | `admin` |

> Se recomienda cambiar la contraseña desde el panel de administración después del primer acceso.

---

## Historial de Cambios (Git)

| Commit | Descripción |
|--------|-------------|
| `63d2875` | feat: historia clínica, pacientes, Google Drive y panel admin |
| `80be1d1` | chore: excluir .env del repositorio |
| `cf3ac83` | fix: corregir historial de citas en el dashboard |
| `0c756ce` | fix: corregir historial de citas en el dashboard |
| `a5b9054` | fix: usar fecha local en el filtro Hoy (zona horaria) |
| `f87ef71` | feat: configurar despliegue en Vercel |
| `84420dc` | fix: SSL para Railway MySQL y proteger lifespan |

---

*Documentación generada para el proyecto Sistema de Gestión Médica — Unidad Médica Central.*  
*Repositorio: github.com/tguevaraa/arquitectura*
