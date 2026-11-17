from typing import Optional
from fastapi import Request, HTTPException, status
from ..config import settings
from ..models.user import User
from ..database.firestore import repo

IAP_HEADER_EMAIL = "x-goog-authenticated-user-email"

ALLOWED_DOMAINS = ("@selectra.com", "@selectra.info")

def extract_authenticated_email(request: Request) -> str:
    """
    Extrae y normaliza el correo corporativo del usuario desde la cabecera
    inyectada por Google Cloud Identity-Aware Proxy (IAP).
    Formato IAP: 'accounts.google.com:usuario@selectra.com'
    """
    raw_header = request.headers.get(IAP_HEADER_EMAIL)
    
    if raw_header:
        email = raw_header.split(":")[-1].strip().lower()
        if not any(email.endswith(d) for d in ALLOWED_DOMAINS):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Dominio no autorizado. Acceso exclusivo para cuentas {', '.join(ALLOWED_DOMAINS)}."
            )
        return email

    # Si estamos en entorno de desarrollo local y no hay cabecera IAP
    if settings.dev_mode:
        override_user = request.query_params.get("as_user")
        if override_user:
            return override_user.strip().lower()
        return settings.dev_user_email.strip().lower()

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se ha detectado autenticación corporativa IAP de Google Workspace (@selectra.com)."
    )

def get_current_user(request: Request) -> User:
    """
    Obtiene o crea el registro del usuario corporativo autenticado con sus roles y permisos.
    """
    email = extract_authenticated_email(request)
    
    # Validar dominio corporativo
    if not (email.endswith("@selectra.com") or email.endswith("@selectra.info")):
        if not settings.dev_mode:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso restringido a cuentas corporativas de Selectra (@selectra.com, @selectra.info)."
            )

    user = repo.get_user(email)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo o sin autorización en la plataforma."
        )
    return user
