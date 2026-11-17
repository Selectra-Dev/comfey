from enum import Enum

class Role(str, Enum):
    ADMIN = "admin"
    AGENT = "agent"

class ModuleEnum(str, Enum):
    INCIDENCIAS_CONTRATOS = "incidencias_contratos"
    ATENCION_RETENCION = "atencion_retencion"
    RECLAMACIONES = "reclamaciones"
    BORRADO_DATOS = "borrado_datos"
    INCIDENCIAS_SUMINISTRO = "incidencias_suministro"
    RECHAZOS_ATR = "rechazos_atr"

MODULE_METADATA = {
    ModuleEnum.INCIDENCIAS_CONTRATOS: {
        "title": "Backoffice",
        "description": "Gestión de incidencias y operativa en contratos formalizados.",
        "icon": "briefcase"
    },
    ModuleEnum.ATENCION_RETENCION: {
        "title": "Atención al Cliente, Retención y Fidelización",
        "description": "Atención prioritaria para evitar bajas y fidelizar cartera de clientes.",
        "icon": "heart"
    },
    ModuleEnum.RECLAMACIONES: {
        "title": "Gestión de Reclamaciones",
        "description": "Reclamaciones formales de clientes hacia distribuidoras, comercializadoras o servicio.",
        "icon": "exclamation-triangle"
    },
    ModuleEnum.BORRADO_DATOS: {
        "title": "Peticiones de Borrado de Datos (GDPR)",
        "description": "Solicitudes de ejercicio de derechos ARCO/GDPR y eliminación de datos personales.",
        "icon": "trash"
    },
    ModuleEnum.INCIDENCIAS_SUMINISTRO: {
        "title": "Incidencias en Altas de Suministro (Luz y Gas)",
        "description": "Seguimiento y desbloqueo de altas técnicas y activaciones con distribuidoras.",
        "icon": "bolt"
    },
    ModuleEnum.RECHAZOS_ATR: {
        "title": "Rechazos ATR de Compañías",
        "description": "Gestión de errores y códigos de rechazo en las solicitudes de acceso a la red (ATR).",
        "icon": "shield-exclamation"
    }
}

MODULE_EMAIL_CONFIG = {
    ModuleEnum.INCIDENCIAS_CONTRATOS: {
        "email": "tugestion@selectra.com",
        "name": "Selectra Posventa - Backoffice",
        "account_type": "google_group",
        "type_label": "Bandeja de Grupo de Google Workspace",
        "description": "Bandeja colaborativa de grupo para gestión de backoffice e incidencias de contratos",
        "badge_bg": "bg-sky-50",
        "badge_text": "text-[#125DA5]",
        "border_color": "border-[#125DA5]/30",
        "icon": "fa-users"
    },
    ModuleEnum.INCIDENCIAS_SUMINISTRO: {
        "email": "tugestion@selectra.com",
        "name": "Selectra Posventa - Altas de Suministro",
        "account_type": "google_group",
        "type_label": "Bandeja de Grupo de Google Workspace",
        "description": "Bandeja colaborativa de grupo para seguimiento de altas de luz y gas",
        "badge_bg": "bg-sky-50",
        "badge_text": "text-[#125DA5]",
        "border_color": "border-[#125DA5]/30",
        "icon": "fa-users"
    },
    ModuleEnum.RECLAMACIONES: {
        "email": "teayudamos@selectra.com",
        "name": "Selectra Reclamaciones - Te Ayudamos",
        "account_type": "google_group",
        "type_label": "Bandeja de Grupo de Google Workspace",
        "description": "Bandeja colaborativa de grupo para gestión formal de reclamaciones",
        "badge_bg": "bg-teal-50",
        "badge_text": "text-[#4799B7]",
        "border_color": "border-[#4799B7]/30",
        "icon": "fa-people-group"
    },
    ModuleEnum.ATENCION_RETENCION: {
        "email": "atencionalcliente@selectra.com",
        "name": "Selectra - Atención al Cliente y Fidelización",
        "account_type": "user_password",
        "type_label": "Cuenta Individual Google Workspace (Usuario y Contraseña)",
        "description": "Buzón corporativo autenticado con credenciales de usuario",
        "badge_bg": "bg-indigo-50",
        "badge_text": "text-[#1861C3]",
        "border_color": "border-[#1861C3]/30",
        "icon": "fa-user-lock"
    },
    ModuleEnum.RECHAZOS_ATR: {
        "email": "tugestion@selectra.com",
        "name": "Selectra Posventa - Rechazos ATR",
        "account_type": "google_group",
        "type_label": "Bandeja de Grupo de Google Workspace",
        "description": "Bandeja colaborativa de grupo para subsanación de rechazos de distribuidora",
        "badge_bg": "bg-sky-50",
        "badge_text": "text-[#125DA5]",
        "border_color": "border-[#125DA5]/30",
        "icon": "fa-users"
    },
    ModuleEnum.BORRADO_DATOS: {
        "email": "teayudamos@selectra.com",
        "name": "Selectra Privacidad - Ejercicio Derechos RGPD",
        "account_type": "google_group",
        "type_label": "Bandeja de Grupo de Google Workspace",
        "description": "Bandeja colaborativa de grupo para solicitudes de derechos y RGPD",
        "badge_bg": "bg-teal-50",
        "badge_text": "text-[#4799B7]",
        "border_color": "border-[#4799B7]/30",
        "icon": "fa-shield-halved"
    }
}

