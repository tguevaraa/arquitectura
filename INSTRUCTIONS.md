# Sistema de Gestión de Turnos Médicos (FastAPI + MySQL + Pandas)

Este proyecto es una solución integral para la gestión de turnos médicos, diseñada con una arquitectura limpia (Clean Architecture) y preparada para manejar alta concurrencia.

## 🚀 Requisitos Previos

- **Python 3.10+**
- **MySQL Server** (u otro compatible como MariaDB)
- **Pip** (gestor de paquetes de Python)

## 🛠️ Instalación y Configuración

1. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configurar variables de entorno:**
   Edita el archivo `.env` en la raíz del proyecto con tus credenciales de MySQL:
   ```env
   DATABASE_URL=mysql+aiomysql://usuario:contraseña@localhost:3306/nombre_db
   SECRET_KEY=tu_clave_secreta_para_jwt
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ```

3. **Inicialización de la Base de Datos:**
   El sistema está configurado para crear automáticamente las tablas al iniciar la aplicación por primera vez (`src/main.py`). Asegúrate de que la base de datos especificada en el `.env` ya exista.

## 🏃 Ejecución del Sistema

### Backend (API)
Inicia el servidor de desarrollo:
```bash
python run.py
```
- **API URL:** `http://localhost:8000`
- **Documentación Swagger:** `http://localhost:8000/docs` (Útil para probar endpoints manualmente)

### Frontend
No requiere servidor de node. Abre directamente el archivo en tu navegador:
```text
frontend/index.html
```

## 📋 Funcionalidades Principales

1.  **Seguridad (JWT):** Autenticación basada en tokens y Roles (Paciente, Doctor, Admin).
2.  **Gestión de Turnos:** Lógica asíncrona para reservar citas.
3.  **Detección de Colisiones:** El sistema impide agendar citas que se solapen (bloques de 30 min).
4.  **Módulo de Analítica:**
    - `GET /analytics/summary`: Reporte procesado con Pandas (Solo Admins).
    - `GET /analytics/export/csv`: Exportación de la base de datos de turnos a CSV.

## 🧪 Pruebas
Para ejecutar los tests de lógica:
```bash
pytest tests/
```

## 📂 Estructura del Código
- `src/api`: Definición de rutas REST.
- `src/services`: Lógica de negocio y control de concurrencia.
- `src/models`: Esquema de base de datos SQLAlchemy.
- `src/analytics`: Pipelines de datos con Pandas.
- `frontend/`: Interfaz de usuario minimalista con Vanilla JS.
