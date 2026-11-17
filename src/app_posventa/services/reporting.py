import csv
import io
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from ..models.ticket import Ticket
from ..models.enums import (
    ModuleEnum,
    TicketStatus,
    Priority,
    MODULE_METADATA,
    STATUS_METADATA
)

PRIORITY_METADATA = {
    Priority.URGENTE: {"title": "Urgente", "color": "#DC2626", "badge_bg": "bg-red-50", "badge_text": "text-red-700"},
    Priority.ALTA: {"title": "Alta", "color": "#EA580C", "badge_bg": "bg-orange-50", "badge_text": "text-orange-700"},
    Priority.MEDIA: {"title": "Media", "color": "#D97706", "badge_bg": "bg-amber-50", "badge_text": "text-amber-700"},
    Priority.BAJA: {"title": "Baja", "color": "#16A34A", "badge_bg": "bg-emerald-50", "badge_text": "text-emerald-700"},
}

def parse_date(date_str: Optional[str]) -> Optional[date]:
    """Parsea una cadena en formato YYYY-MM-DD a objeto date de forma segura."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
    except (ValueError, AttributeError):
        return None

def filter_tickets(
    tickets: List[Ticket],
    module_key: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status_key: Optional[str] = None
) -> List[Ticket]:
    """
    Filtra una lista de tickets según módulo, rango de fechas y/o estado.
    """
    parsed_start = parse_date(start_date)
    parsed_end = parse_date(end_date)
    
    filtered = []
    for t in tickets:
        # Filtro de módulo
        if module_key and module_key != "todos":
            mod_val = t.module.value if hasattr(t.module, "value") else str(t.module)
            if mod_val != module_key:
                continue

        # Filtro de fecha inicio
        if parsed_start:
            ticket_date = t.created_at.date() if hasattr(t.created_at, "date") else None
            if ticket_date and ticket_date < parsed_start:
                continue

        # Filtro de fecha fin
        if parsed_end:
            ticket_date = t.created_at.date() if hasattr(t.created_at, "date") else None
            if ticket_date and ticket_date > parsed_end:
                continue

        # Filtro de estado opcional
        if status_key and status_key != "todos":
            stat_val = t.status.value if hasattr(t.status, "value") else str(t.status)
            if stat_val != status_key:
                continue

        filtered.append(t)

    return sorted(filtered, key=lambda x: x.created_at, reverse=True)

def generate_tickets_csv(tickets: List[Ticket]) -> str:
    """
    Genera un documento CSV delimitado por punto y coma (;) y con BOM UTF-8 (\ufeff)
    para máxima compatibilidad con Microsoft Excel y LibreOffice en español.
    """
    output = io.StringIO()
    # Escribir BOM UTF-8 para que Excel reconozca tildes y caracteres españoles
    output.write("\ufeff")
    writer = csv.writer(output, delimiter=";", quoting=csv.QUOTE_MINIMAL)

    headers = [
        "ID Ticket",
        "ID Contrato",
        "Módulo",
        "Título",
        "Descripción",
        "Nombre Cliente",
        "Apellido Cliente",
        "Nombre Completo",
        "Email",
        "Teléfono",
        "Compañía / Proveedor",
        "Departamento",
        "CUPS",
        "Prioridad",
        "Estado",
        "Resolución",
        "Clasificación",
        "Medio Recuperación",
        "Asignado a",
        "Creado por",
        "Fecha Creación",
        "Fecha Actualización"
    ]
    writer.writerow(headers)

    for t in tickets:
        mod_name = MODULE_METADATA.get(t.module, {}).get("title", t.module.value if hasattr(t.module, "value") else str(t.module))
        status_name = STATUS_METADATA.get(t.status, {}).get("title", t.status.value if hasattr(t.status, "value") else str(t.status))
        prio_val = t.priority.value if hasattr(t.priority, "value") else str(t.priority)
        
        created_str = t.created_at.strftime("%Y-%m-%d %H:%M:%S") if t.created_at else ""
        updated_str = t.updated_at.strftime("%Y-%m-%d %H:%M:%S") if t.updated_at else ""

        # Limpieza básica para celdas multilínea o nulas
        desc_clean = (t.description or "").replace("\r\n", " ").replace("\n", " ").strip()

        row = [
            t.id or "",
            t.contract_reference or "",
            mod_name,
            t.title or "",
            desc_clean,
            t.customer_name or "",
            t.customer_surname or "",
            t.full_customer_name if hasattr(t, "full_customer_name") else f"{t.customer_name or ''} {t.customer_surname or ''}".strip(),
            t.customer_email or "",
            t.customer_phone or "",
            t.company or "",
            t.department or "",
            t.cups or "",
            prio_val.upper(),
            status_name,
            t.resolution or "",
            t.classification or "",
            t.recovery_channel or "",
            t.assigned_to or "Sin asignar",
            t.created_by or "",
            created_str,
            updated_str
        ]
        writer.writerow(row)

    return output.getvalue()

def calculate_dashboard_metrics(
    tickets: List[Ticket],
    module_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calcula los indicadores clave (KPIs) y las agregaciones por estado,
    prioridad y módulo para el Dashboard del Administrador.
    """
    total = len(tickets)
    
    # Conteo por estados
    status_counts = {}
    for st in TicketStatus:
        count = sum(1 for t in tickets if t.status == st)
        pct = round((count / total) * 100, 1) if total > 0 else 0.0
        meta = STATUS_METADATA.get(st, {})
        status_counts[st.value] = {
            "key": st.value,
            "title": meta.get("title", st.value),
            "count": count,
            "percentage": pct,
            "color": meta.get("color", "#6B7280"),
            "badge_bg": meta.get("badge_bg", "bg-gray-100"),
            "badge_text": meta.get("badge_text", "text-gray-700"),
            "icon": meta.get("icon", "fa-circle")
        }

    # Conteo por prioridad
    priority_counts = {}
    for pr in Priority:
        count = sum(1 for t in tickets if t.priority == pr)
        pct = round((count / total) * 100, 1) if total > 0 else 0.0
        meta = PRIORITY_METADATA.get(pr, {})
        priority_counts[pr.value] = {
            "key": pr.value,
            "title": meta.get("title", pr.value.capitalize()),
            "count": count,
            "percentage": pct,
            "color": meta.get("color", "#6B7280"),
            "badge_bg": meta.get("badge_bg", "bg-gray-100"),
            "badge_text": meta.get("badge_text", "text-gray-700")
        }

    # Conteo por módulo (para comparar cuando se ve 'todos')
    module_counts = {}
    for mod in ModuleEnum:
        count = sum(1 for t in tickets if t.module == mod)
        meta = MODULE_METADATA.get(mod, {})
        module_counts[mod.value] = {
            "key": mod.value,
            "title": meta.get("title", mod.value),
            "count": count,
            "icon": meta.get("icon", "briefcase")
        }

    # KPIs principales
    active_count = sum(1 for t in tickets if t.status in (TicketStatus.ABIERTO, TicketStatus.EN_PROCESO, TicketStatus.ESPERA_CLIENTE))
    resolved_count = sum(1 for t in tickets if t.status == TicketStatus.RESUELTO)
    closed_count = sum(1 for t in tickets if t.status == TicketStatus.CERRADO)
    urgent_count = sum(1 for t in tickets if t.priority == Priority.URGENTE and t.status != TicketStatus.CERRADO)
    resolution_rate = round(((resolved_count + closed_count) / total) * 100, 1) if total > 0 else 0.0

    return {
        "total_tickets": total,
        "active_tickets": active_count,
        "resolved_tickets": resolved_count,
        "closed_tickets": closed_count,
        "urgent_tickets": urgent_count,
        "resolution_rate": resolution_rate,
        "status_counts": status_counts,
        "priority_counts": priority_counts,
        "module_counts": module_counts,
        "recent_tickets": tickets[:8]
    }
