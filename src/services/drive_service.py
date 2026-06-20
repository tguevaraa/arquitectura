import os
import asyncio
from src.core.config import settings


async def subir_archivo(file_bytes: bytes, filename: str, mimetype: str) -> dict:
    """
    Sube un archivo a Google Drive usando una cuenta de servicio.
    Si las credenciales no están configuradas, retorna drive_file_id=None y drive_url=None,
    y muestra un mensaje en la consola del servidor.
    """
    creds_file = settings.GOOGLE_CREDENTIALS_FILE
    folder_id = settings.GOOGLE_DRIVE_FOLDER_ID

    if not creds_file or not os.path.exists(creds_file):
        print(
            f"\n[DRIVE] Sin credenciales configuradas. "
            f"Archivo '{filename}' no se subió a Google Drive.\n"
            f"  → Configure GOOGLE_CREDENTIALS_FILE y GOOGLE_DRIVE_FOLDER_ID en .env\n",
            flush=True,
        )
        return {"drive_file_id": None, "drive_url": None}

    def _upload():
        try:
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaIoBaseUpload
            from google.oauth2 import service_account
            import io

            SCOPES = ["https://www.googleapis.com/auth/drive.file"]
            creds = service_account.Credentials.from_service_account_file(
                creds_file, scopes=SCOPES
            )
            service = build("drive", "v3", credentials=creds)

            file_metadata = {"name": filename}
            if folder_id:
                file_metadata["parents"] = [folder_id]

            media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype=mimetype)
            result = (
                service.files()
                .create(body=file_metadata, media_body=media, fields="id,webViewLink")
                .execute()
            )

            # Permite lectura pública para que el enlace funcione sin login
            service.permissions().create(
                fileId=result["id"],
                body={"type": "anyone", "role": "reader"},
            ).execute()

            print(
                f"\n[DRIVE] Archivo '{filename}' subido correctamente.\n"
                f"  → ID: {result['id']}\n"
                f"  → URL: {result.get('webViewLink')}\n",
                flush=True,
            )
            return {"drive_file_id": result["id"], "drive_url": result.get("webViewLink")}

        except Exception as e:
            print(f"\n[DRIVE] Error al subir '{filename}': {e}\n", flush=True)
            return {"drive_file_id": None, "drive_url": None}

    return await asyncio.to_thread(_upload)
