# Reporte de Despliegue
# Sistema de Gestión Médica — Unidad Médica Central

---

## Información General

| Campo | Detalle |
|-------|---------|
| Proyecto | Sistema de Gestión Médica — Unidad Médica Central |
| Repositorio | github.com/tguevaraa/arquitectura |
| Plataforma de hosting | Vercel |
| Plataforma de base de datos | Railway |
| Fecha de despliegue | Julio 2026 |
| Responsable | Tommy Guevara |

---

## 1. Preparación del Código para Producción

Antes de realizar el despliegue, fue necesario adaptar el código del proyecto para que funcionara correctamente en un entorno serverless (sin servidor persistente). Se realizaron los siguientes cambios:

### 1.1 Archivo de entrada para Vercel — `api/index.py`

Se creó la carpeta `api/` y dentro el archivo `index.py`. Este archivo es el punto de entrada que Vercel utiliza para ejecutar la aplicación. Su contenido es mínimo: importa la aplicación FastAPI ya configurada.

```python
from src.main import app
```

Vercel detecta este archivo automáticamente como la función serverless de Python.

### 1.2 Configuración de rutas — `vercel.json`

Se creó el archivo `vercel.json` en la raíz del proyecto. Este archivo le indica a Vercel cómo construir y enrutar el proyecto:

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

Todo el tráfico (cualquier ruta) se enruta hacia la función Python. FastAPI se encarga internamente de distinguir entre las rutas de la API y los archivos del frontend (HTML, CSS, JS).

### 1.3 Versión de Python — `runtime.txt`

Vercel soporta Python hasta la versión 3.12. El proyecto fue desarrollado con Python 3.13 localmente, por lo que se declaró la versión compatible:

```
python-3.12
```

### 1.4 Archivos ignorados — `.vercelignore`

Se creó el archivo `.vercelignore` para excluir del despliegue archivos innecesarios que aumentarían el tamaño del paquete:

```
**/__pycache__
**/*.pyc
.pytest_cache
tests/
.env
run.py
create_admin.py
```

### 1.5 Ruta absoluta del frontend — `src/main.py`

En desarrollo local, el servidor se ejecuta desde la raíz del proyecto y la ruta relativa `"frontend"` funciona correctamente. En Vercel, el directorio de trabajo puede ser diferente, por lo que se cambió a una ruta absoluta calculada desde la ubicación del propio archivo:

```python
import os
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
```

### 1.6 Pool de conexiones — `src/core/database.py`

En entornos serverless, cada request puede ser manejado por una instancia diferente del servidor. Mantener un pool de conexiones persistentes causa errores de conexión. Se configuró `NullPool` para que cada request abra y cierre su propia conexión:

```python
from sqlalchemy.pool import NullPool

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    poolclass=NullPool,
)
```

### 1.7 Soporte SSL — `src/core/database.py`

Railway requiere conexiones SSL para el acceso público a la base de datos. Se configuró un contexto SSL en el motor de base de datos:

```python
import ssl

_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    poolclass=NullPool,
    connect_args={"ssl": _ssl_ctx},
)
```

### 1.8 URL de la API en el frontend — `frontend/js/api.js`

En desarrollo, la API estaba en `http://127.0.0.1:8000`. En producción, el frontend y el backend viven en el mismo dominio de Vercel, por lo que se cambió a una URL relativa vacía:

```javascript
// Antes
const API_URL = "http://127.0.0.1:8000";

// Después
const API_URL = "";
```

Con `API_URL = ""`, todas las llamadas como `` `${API_URL}/auth/login` `` se convierten en `/auth/login`, que apuntan automáticamente al mismo dominio donde está el sitio.

### 1.9 CORS abierto — `src/main.py`

