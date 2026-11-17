from ...models.enums import ModuleEnum
from ..common import create_module_router

router = create_module_router(
    module=ModuleEnum.RECHAZOS_ATR,
    tags=["Módulo: Rechazos ATR"]
)
