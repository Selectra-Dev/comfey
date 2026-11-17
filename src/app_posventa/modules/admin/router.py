from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from ...models.user import User, UserUpdatePermissions
from ...models.enums import ModuleEnum
from ...auth.rbac import require_admin
from ...database.firestore import repo

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["Administración y Roles (RBAC)"],
    dependencies=[Depends(require_admin)]
)

@router.get("/users", response_model=List[User])
def list_system_users(admin_user: User = Depends(require_admin)):
    """Lista todos los usuarios del sistema y sus permisos por módulo."""
    return repo.list_users()

@router.post("/users/{email}/permissions", response_model=User)
def update_user_permissions(
    email: str,
    update: UserUpdatePermissions,
    admin_user: User = Depends(require_admin)
):
    """
    Asigna o modifica los módulos permitidos y el rol de un usuario.
    Solo accesible por administradores.
    """
    user = repo.get_user(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con email '{email}' no encontrado."
        )

    user.role = update.role
    user.allowed_modules = update.allowed_modules
    saved = repo.save_user(user)
    return saved
