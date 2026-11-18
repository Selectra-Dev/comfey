import os
from pydantic import BaseModel
from dotenv import load_dotenv

# Cargar variables locales desde .env si existe
load_dotenv()

class Settings(BaseModel):
    app_name: str = os.getenv("APP_NAME", "COMFEY")
    project_id: str = os.getenv("PROJECT_ID", "safari-zone-selectra")
    port: int = int(os.getenv("PORT", "8080"))
    dev_mode: bool = os.getenv("DEV_MODE", "false").lower() in ("true", "1", "yes")
    dev_user_email: str = os.getenv("DEV_USER_EMAIL", "carlos.alfageme@selectra.com")
    dev_user_role: str = os.getenv("DEV_USER_ROLE", "admin")
    gcs_bucket_name: str = os.getenv("GCS_BUCKET_NAME", "safari-zone-comfey-data")
    firestore_database_id: str = os.getenv("FIRESTORE_DATABASE_ID", "comfey")

settings = Settings()
