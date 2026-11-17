from .incidencias_contratos.router import router as router_incidencias_contratos
from .atencion_retencion.router import router as router_atencion_retencion
from .reclamaciones.router import router as router_reclamaciones
from .borrado_datos.router import router as router_borrado_datos
from .incidencias_suministro.router import router as router_incidencias_suministro
from .rechazos_atr.router import router as router_rechazos_atr
from .admin.router import router as router_admin

__all__ = [
    "router_incidencias_contratos",
    "router_atencion_retencion",
    "router_reclamaciones",
    "router_borrado_datos",
    "router_incidencias_suministro",
    "router_rechazos_atr",
    "router_admin"
]
