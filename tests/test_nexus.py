import pytest
from fastapi.testclient import TestClient
from src.app_posventa.main import app
from src.app_posventa.services.nexus import nexus_client

client = TestClient(app)

def test_nexus_client_mock_retrieval():
    """Verifica que el cliente de Nexus obtenga contratos válidos por contract_id (ID documento)."""
    # 1. Contrato predefinido DOC-2024-8831 (Iberdrola)
    contract_iberdrola = nexus_client.get_contract("DOC-2024-8831")
    assert contract_iberdrola is not None
    assert contract_iberdrola["contract_id"] == "DOC-2024-8831"
    assert contract_iberdrola["provider"]["name"] == "Iberdrola Clientes"
    assert contract_iberdrola["customer"]["full_name"] == "María García López"
    assert "cups" in contract_iberdrola["supply_details"]

    # 2. Contrato predefinido cnt_8f93a102b4c5 (TotalEnergies)
    contract_total = nexus_client.get_contract("cnt_8f93a102b4c5")
    assert contract_total is not None
    assert contract_total["contract_id"] == "cnt_8f93a102b4c5"
    assert contract_total["provider"]["name"] == "TotalEnergies"

    # 3. ID dinámico
    contract_custom = nexus_client.get_contract("DOC-PRUEBA-999")
    assert contract_custom is not None
    assert contract_custom["contract_id"] == "DOC-PRUEBA-999"

def test_api_get_nexus_contract_endpoint():
    """Valida el endpoint REST GET /api/v1/nexus/contracts/{contract_id}."""
    response = client.get("/api/v1/nexus/contracts/DOC-2024-8831")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["contract_id"] == "DOC-2024-8831"
    assert data["data"]["provider"]["name"] == "Iberdrola Clientes"

def test_ticket_detail_shows_nexus_widget():
    """Valida que la pantalla del ticket contenga el buscador y visualizador de Nexus."""
    response = client.get("/tickets/TCK-1001")
    assert response.status_code == 200
    assert "Nexus Assets" in response.text
    assert "nexus-card-container" in response.text
    assert "nexus-search-input" in response.text
    assert "nexus-search-btn" in response.text
    assert "DOC-2024-8831" in response.text
    assert "Sincronizar datos al Ticket" in response.text

def test_sync_nexus_contract_with_ticket():
    """Valida el flujo de sincronización de datos de Nexus hacia el ticket."""
    response = client.post(
        "/tickets/TCK-1001/sync_nexus",
        data={"contract_id": "cnt_8f93a102b4c5"},
        follow_redirects=True
    )
    assert response.status_code == 200
    # Verifica que el ticket actualizó sus datos con TotalEnergies
    assert "TotalEnergies" in response.text
    assert "Juan Pérez Gómez" in response.text
    assert "ES0031405999999999AB0F" in response.text
    assert "Datos sincronizados con Nexus Assets" in response.text

def test_ticket_creation_requires_contract_reference():
    """Valida que el campo ID CONTRATO sea obligatorio para la apertura de tickets."""
    # 1. Petición sin contract_reference debe fallar
    res_missing = client.post(
        "/modulo/incidencias_contratos/tickets",
        data={
            "title": "Incidencia sin contrato",
            "description": "Debe fallar porque falta ID CONTRATO",
        }
    )
    assert res_missing.status_code == 422  # Error de validación de campo obligatorio

    # 2. Petición con contract_reference vacío debe responder 400
    res_empty = client.post(
        "/modulo/incidencias_contratos/tickets",
        data={
            "title": "Incidencia con ID vacío",
            "description": "Debe fallar porque está en blanco",
            "contract_reference": "   "
        }
    )
    assert res_empty.status_code == 400
    assert "ID CONTRATO es obligatorio" in res_empty.json()["detail"]

def test_ticket_creation_auto_populates_from_nexus():
    """Valida que al crear un ticket con ID CONTRATO se consulte Nexus y se rellene Nombre, Apellido, Mail, Compañía y Departamento."""
    from src.app_posventa.database.firestore import repo

    # Crear ticket pasando solo el ID CONTRATO 'DOC-2024-8831'
    res = client.post(
        "/modulo/incidencias_contratos/tickets",
        data={
            "title": "Reclamación tarifa no respetada",
            "description": "Cliente indica discrepancia con contrato",
            "contract_reference": "DOC-2024-8831",
            "priority": "alta"
        },
        follow_redirects=True
    )
    assert res.status_code == 200

    # Comprobar que en el repositorio el último ticket tiene los datos de Nexus
    tickets = repo.list_tickets()
    created_ticket = next((t for t in tickets if t.contract_reference == "DOC-2024-8831" and t.title == "Reclamación tarifa no respetada"), None)
    assert created_ticket is not None
    assert created_ticket.customer_name == "María"
    assert created_ticket.customer_surname == "García López"
    assert created_ticket.customer_email == "maria.garcia@example.com"
    assert created_ticket.company == "Iberdrola Clientes"
    assert created_ticket.department == "Electricidad"

    # Verificar que el detalle del ticket muestra los datos correctamente
    detail_res = client.get(f"/tickets/{created_ticket.id}")
    assert detail_res.status_code == 200
    assert "María García López" in detail_res.text
    assert "Iberdrola Clientes" in detail_res.text
    assert "Electricidad" in detail_res.text
    assert "DOC-2024-8831" in detail_res.text
