import uuid
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field
from .enums import ModuleEnum

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

DEFAULT_RGPD_FOOTER = (
    "INFORMACIÓN BÁSICA DE PROTECCIÓN DE DATOS (RGPD / LOPDGDD): Responsable del tratamiento: Selectra. "
    "Finalidad: Gestión, tramitación y seguimiento de su expediente o solicitud posventa. "
    "Legitimación: Ejecución de la relación de intermediación o consulta contractual. "
    "Destinatarios: Empresas comercializadoras o distribuidoras del suministro cuando sea estrictamente necesario. "
    "Derechos: Podrá ejercitar en todo momento sus derechos de acceso, rectificación, supresión, limitación y oposición "
    "remitiendo un correo a dpo@selectra.com. Información adicional en https://selectra.es/privacidad."
)

DEFAULT_SIGNATURE_TEMPLATE = (
    "Atentamente,\n"
    "Equipo de Posventa - Selectra España\n"
    "Teléfono de Soporte: 91 123 45 67 | https://selectra.es\n"
    "Selectra: Expertos en gestión y optimización de suministros"
)

class ModuleEmailSetting(BaseModel):
    module: ModuleEnum
    email: str
    sender_name: str
    account_type: str = "google_group"
    type_label: str = "Bandeja de Grupo de Google Workspace"
    description: str = ""
    signature: str = DEFAULT_SIGNATURE_TEMPLATE
    rgpd_footer: str = DEFAULT_RGPD_FOOTER

class EmailTemplate(BaseModel):
    id: str = Field(default_factory=lambda: f"tpl-{uuid.uuid4().hex[:8]}")
    name: str
    module: str = "todos"  # "todos" o el valor de ModuleEnum
    subject: str
    body: str
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
