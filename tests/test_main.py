from fastapi.testclient import TestClient
from src.app_posventa.main import app
from src.app_posventa.models.enums import ModuleEnum, Priority

client = TestClient(app)

def test_health_endpoint():
    """Valida el endpoint /health exigido por Cloud Run y Safari Zone."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "app" in data

def test_web_dashboard():
    """Valida que la pantalla principal cargue con éxito en el navegador."""
    response = client.get("/")
    assert response.status_code == 200
    assert "APP POSVENTA" in response.text
    assert "Módulos de Operaciones" in response.text

def test_web_module_view():
    """Valida que la vista web de un módulo cargue con éxito las vistas Tabla y Panel."""
    response = client.get("/modulo/incidencias_contratos")
    assert response.status_code == 200
    assert "Vista Lista" in response.text
    assert "Vista Panel" in response.text
    assert "view-kanban-container" in response.text
    assert "En Proceso" in response.text

def test_create_ticket_api():
    """Valida la creación de un ticket vía API para el módulo de Incidencias de Contratos."""
    payload = {
        "module": ModuleEnum.INCIDENCIAS_CONTRATOS.value,
        "title": "Error en contrato firmado",
        "description": "El cliente reporta tarifa incorrecta en el documento final.",
        "customer_name": "Ana Gómez",
        "customer_email": "ana.gomez@example.com",
        "priority": Priority.ALTA.value
    }
    response = client.post("/api/v1/incidencias_contratos", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"].startswith("TCK-")
    assert data["title"] == payload["title"]
    assert data["module"] == ModuleEnum.INCIDENCIAS_CONTRATOS.value

def test_web_ticket_detail_workspace():
    """Valida la pantalla de detalle del ticket con 3/4 zona de trabajo y canal de correo."""
    response = client.get("/tickets/TCK-1001")
    assert response.status_code == 200
    assert "TCK-1001" in response.text
    assert "Poner Nota Interna" in response.text
    assert "Registrar Llamada" in response.text
    assert "Mandar Correo al Cliente" in response.text
    assert "tugestion@selectra.com" in response.text
    assert "Historial de Actividades" in response.text
    # Comprobar resaltado del módulo a la izquierda con #F6BE1A y texto negro
    assert "#F6BE1A" in response.text
    assert "color: #000000" in response.text or "text-black" in response.text

def test_ticket_actions_flow():
    """Valida el registro de notas, llamadas, correos y actualización de estado."""
    # 1. Añadir Nota Interna
    note_res = client.post(
        "/tickets/TCK-1001/notes",
        data={"content": "Nota de prueba automatizada para verificación de flujo."},
        follow_redirects=True
    )
    assert note_res.status_code == 200
    assert "Nota de prueba automatizada" in note_res.text

    # 2. Registrar Llamada
    call_res = client.post(
        "/tickets/TCK-1001/calls",
        data={
            "call_direction": "saliente",
            "phone": "+34 600 111 222",
            "outcome": "contactado",
            "duration": "5 min",
            "content": "Cliente conforme con la resolución propuesta."
        },
        follow_redirects=True
    )
    assert call_res.status_code == 200
    assert "Cliente conforme con la resolución propuesta." in call_res.text

    # 3. Mandar Correo al Cliente
    email_res = client.post(
        "/tickets/TCK-1001/emails",
        data={
            "recipient": "maria.garcia@example.com",
            "subject": "[#TCK-1001] Notificación oficial Selectra",
            "content": "Hola María, tu expediente ha sido tramitado con éxito."
        },
        follow_redirects=True
    )
    assert email_res.status_code == 200
    assert "Notificación oficial Selectra" in email_res.text

    # 4. Actualizar Estado
    status_res = client.post(
        "/tickets/TCK-1001/status",
        data={"new_status": "resuelto"},
        follow_redirects=True
    )
    assert status_res.status_code == 200
    assert "Resuelto" in status_res.text

def test_module_email_channels():
    """Valida los canales de correo según el módulo (tugestion, teayudamos, atencionalcliente)."""
    # Reclamaciones -> teayudamos@selectra.com
    res_rec = client.get("/tickets/TCK-1003")
    assert res_rec.status_code == 200
    assert "teayudamos@selectra.com" in res_rec.text

    # Atencion / Retencion -> atencionalcliente@selectra.com
    res_ret = client.get("/tickets/TCK-1004")
    assert res_ret.status_code == 200
    assert "atencionalcliente@selectra.com" in res_ret.text

def test_backoffice_module_renamed_and_categorization_fields():
    """Valida el renombre a Backoffice y la presencia de picklists y badges de categorización."""
    res = client.get("/modulo/incidencias_contratos")
    assert res.status_code == 200
    assert "Backoffice" in res.text
    assert "Categorización Backoffice" in res.text
    # Comprobar opciones de Resolución
    assert "Pendiente Gestor" in res.text
    assert "Escalado" in res.text
    assert "Cancelado por tiempo" in res.text
    # Comprobar opciones de Clasificación
    assert "Error grabación" in res.text
    assert "P0 (Titularidad)" in res.text
    # Comprobar opciones de Medio de recuperación
    assert "Auditoría" in res.text
    assert "Whatsapp" in res.text

def test_backoffice_ticket_picklists_update():
    """Valida que un ticket Backoffice actualice sus campos picklist (Resolución, Clasificación, Medio)."""
    # 1. Comprobar que en la vista de detalle salen los selectores y badges
    detail_res = client.get("/tickets/TCK-1001")
    assert detail_res.status_code == 200
    assert "Categorización Backoffice" in detail_res.text
    assert "Resolución" in detail_res.text
    assert "Clasificación" in detail_res.text
    assert "Medio de recuperación" in detail_res.text

    # 2. Actualizar campos mediante POST
    update_res = client.post(
        "/tickets/TCK-1001/backoffice_fields",
        data={
            "resolution": "Recuperado",
            "classification": "Error grabación",
            "recovery_channel": "Whatsapp"
        },
        follow_redirects=True
    )
    assert update_res.status_code == 200
    assert "Recuperado" in update_res.text
    assert "Error grabación" in update_res.text
    assert "Whatsapp" in update_res.text
    assert "Categorización actualizada" in update_res.text

def test_backoffice_create_ticket_with_picklists():
    """Valida la creación de un ticket en Backoffice con valores de picklist seleccionados."""
    create_res = client.post(
        "/modulo/incidencias_contratos/tickets",
        data={
            "title": "Incidencia titularidad Backoffice",
            "description": "El cliente solicita cambio P0 urgente.",
            "contract_reference": "DOC-2024-8831",
            "customer_name": "Laura Méndez",
            "priority": "alta",
            "resolution": "Escalado",
            "classification": "P0 (Titularidad)",
            "recovery_channel": "Llamada"
        },
        follow_redirects=True
    )
    assert create_res.status_code == 200
    assert "Incidencia titularidad Backoffice" in create_res.text
    assert "Escalado" in create_res.text
    assert "P0 (Titularidad)" in create_res.text
    assert "Llamada" in create_res.text

def test_whatsapp_tab_and_sending_flow():
    """Valida la presencia del espacio de WhatsApp, envío simulado de plantillas y trazabilidad en timeline."""
    # 1. Comprobar que el tab y formulario de WhatsApp existen en la vista del ticket
    detail_res = client.get("/tickets/TCK-1001?tab=whatsapp")
    assert detail_res.status_code == 200
    assert "WhatsApp" in detail_res.text
    assert "tab-btn-whatsapp" in detail_res.text
    assert "action-content-whatsapp" in detail_res.text
    assert "WhatsApp Business API" in detail_res.text
    assert "whatsapp-template-select" in detail_res.text
    assert "actualizacion_estado" in detail_res.text
    assert "solicitud_documentacion" in detail_res.text

    # 2. Enviar un mensaje de WhatsApp con plantilla oficial
    wa_res = client.post(
        "/tickets/TCK-1001/whatsapp",
        data={
            "phone": "+34 699 888 777",
            "template_name": "solicitud_documentacion",
            "content": "Hola María, necesitamos tu DNI para tramitar la gestión con Iberdrola Clientes."
        },
        follow_redirects=True
    )
    assert wa_res.status_code == 200
    assert "WhatsApp enviado" in wa_res.text
    assert "+34 699 888 777" in wa_res.text
    assert "Solicitud de Documentación" in wa_res.text
    assert "Hola María, necesitamos tu DNI" in wa_res.text
    assert "enviado" in wa_res.text.lower()


