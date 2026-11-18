import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from .config import settings
from .models.enums import (
    ModuleEnum,
    MODULE_METADATA,
    Role,
    TicketStatus,
    Priority,
    STATUS_METADATA,
    MODULE_EMAIL_CONFIG,
    BACKOFFICE_RESOLUCIONES,
    RESOLUCION_METADATA,
    BACKOFFICE_CLASIFICACIONES,
    CLASIFICACION_METADATA,
    BACKOFFICE_MEDIOS_RECUPERACION,
    MEDIO_RECUPERACION_METADATA
)
from .models.ticket import TicketCreate, TicketUpdate, ActivityType
from .models.user import User
from .models.email_config import ModuleEmailSetting, EmailTemplate
from .database.firestore import repo
from .auth.iap import get_current_user
from .auth.rbac import require_admin, require_module_access
from .services.nexus import nexus_client
from .services.reporting import filter_tickets, generate_tickets_csv, calculate_dashboard_metrics

from .modules.incidencias_contratos.router import router as router_incidencias_contratos
from .modules.atencion_retencion.router import router as router_atencion_retencion
from .modules.reclamaciones.router import router as router_reclamaciones
from .modules.borrado_datos.router import router as router_borrado_datos
from .modules.incidencias_suministro.router import router as router_incidencias_suministro
from .modules.rechazos_atr.router import router as router_rechazos_atr
from .modules.admin.router import router as router_admin

app = FastAPI(
    title=settings.app_name,
    description="Herramienta interna modular de Posventa Selectra con RBAC y autenticación corporativa IAP",
    version="1.0.0"
)

# Configuración de Plantillas Jinja2 para la Interfaz Web
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Registro de Routers de API
app.include_router(router_incidencias_contratos)
app.include_router(router_atencion_retencion)
app.include_router(router_reclamaciones)
app.include_router(router_borrado_datos)
app.include_router(router_incidencias_suministro)
app.include_router(router_rechazos_atr)
app.include_router(router_admin)

# -------------------------------------------------------------
# Endpoints de Sistema y Salud (Health Check para Cloud Run)
# -------------------------------------------------------------
@app.get("/health", tags=["Salud del Sistema"])
def health_check():
    """Endpoint de salud requerido por Cloud Run y Load Balancers."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "dev_mode": settings.dev_mode,
        "database": settings.firestore_database_id
    }

# -------------------------------------------------------------
# Rutas de Interfaz de Navegador (Web UI)
# -------------------------------------------------------------
@app.get("/", response_class=HTMLResponse, tags=["Interfaz Web"])
def web_dashboard(request: Request, current_user: User = Depends(get_current_user)):
    """Pantalla principal con métricas y módulos asignados al usuario."""
    # Filtrar tickets solo de los módulos que el usuario puede ver
    all_tickets = repo.list_tickets()
    accessible_tickets = [
        t for t in all_tickets if current_user.has_module_access(t.module)
    ]

    open_tickets = sum(1 for t in accessible_tickets if t.status in (TicketStatus.ABIERTO, TicketStatus.EN_PROCESO))
    urgent_tickets = sum(1 for t in accessible_tickets if t.priority == Priority.URGENTE and t.status != TicketStatus.CERRADO)
    accessible_count = len([m for m in ModuleEnum if current_user.has_module_access(m)])

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "current_user": current_user,
            "dev_mode": settings.dev_mode,
            "active_page": "dashboard",
            "modules_catalog": MODULE_METADATA,
            "accessible_modules_count": accessible_count,
            "total_tickets": len(accessible_tickets),
            "open_tickets": open_tickets,
            "urgent_tickets": urgent_tickets,
            "recent_tickets": accessible_tickets[:8]
        }
    )

@app.get("/modulo/{module_name}", response_class=HTMLResponse, tags=["Interfaz Web"])
def web_module_view(
    module_name: str,
    request: Request,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Vista detallada de un módulo específico y gestión de sus tickets."""
    try:
        mod_enum = ModuleEnum(module_name)
    except ValueError:
        raise HTTPException(status_code=404, detail="Módulo no reconocido.")

    if not current_user.has_module_access(mod_enum):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN if hasattr(status, 'HTTP_403_FORBIDDEN') else 403,
            detail=f"No tienes permisos asignados por el Administrador para acceder al módulo {mod_enum.value}."
        )

    status_filter = None
    if status:
        try:
            status_filter = TicketStatus(status)
        except ValueError:
            pass

    all_module_tickets = repo.list_tickets(module=mod_enum)
    tickets = [t for t in all_module_tickets if t.status == status_filter] if status_filter else all_module_tickets
    
    # Agrupar tickets por cada estado para la vista de panel (Kanban)
    tickets_by_status = {
        s: [t for t in all_module_tickets if t.status == s]
        for s in TicketStatus
    }

    return templates.TemplateResponse(
        request=request,
        name="module_tickets.html",
        context={
            "current_user": current_user,
            "dev_mode": settings.dev_mode,
            "active_page": mod_enum.value,
            "module_key": mod_enum.value,
            "module_info": MODULE_METADATA[mod_enum],
            "modules_catalog": MODULE_METADATA,
            "tickets": tickets,
            "all_tickets_count": len(all_module_tickets),
            "tickets_by_status": tickets_by_status,
            "statuses_catalog": STATUS_METADATA,
            "active_status": status or "",
            "resoluciones_catalog": BACKOFFICE_RESOLUCIONES,
            "resolucion_metadata": RESOLUCION_METADATA,
            "clasificaciones_catalog": BACKOFFICE_CLASIFICACIONES,
            "clasificacion_metadata": CLASIFICACION_METADATA,
            "medios_catalog": BACKOFFICE_MEDIOS_RECUPERACION,
            "medio_metadata": MEDIO_RECUPERACION_METADATA
        }
    )

