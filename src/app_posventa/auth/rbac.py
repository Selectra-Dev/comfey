from typing import Callable
from fastapi import Depends, HTTPException, status
from ..models.enums import Role, ModuleEnum
from ..models.user import User
from .iap import get_current_user

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Verifica que el usuario tenga rol de Administrador."""
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operación restringida exclusivamente al rol Administrador."
        )
    return current_user

def require_module_access(module: ModuleEnum) -> Callable[[User], User]:
    """
    Fábrica de dependencias para validar que el usuario actual tenga acceso
    al módulo específico solicitado (o sea Administrador).
    """
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if not current_user.has_module_access(module):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado: no dispones de permisos para el módulo '{module.value}'."
            )
        return current_user
    return dependency
