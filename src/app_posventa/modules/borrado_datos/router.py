from ...models.enums import ModuleEnum
from ..common import create_module_router

router = create_module_router(
    module=ModuleEnum.BORRADO_DATOS,
    tags=["Módulo: Borrado de Datos (GDPR)"]
)
