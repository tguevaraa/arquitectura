import asyncio
import logging
import random
import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.core.config import settings

logger = logging.getLogger(__name__)

# Almacén en memoria: { email: { "code": str, "expires": datetime } }
_store: dict[str, dict] = {}


def generar_codigo() -> str:
    return str(random.randint(100000, 999999))


def guardar_codigo(email: str, code: str) -> None:
    _store[email] = {
        "code": code,
        "expires": datetime.now(timezone.utc) + timedelta(minutes=10),
    }


def verificar_codigo(email: str, code: str):
    """Retorna True si es válido, 'expired' si expiró, None si no existe, False si es incorrecto."""
    entry = _store.get(email)
    if not entry:
        return None
    if datetime.now(timezone.utc) > entry["expires"]:
        del _store[email]
        return "expired"
    if entry["code"] != code:
        return False
    del _store[email]
    return True


def _enviar_sync(to_email: str, code: str) -> None:
    if not settings.SMTP_HOST:
        print("\n" + "=" * 52, flush=True)
        print(f"  [VERIFICACIÓN] Correo : {to_email}", flush=True)
        print(f"  [VERIFICACIÓN] Código : {code}", flush=True)
        print("  (Expira en 10 minutos)", flush=True)
        print("=" * 52 + "\n", flush=True)
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Código de verificación — Unidad Médica Central"
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email

    html = f"""
    <div style="font-family:'Segoe UI',sans-serif;max-width:480px;margin:0 auto;padding:32px;">
      <h2 style="color:#1a73e8;margin:0 0 8px;">Unidad Médica Central</h2>
      <p style="color:#444;margin:0 0 20px;">
        Ingrese el siguiente código para confirmar su identidad:
      </p>
      <div style="font-size:38px;font-weight:700;letter-spacing:12px;color:#1a73e8;
                  background:#e8f0fe;padding:22px;border-radius:10px;text-align:center;">
        {code}
      </div>
      <p style="color:#888;font-size:13px;margin-top:20px;">
        Este código expira en <strong>10 minutos</strong>.<br>
        Si no solicitó este código, ignore este mensaje.
      </p>
    </div>"""

    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.send_message(msg)


async def enviar_codigo(to_email: str, code: str) -> None:
    await asyncio.to_thread(_enviar_sync, to_email, code)