class TicketStatus(str, Enum):
    ABIERTO = "abierto"
    EN_PROCESO = "en_proceso"
    ESPERA_CLIENTE = "espera_cliente"
    RESUELTO = "resuelto"
    CERRADO = "cerrado"

STATUS_METADATA = {
    TicketStatus.ABIERTO: {
        "key": "abierto",
        "title": "Abierto",
        "color": "#1861C3",
        "badge_bg": "bg-blue-50",
        "badge_text": "text-[#1861C3]",
        "border_color": "border-[#1861C3]",
        "icon": "fa-folder-open"
    },
    TicketStatus.EN_PROCESO: {
        "key": "en_proceso",
        "title": "En Proceso",
        "color": "#125DA5",
        "badge_bg": "bg-sky-50",
        "badge_text": "text-[#125DA5]",
        "border_color": "border-[#125DA5]",
        "icon": "fa-arrows-rotate"
    },
    TicketStatus.ESPERA_CLIENTE: {
        "key": "espera_cliente",
        "title": "En Espera Cliente",
        "color": "#4799B7",
        "badge_bg": "bg-teal-50",
        "badge_text": "text-[#4799B7]",
        "border_color": "border-[#4799B7]",
        "icon": "fa-clock"
    },
    TicketStatus.RESUELTO: {
        "key": "resuelto",
        "title": "Resuelto",
        "color": "#10B981",
        "badge_bg": "bg-emerald-50",
        "badge_text": "text-emerald-700",
        "border_color": "border-emerald-500",
        "icon": "fa-circle-check"
    },
    TicketStatus.CERRADO: {
        "key": "cerrado",
        "title": "Cerrado",
        "color": "#64748B",
        "badge_bg": "bg-gray-100",
        "badge_text": "text-gray-600",
        "border_color": "border-gray-400",
        "icon": "fa-lock"
    }
}

# ==============================================================================
# Campos y Picklists específicos para el módulo de BACKOFFICE
# ==============================================================================

BACKOFFICE_RESOLUCIONES = [
    "Nuevo",
    "Pendiente Gestor",
    "Escalado",
    "Cita",
    "Tratando",
    "Recuperado",
    "No recuperado",
    "Recuperado Gestor / comercial",
    "Cancelado Gestor / comercial",
    "Cancelado por tiempo"
]