En desarrollo, CORS estaba configurado para permitir solo orígenes específicos (`localhost:5500`, `localhost:8000`). En producción, se abrió para aceptar cualquier origen:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    ...
)
```

### 1.10 Protección del lifespan — `src/main.py`

El evento `lifespan` ejecuta la creación de tablas al arrancar. Se envolvió en un bloque `try/except` para que un fallo de conexión temporal a la base de datos no tumbe toda la aplicación:

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

## 2. Alojamiento de la Base de Datos en Railway

Railway es una plataforma en la nube que permite desplegar bases de datos y aplicaciones de forma sencilla. Se utilizó para alojar la base de datos MySQL del sistema.

### 2.1 Creación del proyecto en Railway

1. Se ingresó a [railway.app](https://railway.app) y se inició sesión con cuenta de GitHub.
2. Se creó un nuevo proyecto haciendo clic en **New Project**.
3. Se seleccionó la opción **Deploy MySQL** del catálogo de servicios disponibles.
4. Railway aprovisionó automáticamente una instancia de MySQL 8.x con:
   - Base de datos llamada `railway`
   - Usuario: `root`
   - Contraseña generada automáticamente
   - Host público: `acela.proxy.rlwy.net`
   - Puerto: `10395`

### 2.2 Obtención de la cadena de conexión

Una vez creada la instancia:

1. Se abrió el servicio MySQL en Railway.
2. Se navegó a la pestaña **Database** → subtab **Data** → botón **Connect** (esquina superior derecha).
3. Se seleccionó la tab **Public Network**.
4. Railway mostró la **Connection URL**:

```
mysql://root:********@acela.proxy.rlwy.net:10395/railway
```

5. Se hizo clic en **show** para revelar la contraseña real.
6. Se copió la URL completa y se modificó el prefijo de `mysql://` a `mysql+aiomysql://` para compatibilidad con el driver asíncrono del proyecto:

```
mysql+aiomysql://root:ogHzlxbgGlywfOpWWvlnEDBhAUjIaUKV@acela.proxy.rlwy.net:10395/railway
```

### 2.3 Creación automática de tablas

Las tablas de la base de datos **no se crearon manualmente**. El sistema usa SQLAlchemy con `Base.metadata.create_all`, que lee todos los modelos definidos en Python y crea las tablas correspondientes automáticamente la primera vez que la aplicación arranca.

Las tablas creadas fueron:
- `users`
- `doctors`
- `patient_profiles`
- `appointments`
- `consulta_records`
- `documentos`

Esto se verificó desde el panel de Railway → Database → Data, donde las 6 tablas aparecieron listadas correctamente.

### 2.4 Creación del usuario administrador

Dado que la base de datos está en la nube y el driver `aiomysql` con SSL tiene incompatibilidades con Windows (WinError 87 de IOCP), el usuario administrador se creó directamente mediante SQL desde la consola de Railway.

**Paso 1 — Generar el hash de la contraseña localmente:**

```bash
python -c "from src.core.security import get_password_hash; print(get_password_hash('Admin1234!'))"
```

Resultado:
```
$2b$12$C3KrURkQbvFRw72p1sHh2usC8VBmuQ.HdvG1FqXNPRBOpiqWy8bd.
```

**Paso 2 — Ejecutar el INSERT en la consola SQL de Railway:**

En Railway → Database → Data → campo SQL, se ejecutó:

```sql
INSERT INTO users (email, hashed_password, full_name, role, is_active)
VALUES (
  'tommylguevara@gmail.com',
  '$2b$12$C3KrURkQbvFRw72p1sHh2usC8VBmuQ.HdvG1FqXNPRBOpiqWy8bd.',
  'Administrador',
  'admin',
  1
);
```

El usuario administrador quedó registrado con:
- **Correo:** `tommylguevara@gmail.com`
- **Contraseña:** `Admin1234!`
- **Rol:** `admin`

---

## 3. Despliegue en Vercel

Vercel es una plataforma de despliegue que soporta aplicaciones Python mediante funciones serverless. Cada request activa una instancia de la función, la ejecuta y la apaga.

### 3.1 Conexión del repositorio

