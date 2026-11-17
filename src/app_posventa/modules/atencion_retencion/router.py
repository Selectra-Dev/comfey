from ...models.enums import ModuleEnum
from ..common import create_module_router

router = create_module_router(
    module=ModuleEnum.ATENCION_RETENCION,
    tags=["Módulo: Atención al Cliente, Retención y Fidelización"]
)