RESOLUCION_METADATA = {
    "Nuevo": {
        "badge_bg": "bg-blue-50",
        "badge_text": "text-[#1861C3]",
        "border": "border-blue-200",
        "icon": "fa-sparkles"
    },
    "Pendiente Gestor": {
        "badge_bg": "bg-amber-50",
        "badge_text": "text-amber-800",
        "border": "border-amber-200",
        "icon": "fa-user-clock"
    },
    "Escalado": {
        "badge_bg": "bg-purple-50",
        "badge_text": "text-purple-700",
        "border": "border-purple-200",
        "icon": "fa-turn-up"
    },
    "Cita": {
        "badge_bg": "bg-indigo-50",
        "badge_text": "text-indigo-700",
        "border": "border-indigo-200",
        "icon": "fa-calendar-check"
    },
    "Tratando": {
        "badge_bg": "bg-sky-50",
        "badge_text": "text-[#125DA5]",
        "border": "border-sky-200",
        "icon": "fa-arrows-rotate"
    },
    "Recuperado": {
        "badge_bg": "bg-emerald-50",
        "badge_text": "text-emerald-700",
        "border": "border-emerald-200",
        "icon": "fa-circle-check"
    },
    "No recuperado": {
        "badge_bg": "bg-rose-50",
        "badge_text": "text-rose-700",
        "border": "border-rose-200",
        "icon": "fa-circle-xmark"
    },
    "Recuperado Gestor / comercial": {
        "badge_bg": "bg-teal-50",
        "badge_text": "text-teal-700",
        "border": "border-teal-200",
        "icon": "fa-user-check"
    },
    "Cancelado Gestor / comercial": {
        "badge_bg": "bg-gray-100",
        "badge_text": "text-gray-700",
        "border": "border-gray-200",
        "icon": "fa-ban"
    },
    "Cancelado por tiempo": {
        "badge_bg": "bg-stone-100",
        "badge_text": "text-stone-600",
        "border": "border-stone-200",
        "icon": "fa-hourglass-end"
    }
}

BACKOFFICE_CLASIFICACIONES = [
    "Error grabación",
    "Error lectura",
    "Peaje / potencia",
    "Error datos",
    "Precios",
    "Documentación",
    "P0 (Titularidad)"
]

CLASIFICACION_METADATA = {
    "Error grabación": {"icon": "fa-microphone-slash", "badge_bg": "bg-red-50", "badge_text": "text-red-700"},
    "Error lectura": {"icon": "fa-gauge-high", "badge_bg": "bg-orange-50", "badge_text": "text-orange-700"},
    "Peaje / potencia": {"icon": "fa-bolt-lightning", "badge_bg": "bg-amber-50", "badge_text": "text-amber-700"},
    "Error datos": {"icon": "fa-triangle-exclamation", "badge_bg": "bg-yellow-50", "badge_text": "text-yellow-800"},
    "Precios": {"icon": "fa-tag", "badge_bg": "bg-sky-50", "badge_text": "text-sky-700"},
    "Documentación": {"icon": "fa-file-invoice", "badge_bg": "bg-blue-50", "badge_text": "text-blue-700"},
    "P0 (Titularidad)": {"icon": "fa-id-card", "badge_bg": "bg-purple-50", "badge_text": "text-purple-700"}
}

BACKOFFICE_MEDIOS_RECUPERACION = [
    "Auditoría",
    "Llamada",
    "Mail",
    "Whatsapp"
]

MEDIO_RECUPERACION_METADATA = {
    "Auditoría": {"icon": "fa-clipboard-check", "badge_bg": "bg-slate-100", "badge_text": "text-slate-700"},
    "Llamada": {"icon": "fa-phone-volume", "badge_bg": "bg-indigo-50", "badge_text": "text-[#1861C3]"},
    "Mail": {"icon": "fa-envelope", "badge_bg": "bg-sky-50", "badge_text": "text-[#125DA5]"},
    "Whatsapp": {"icon": "fa-brands fa-whatsapp", "badge_bg": "bg-emerald-50", "badge_text": "text-emerald-700"}
}

class Priority(str, Enum):
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    URGENTE = "urgente"