1. Se ingresó a [vercel.com](https://vercel.com) y se inició sesión.
2. Se hizo clic en **Add New Project**.
3. Se conectó la cuenta de GitHub y se seleccionó el repositorio `tguevaraa/arquitectura`.
4. Vercel detectó automáticamente el archivo `vercel.json` y configuró el proyecto.

### 3.2 Configuración de variables de entorno

Antes de realizar el primer despliegue, se configuraron las variables de entorno en Vercel:

**Ruta:** Settings → Environment Variables

Se agregaron las siguientes variables:

| Variable | Valor configurado |
|----------|-------------------|
| `DATABASE_URL` | `mysql+aiomysql://root:ogHzlxbgGlywfOpWWvlnEDBhAUjIaUKV@acela.proxy.rlwy.net:10395/railway` |
| `SECRET_KEY` | `4c7efe97f33feb51ac695dc25dec50fc09acfe4d8cad3baa557c2a02ba5ebbb4` |
| `ALGORITHM` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `480` |

La `SECRET_KEY` se generó con el siguiente comando de Python:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3.3 Primer despliegue y errores encontrados

#### Error 1 — Variables de entorno no encontradas

En el primer intento de despliegue, la aplicación fallaba al iniciar con el siguiente error en los logs:

```
pydantic_core.ValidationError: 2 validation errors for Settings
DATABASE_URL: Field required
SECRET_KEY:   Field required
```

**Causa:** Las variables de entorno se configuraron después de que Vercel ya había hecho el build. En Vercel, las variables solo se inyectan al momento del build y del runtime si están configuradas previamente.

**Solución:** Se verificó que las variables estuvieran guardadas en Settings → Environment Variables y se realizó un **Redeploy** desde Deployments → botón `···` → Redeploy.

#### Error 2 — FUNCTION_INVOCATION_FAILED (500)

Después de que las variables fueron reconocidas, la aplicación arrancaba pero fallaba al recibir requests con error 500.

**Causa:** Railway requiere SSL para conexiones públicas. El motor de base de datos no tenía configurado el contexto SSL, por lo que la conexión era rechazada.

**Solución:** Se agregó el contexto SSL al `create_async_engine` y se protegió el `lifespan` con `try/except`. Los cambios se hicieron en el código local y se subieron con:

```bash
git add src/core/database.py src/main.py
git commit -m "fix: SSL para Railway MySQL y proteger lifespan contra errores de BD"
git push
```

Vercel detectó el nuevo push automáticamente y realizó un nuevo deploy.

### 3.4 Resultado final

Tras resolver los errores, el sistema quedó operativo en producción. Vercel asignó una URL pública al proyecto. El flujo de despliegue continuo quedó configurado así:

```
Desarrollador hace cambios → git push → GitHub → Vercel detecta el push
→ Instala dependencias de requirements.txt → Ejecuta el build
→ Despliega la nueva versión automáticamente
```

---

## 4. Diagrama del Sistema en Producción

```
┌─────────────────────────────────────────────────────┐
│                    USUARIO FINAL                    │
│           (Navegador web — cualquier lugar)         │
└──────────────────────┬──────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────┐
│                     VERCEL                          │
│  ┌─────────────────────────────────────────────┐   │
│  │  Función Python Serverless (api/index.py)   │   │
│  │                                             │   │
│  │  FastAPI app                                │   │
│  │  ├── Rutas API: /auth, /appointments, etc.  │   │
│  │  └── StaticFiles: /frontend/*.html          │   │
│  └──────────────────────┬──────────────────────┘   │
└─────────────────────────│───────────────────────────┘
                          │ MySQL + SSL (Puerto 10395)
┌─────────────────────────▼───────────────────────────┐
│                    RAILWAY                          │
│  ┌─────────────────────────────────────────────┐   │
│  │  MySQL 8.x                                  │   │
│  │  Host: acela.proxy.rlwy.net                 │   │
│  │  Base de datos: railway                     │   │
│  │  Tablas: users, doctors, patient_profiles,  │   │
│  │          appointments, consulta_records,    │   │
│  │          documentos                         │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

---

## 5. Resumen de Archivos Creados/Modificados para el Despliegue

| Archivo | Tipo | Cambio realizado |
|---------|------|-----------------|
| `api/index.py` | Nuevo | Entry point de Vercel |
| `vercel.json` | Nuevo | Configuración de build y rutas |
| `runtime.txt` | Nuevo | Declaración de Python 3.12 |
| `.vercelignore` | Nuevo | Exclusión de archivos innecesarios |
| `src/main.py` | Modificado | Ruta absoluta del frontend, CORS abierto, lifespan protegido |
| `src/core/database.py` | Modificado | NullPool + SSL para Railway |
| `frontend/js/api.js` | Modificado | API_URL cambiada a ruta relativa vacía |

---

*Reporte generado para el proyecto Sistema de Gestión Médica — Unidad Médica Central.*
*Repositorio: github.com/tguevaraa/arquitectura*