@app.post("/modulo/{module_name}/tickets", tags=["Interfaz Web"])
def web_create_ticket(
    module_name: str,
    title: str = Form(...),
    description: str = Form(...),
    contract_reference: str = Form(...),
    customer_name: Optional[str] = Form(None),
    customer_surname: Optional[str] = Form(None),
    customer_phone: Optional[str] = Form(None),
    customer_email: Optional[str] = Form(None),
    company: Optional[str] = Form(None),
    department: Optional[str] = Form(None),
    priority: str = Form("media"),
    resolution: Optional[str] = Form(None),
    classification: Optional[str] = Form(None),
    recovery_channel: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user)
):
    """
    Crea un ticket en el módulo desde el formulario del navegador.
    El campo ID CONTRATO (contract_reference) es obligatorio para la apertura del ticket.
    Al crearse, consulta a Nexus Query API Assets mediante dicho ID y auto-completa:
    Nombre del cliente, Apellido, Mail, Compañía y Departamento.
    """
    mod_enum = ModuleEnum(module_name)
    if not current_user.has_module_access(mod_enum):
        raise HTTPException(status_code=403, detail="Sin permisos para este módulo.")

    contract_id = (contract_reference or "").strip()
    if not contract_id:
        raise HTTPException(
            status_code=400,
            detail="El campo ID CONTRATO es obligatorio para la apertura del ticket."
        )

    # Consultar Nexus Query API Assets para obtener datos del contrato
    nexus_contract = None
    cups_found = None
    try:
        nexus_contract = nexus_client.get_contract(contract_id)
    except Exception as e:
        logger.warning("Error al consultar contrato en Nexus durante la creación del ticket: %s", e)

    if nexus_contract:
        cust = nexus_contract.get("customer", {})
        prov = nexus_contract.get("provider", {})
        supply = nexus_contract.get("supply_details", {})

        # Si el usuario no especificó valores en el formulario, rellenamos desde Nexus
        if not customer_name:
            customer_name = cust.get("first_name") or cust.get("full_name")
        if not customer_surname:
            customer_surname = cust.get("last_name")
        if not customer_email:
            customer_email = cust.get("email")
        if not customer_phone:
            customer_phone = cust.get("phone")
        if not company:
            company = prov.get("name") or nexus_contract.get("company")
        if not department:
            department = nexus_contract.get("department") or nexus_contract.get("commodity_label") or nexus_contract.get("commodity")
        if supply.get("cups"):
            cups_found = supply.get("cups")

    ticket_in = TicketCreate(
        module=mod_enum,
        title=title,
        description=description,
        customer_name=customer_name.strip() if customer_name else None,
        customer_surname=customer_surname.strip() if customer_surname else None,
        customer_phone=customer_phone.strip() if customer_phone else None,
        customer_email=customer_email.strip() if customer_email else None,
        contract_reference=contract_id,
        cups=cups_found,
        company=company.strip() if company else None,
        department=department.strip() if department else None,
        priority=Priority(priority),
        resolution=resolution.strip() if resolution and resolution.strip() else None,
        classification=classification.strip() if classification and classification.strip() else None,
        recovery_channel=recovery_channel.strip() if recovery_channel and recovery_channel.strip() else None
    )
    new_ticket = repo.create_ticket(ticket_in=ticket_in, created_by=current_user.email)

    # Registrar actividad de apertura vinculada a Nexus
    if nexus_contract:
        repo.add_activity(
            ticket_id=new_ticket.id,
            activity_type=ActivityType.CATEGORIZATION,
            author=current_user.email,
            author_name=current_user.name or current_user.email.split("@")[0].replace(".", " ").title(),
            content=f"Ticket abierto con ID CONTRATO {contract_id}. Datos obtenidos de Nexus Assets: Titular: {new_ticket.customer_name or ''} {new_ticket.customer_surname or ''}, Compañía: {new_ticket.company or 'N/D'}, Dept: {new_ticket.department or 'N/D'}.",
            metadata={
                "source": "nexus_query_api_assets",
                "contract_id": contract_id,
                "company": new_ticket.company,
                "department": new_ticket.department
            }
        )

    return RedirectResponse(url=f"/modulo/{module_name}", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/modulo/{module_name}/tickets/{ticket_id}/status", tags=["Interfaz Web"])
def web_update_ticket_status(
    module_name: str,
    ticket_id: str,
    new_status: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    """Actualiza el estado de un ticket desde el desplegable del navegador."""
    mod_enum = ModuleEnum(module_name)
    if not current_user.has_module_access(mod_enum):
        raise HTTPException(status_code=403, detail="Sin permisos.")

    repo.update_ticket(ticket_id, TicketUpdate(status=TicketStatus(new_status)), updated_by=current_user.email)
    return RedirectResponse(url=f"/modulo/{module_name}", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/tickets/{ticket_id}", response_class=HTMLResponse, tags=["Interfaz Web"])
def web_ticket_detail(
    request: Request,
    ticket_id: str,
    tab: str = "notes",
    current_user: User = Depends(get_current_user)
):
    """
    Vista de trabajo del ticket: 3/4 zona de trabajo (notas, llamadas, emails)
    y 1/4 información y metadatos del ticket a la derecha.
    Permite abrir en pestaña nueva para trabajar en múltiples tickets simultáneamente.
    """
    ticket = repo.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    if not current_user.has_module_access(ticket.module):
        raise HTTPException(status_code=403, detail="No tienes permisos para acceder a este módulo.")

    module_info = MODULE_METADATA.get(ticket.module)
    email_setting = repo.get_module_email_setting(ticket.module)
    email_config = email_setting.model_dump()
    templates_list = repo.list_email_templates(module=ticket.module.value)
    templates_json = json.dumps([t.model_dump() for t in templates_list], default=str)

    nexus_contract = None
    ref_to_query = ticket.contract_reference or "DOC-2024-8831"
    try:
        nexus_contract = nexus_client.get_contract(ref_to_query)
    except Exception:
        nexus_contract = None

    return templates.TemplateResponse(
        request=request,
        name="ticket_detail.html",
        context={
            "current_user": current_user,
            "dev_mode": settings.dev_mode,
            "active_page": ticket.module.value,
            "is_ticket_view": True,
            "ticket": ticket,
            "module_key": ticket.module.value,
            "module_info": module_info,
            "modules_catalog": MODULE_METADATA,
            "statuses_catalog": STATUS_METADATA,
            "email_config": email_config,
            "email_templates": templates_list,
            "email_templates_json": templates_json,
            "active_tab": tab,
            "activities": ticket.activities,
            "resoluciones_catalog": BACKOFFICE_RESOLUCIONES,
            "resolucion_metadata": RESOLUCION_METADATA,
            "clasificaciones_catalog": BACKOFFICE_CLASIFICACIONES,
            "clasificacion_metadata": CLASIFICACION_METADATA,
            "medios_catalog": BACKOFFICE_MEDIOS_RECUPERACION,
            "medio_metadata": MEDIO_RECUPERACION_METADATA,
            "nexus_contract": nexus_contract,
            "nexus_ref_queried": ref_to_query
        }
    )

@app.post("/tickets/{ticket_id}/notes", tags=["Interfaz Web"])
def web_ticket_add_note(
    ticket_id: str,
    content: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    """Añade una nota interna al ticket y la registra en el timeline."""
    ticket = repo.get_ticket(ticket_id)
    if not ticket or not current_user.has_module_access(ticket.module):
        raise HTTPException(status_code=403, detail="Sin permisos para este ticket.")

    repo.add_activity(
        ticket_id=ticket_id,
        activity_type=ActivityType.NOTE,
        author=current_user.email,
        author_name=current_user.name or current_user.email.split("@")[0].replace(".", " ").title(),
        content=content.strip()
    )
    return RedirectResponse(url=f"/tickets/{ticket_id}?tab=notes", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/tickets/{ticket_id}/calls", tags=["Interfaz Web"])
def web_ticket_log_call(
    ticket_id: str,
    call_direction: str = Form(...),
    phone: str = Form(...),
    outcome: str = Form(...),
    duration: Optional[str] = Form(None),
    content: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    """Registra una llamada telefónica saliente o entrante con el cliente."""
    ticket = repo.get_ticket(ticket_id)
    if not ticket or not current_user.has_module_access(ticket.module):
        raise HTTPException(status_code=403, detail="Sin permisos para este ticket.")

    metadata = {
        "call_direction": call_direction,
        "phone": phone,
        "outcome": outcome,
        "duration": duration or ""
    }
    repo.add_activity(
        ticket_id=ticket_id,
        activity_type=ActivityType.CALL,
        author=current_user.email,
        author_name=current_user.name or current_user.email.split("@")[0].replace(".", " ").title(),
        content=content.strip(),
        metadata=metadata
    )
    return RedirectResponse(url=f"/tickets/{ticket_id}?tab=calls", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/tickets/{ticket_id}/emails", tags=["Interfaz Web"])
def web_ticket_send_email(
    ticket_id: str,
    recipient: str = Form(...),
    subject: str = Form(...),
    content: str = Form(...),
    cc: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user)
):
    """
    Envía y registra un correo electrónico al cliente usando el buzón
    oficial de Selectra asignado al módulo (tugestion@, teayudamos@, atencionalcliente@).
    """
    ticket = repo.get_ticket(ticket_id)
    if not ticket or not current_user.has_module_access(ticket.module):
        raise HTTPException(status_code=403, detail="Sin permisos para este ticket.")

    module_setting = repo.get_module_email_setting(ticket.module)
    sender_email = module_setting.email
    sender_name = module_setting.sender_name

    body_text = content.strip()
    if module_setting.signature and module_setting.signature.strip() not in body_text:
        body_text += f"\n\n{module_setting.signature.strip()}"
    if module_setting.rgpd_footer and module_setting.rgpd_footer.strip() not in body_text:
        body_text += f"\n\n---\n{module_setting.rgpd_footer.strip()}"

    metadata = {
        "sender": sender_email,
        "sender_name": sender_name,
        "channel_type": module_setting.account_type,
        "recipient": recipient.strip(),
        "cc": cc.strip() if cc else "",
        "subject": subject.strip(),
        "status": "enviado"
    }

    repo.add_activity(
        ticket_id=ticket_id,
        activity_type=ActivityType.EMAIL,
        author=current_user.email,
        author_name=current_user.name or current_user.email.split("@")[0].replace(".", " ").title(),
        content=body_text,
        metadata=metadata
    )
    return RedirectResponse(url=f"/tickets/{ticket_id}?tab=emails", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/tickets/{ticket_id}/whatsapp", tags=["Interfaz Web"])
def web_ticket_send_whatsapp(
    ticket_id: str,
    phone: str = Form(...),
    template_name: str = Form(...),
    content: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    """
    Envía y registra un mensaje de WhatsApp al cliente utilizando una plantilla predefinida
    a través de la integración de API de WhatsApp Business.
    """
    ticket = repo.get_ticket(ticket_id)
    if not ticket or not current_user.has_module_access(ticket.module):
        raise HTTPException(status_code=403, detail="Sin permisos para este ticket.")

    template_labels = {
        "actualizacion_estado": "Actualización de Estado de Gestión",
        "solicitud_documentacion": "Petición de Documentación Adicional",
        "resolucion_favorable": "Resolución Favorable del Caso",
        "contacto_pendiente": "Recordatorio de Contacto / Llamada",
        "mensaje_directo": "Plantilla Personalizada / Libre"
    }

    metadata = {
        "phone": phone.strip(),
        "template_name": template_name.strip(),
        "template_label": template_labels.get(template_name, template_name),
        "status": "enviado",
        "provider": "WhatsApp Business Cloud API (Simulado - Pendiente Endpoint)"
    }

    repo.add_activity(
        ticket_id=ticket_id,
        activity_type=ActivityType.WHATSAPP,
        author=current_user.email,
        author_name=current_user.name or current_user.email.split("@")[0].replace(".", " ").title(),
        content=content.strip(),
        metadata=metadata
    )
    return RedirectResponse(url=f"/tickets/{ticket_id}?tab=whatsapp", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/tickets/{ticket_id}/status", tags=["Interfaz Web"])
def web_ticket_detail_update_status(
    ticket_id: str,
    new_status: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    """Actualiza el estado de un ticket desde la pantalla de detalle."""
    ticket = repo.get_ticket(ticket_id)
    if not ticket or not current_user.has_module_access(ticket.module):
        raise HTTPException(status_code=403, detail="Sin permisos.")

    old_status_val = ticket.status.value
    target_status = TicketStatus(new_status)
    if ticket.status != target_status:
        repo.update_ticket(ticket_id, TicketUpdate(status=target_status), updated_by=current_user.email)
        old_title = STATUS_METADATA.get(TicketStatus(old_status_val), {}).get("title", old_status_val)
        new_title = STATUS_METADATA.get(target_status, {}).get("title", target_status.value)
        repo.add_activity(
            ticket_id=ticket_id,
            activity_type=ActivityType.STATUS_CHANGE,
            author=current_user.email,
            author_name=current_user.name or current_user.email.split("@")[0].replace(".", " ").title(),
            content=f"Estado actualizado de '{old_title}' a '{new_title}'.",
            metadata={"old_status": old_status_val, "new_status": target_status.value}
        )
    return RedirectResponse(url=f"/tickets/{ticket_id}", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/tickets/{ticket_id}/backoffice_fields", tags=["Interfaz Web"])
def web_ticket_update_backoffice_fields(
    ticket_id: str,
    resolution: Optional[str] = Form(None),
    classification: Optional[str] = Form(None),
    recovery_channel: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user)
):
    """Actualiza los campos de categorización (Resolución, Clasificación, Medio de Recuperación) del ticket Backoffice."""
    ticket = repo.get_ticket(ticket_id)
    if not ticket or not current_user.has_module_access(ticket.module):
        raise HTTPException(status_code=403, detail="Sin permisos.")

    res_clean = resolution.strip() if resolution and resolution.strip() else None
    cla_clean = classification.strip() if classification and classification.strip() else None
    med_clean = recovery_channel.strip() if recovery_channel and recovery_channel.strip() else None

    changes = []
    if res_clean != ticket.resolution:
        changes.append(f"Resolución: '{ticket.resolution or 'Sin asignar'}' ➔ '{res_clean or 'Sin asignar'}'")
    if cla_clean != ticket.classification:
        changes.append(f"Clasificación: '{ticket.classification or 'Sin asignar'}' ➔ '{cla_clean or 'Sin asignar'}'")
    if med_clean != ticket.recovery_channel:
        changes.append(f"Medio de recuperación: '{ticket.recovery_channel or 'Sin asignar'}' ➔ '{med_clean or 'Sin asignar'}'")

    if changes:
        repo.update_ticket(
            ticket_id,
            TicketUpdate(
                resolution=res_clean,
                classification=cla_clean,
                recovery_channel=med_clean
            ),
            updated_by=current_user.email
        )
        repo.add_activity(
            ticket_id=ticket_id,
            activity_type=ActivityType.CATEGORIZATION,
            author=current_user.email,
            author_name=current_user.name or current_user.email.split("@")[0].replace(".", " ").title(),
            content="Actualización de categorización Backoffice: " + "; ".join(changes),
            metadata={
                "resolution": res_clean,
                "classification": cla_clean,
                "recovery_channel": med_clean
            }
        )

    return RedirectResponse(url=f"/tickets/{ticket_id}", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/admin/roles", response_class=HTMLResponse, tags=["Interfaz Web"])
def web_admin_roles(
    request: Request,
    saved_user: Optional[str] = None,
    admin_user: User = Depends(require_admin)
):
    """Pantalla del Administrador para configurar roles y acceso a módulos por usuario."""
    users = repo.list_users()
    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            "current_user": admin_user,
            "dev_mode": settings.dev_mode,
            "active_page": "admin_roles",
            "modules_catalog": MODULE_METADATA,
            "users": users,
            "saved_user": saved_user
        }
    )

@app.post("/admin/roles/{user_email}", tags=["Interfaz Web"])
def web_admin_update_roles(
    request: Request,
    user_email: str,
    role: str = Form(...),
    modules: List[str] = Form(default=[]),
    admin_user: User = Depends(require_admin)
):
    """Guarda los cambios de rol y módulos asignados a un usuario."""
    user = repo.get_user(user_email)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    user.role = Role(role)
    if user.role == Role.ADMIN:
        user.allowed_modules = list(ModuleEnum)
    else:
        user.allowed_modules = [ModuleEnum(m) for m in modules if m in [e.value for e in ModuleEnum]]

    repo.save_user(user)

    as_user = request.query_params.get("as_user")
    user_display = user.name or user.email
    redirect_url = f"/admin/roles?saved_user={user_display}"
    if as_user:
        redirect_url += f"&as_user={as_user}"
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)


# ============================================================================
# CONFIGURACIÓN DE CORREO, FIRMAS, RGPD Y PLANTILLAS (EXCLUSIVO ADMINISTRADORES)
# ============================================================================

@app.get("/admin/configuracion", response_class=HTMLResponse, tags=["Configuración"])
def web_admin_configuracion(
    request: Request,
    tab: str = "cuentas",
    saved_module: Optional[str] = None,
    saved_tpl: Optional[str] = None,
    deleted_tpl: Optional[str] = None,
    admin_user: User = Depends(require_admin)
):
    """Pantalla del Administrador para configurar cuentas de correo, firmas, RGPD y plantillas."""
    email_settings = repo.get_email_settings()
    templates_list = repo.list_email_templates()

    return templates.TemplateResponse(
        request=request,
        name="admin_config.html",
        context={
            "current_user": admin_user,
            "dev_mode": settings.dev_mode,
            "active_page": "admin_configuracion",
            "modules_catalog": MODULE_METADATA,
            "email_settings": email_settings,
            "templates": templates_list,
            "active_tab": tab,
            "saved_module": saved_module,
            "saved_tpl": saved_tpl,
            "deleted_tpl": deleted_tpl
        }
    )

@app.post("/admin/configuracion/emails", tags=["Configuración"])
def web_admin_save_email_config(
    request: Request,
    module: str = Form(...),
    email: str = Form(...),
    sender_name: str = Form(...),
    account_type: str = Form("google_group"),
    signature: Optional[str] = Form(None),
    rgpd_footer: Optional[str] = Form(None),
    tab: str = Form("cuentas"),
    admin_user: User = Depends(require_admin)
):
    """Guarda la configuración de cuenta de correo, firma y RGPD para un módulo específico."""
    mod_enum = ModuleEnum(module)
    setting = ModuleEmailSetting(
        module=mod_enum,
        email=email.strip(),
        sender_name=sender_name.strip(),
        account_type=account_type.strip(),
        type_label="Bandeja de Grupo de Google Workspace" if account_type == "google_group" else "Cuenta Individual Google Workspace (Usuario y Contraseña)",
        signature=signature.strip() if signature else "",
        rgpd_footer=rgpd_footer.strip() if rgpd_footer else ""
    )
    repo.save_module_email_setting(setting)

    as_user = request.query_params.get("as_user")
    mod_title = MODULE_METADATA.get(mod_enum, {}).get("title", module)
    redirect_url = f"/admin/configuracion?tab={tab}&saved_module={mod_title}"
    if as_user:
        redirect_url += f"&as_user={as_user}"
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)

@app.post("/admin/configuracion/plantillas", tags=["Configuración"])
def web_admin_save_email_template(
    request: Request,
    template_id: Optional[str] = Form(None),
    name: str = Form(...),
    module: str = Form(...),
    subject: str = Form(...),
    body: str = Form(...),
    admin_user: User = Depends(require_admin)
):
    """Crea o actualiza una plantilla de correo electrónico corporativo."""
    if template_id and template_id.strip():
        existing = repo.get_email_template(template_id.strip())
        if existing:
            existing.name = name.strip()
            existing.module = module.strip()
            existing.subject = subject.strip()
            existing.body = body.strip()
            repo.save_email_template(existing)
        else:
            new_tpl = EmailTemplate(
                id=template_id.strip(),
                name=name.strip(),
                module=module.strip(),
                subject=subject.strip(),
                body=body.strip()
            )
            repo.save_email_template(new_tpl)
    else:
        new_tpl = EmailTemplate(
            name=name.strip(),
            module=module.strip(),
            subject=subject.strip(),
            body=body.strip()
        )
        repo.save_email_template(new_tpl)

    as_user = request.query_params.get("as_user")
    redirect_url = "/admin/configuracion?tab=plantillas&saved_tpl=1"
    if as_user:
        redirect_url += f"&as_user={as_user}"
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)

@app.post("/admin/configuracion/plantillas/{template_id}/delete", tags=["Configuración"])
def web_admin_delete_email_template(
    request: Request,
    template_id: str,
    admin_user: User = Depends(require_admin)
):
    """Elimina una plantilla de correo electrónico del catálogo."""
    repo.delete_email_template(template_id)

    as_user = request.query_params.get("as_user")
    redirect_url = "/admin/configuracion?tab=plantillas&deleted_tpl=1"
    if as_user:
        redirect_url += f"&as_user={as_user}"
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)


# ============================================================================
# INFORMES Y DASHBOARD ANALÍTICO (EXCLUSIVO ADMINISTRADORES)
# ============================================================================

@app.get("/admin/informes", response_class=HTMLResponse, tags=["Informes y Analítica"])
def web_admin_informes(
    request: Request,
    module: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    admin_user: User = Depends(require_admin)
):
    """Generador y previsualizador de informes de tickets con filtros por módulo y rango de fechas."""
    all_tickets = repo.list_tickets()
    filtered = filter_tickets(
        tickets=all_tickets,
        module_key=module,
        start_date=start_date,
        end_date=end_date
    )
    total_results = len(filtered)
    open_results = sum(1 for t in filtered if t.status in (TicketStatus.ABIERTO, TicketStatus.EN_PROCESO, TicketStatus.ESPERA_CLIENTE))
    closed_results = sum(1 for t in filtered if t.status in (TicketStatus.RESUELTO, TicketStatus.CERRADO))
    urgent_results = sum(1 for t in filtered if t.priority == Priority.URGENTE and t.status != TicketStatus.CERRADO)

    return templates.TemplateResponse(
        request=request,
        name="admin_informes.html",
        context={
            "current_user": admin_user,
            "dev_mode": settings.dev_mode,
            "active_page": "admin_informes",
            "modules_catalog": MODULE_METADATA,
            "status_meta": STATUS_METADATA,
            "selected_module": module or "todos",
            "start_date": start_date or "",
            "end_date": end_date or "",
            "tickets": filtered,
            "total_results": total_results,
            "open_results": open_results,
            "closed_results": closed_results,
            "urgent_results": urgent_results
        }
    )

@app.get("/admin/informes/export", tags=["Informes y Analítica"])
def web_admin_informes_export(
    module: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    admin_user: User = Depends(require_admin)
):
    """Descarga de informe de tickets filtrados en formato CSV (delimitado por ';' para Excel en español)."""
    all_tickets = repo.list_tickets()
    filtered = filter_tickets(
        tickets=all_tickets,
        module_key=module,
        start_date=start_date,
        end_date=end_date
    )
    csv_content = generate_tickets_csv(filtered)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    mod_tag = module if module and module != "todos" else "todos_modulos"
    filename = f"informe_tickets_{mod_tag}_{timestamp}.csv"

    return Response(
        content=csv_content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )

@app.get("/admin/dashboard", response_class=HTMLResponse, tags=["Informes y Analítica"])
def web_admin_dashboard(
    request: Request,
    module: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    admin_user: User = Depends(require_admin)
):
    """Dashboard analítico exclusivo para administradores con selector de módulo, fechas y gráficas de estado."""
    all_tickets = repo.list_tickets()
    filtered = filter_tickets(
        tickets=all_tickets,
        module_key=module,
        start_date=start_date,
        end_date=end_date
    )
    metrics = calculate_dashboard_metrics(filtered, module_key=module)

    current_module_title = "Todos los módulos"
    if module and module != "todos":
        try:
            mod_enum = ModuleEnum(module)
            current_module_title = MODULE_METADATA.get(mod_enum, {}).get("title", module)
        except ValueError:
            current_module_title = module

    return templates.TemplateResponse(
        request=request,
        name="admin_dashboard.html",
        context={
            "current_user": admin_user,
            "dev_mode": settings.dev_mode,
            "active_page": "admin_dashboard",
            "modules_catalog": MODULE_METADATA,
            "status_meta": STATUS_METADATA,
            "selected_module": module or "todos",
            "current_module_title": current_module_title,
            "start_date": start_date or "",
            "end_date": end_date or "",
            "metrics": metrics
        }
    )

@app.get("/informes", tags=["Informes y Analítica"])
def redirect_to_admin_informes(admin_user: User = Depends(require_admin)):
    """Acceso directo o alias a la sección de Informes."""
    return RedirectResponse(url="/admin/informes", status_code=status.HTTP_307_TEMPORARY_REDIRECT)


# ============================================================================
# INTEGRACIÓN NEXUS - QUERY API - ASSETS (Selectra-Dev/nexus-query-api-assets)
# ============================================================================

@app.get("/api/v1/nexus/contracts/{contract_id}", tags=["Nexus Query API"])
def api_get_nexus_contract(contract_id: str, current_user: User = Depends(get_current_user)):
    """Consulta un contrato en Nexus Query API Assets mediante contract_id (ID de documento)."""
    contract = nexus_client.get_contract(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail=f"Contrato '{contract_id}' no encontrado en Nexus Assets.")
    return {"status": "success", "data": contract}

@app.post("/tickets/{ticket_id}/sync_nexus", tags=["Interfaz Web"])
def web_sync_nexus_contract(
    ticket_id: str,
    contract_id: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    """Sincroniza los datos del contrato de Nexus Assets con el ticket actual."""
    ticket = repo.get_ticket(ticket_id)
    if not ticket or not current_user.has_module_access(ticket.module):
        raise HTTPException(status_code=403, detail="Sin permisos para este ticket.")

    contract = nexus_client.get_contract(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail=f"No se encontró el contrato '{contract_id}' en Nexus.")

    # Actualizar campos del ticket con datos oficiales de Nexus
    customer_data = contract.get("customer", {})
    supply_data = contract.get("supply_details", {})
    provider_data = contract.get("provider", {})

    repo.update_ticket(
        ticket_id,
        TicketUpdate(
            customer_name=customer_data.get("first_name") or customer_data.get("full_name") or ticket.customer_name,
            customer_surname=customer_data.get("last_name") or ticket.customer_surname,
            customer_email=customer_data.get("email") or ticket.customer_email,
            customer_phone=customer_data.get("phone") or ticket.customer_phone,
            company=provider_data.get("name") or contract.get("company") or ticket.company,
            department=contract.get("department") or contract.get("commodity_label") or ticket.department,
            cups=supply_data.get("cups") or ticket.cups,
            contract_reference=contract.get("contract_id") or contract_id
        ),
        updated_by=current_user.email
    )

    # Registrar actividad de auditoría en el timeline
    repo.add_activity(
        ticket_id=ticket_id,
        activity_type=ActivityType.CATEGORIZATION,
        author=current_user.email,
        author_name=current_user.name or current_user.email.split("@")[0].replace(".", " ").title(),
        content=f"Datos sincronizados con Nexus Assets (Doc ID: {contract_id}). Titular: {ticket.customer_name or ''} {ticket.customer_surname or ''}, Proveedor: {ticket.company}, Dept: {ticket.department}, CUPS: {ticket.cups}.",
        metadata={
            "source": "nexus_query_api_assets",
            "contract_id": contract_id,
            "provider": ticket.company,
            "department": ticket.department,
            "cups": ticket.cups,
            "tariff": provider_data.get("tariff_name")
        }
    )

    return RedirectResponse(url=f"/tickets/{ticket_id}", status_code=status.HTTP_303_SEE_OTHER)
