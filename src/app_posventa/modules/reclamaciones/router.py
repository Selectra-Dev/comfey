from ...models.enums import ModuleEnum
from ..common import create_module_router

router = create_module_router(
    module=ModuleEnum.RECLAMACIONES,
    tags=["Módulo: Reclamaciones"]
)
