import pytest
from datetime import datetime, date, timedelta
from fastapi.testclient import TestClient
from src.app_posventa.main import app
from src.app_posventa.database.firestore import repo
from src.app_posventa.models.enums import ModuleEnum, TicketStatus, Priority
from src.app_posventa.models.ticket import TicketCreate
from src.app_posventa.services.reporting import filter_tickets, generate_tickets_csv, calculate_dashboard_metrics

client = TestClient(app)

ADMIN_USER = "carlos.alfageme@selectra.com"
AGENT_USER = "agente.posventa@selectra.com"

def test_admin_informes_forbidden_for_agent():
    """Verifica que un usuario sin rol de administrador no pueda acceder a Informes."""
    # Intentar acceder a la vista de informes
    res_view = client.get(f"/admin/informes?as_user={AGENT_USER}")
    assert res_view.status_code == 403
    assert "administrador" in res_view.text.lower()

    # Intentar descargar el CSV
    res_export = client.get(f"/admin/informes/export?as_user={AGENT_USER}")
    assert res_export.status_code == 403

    # Intentar acceder por la ruta alias
    res_alias = client.get(f"/informes?as_user={AGENT_USER}")
    assert res_alias.status_code == 403

def test_admin_dashboard_forbidden_for_agent():
    """Verifica que un agente sin rol admin reciba 403 en el Dashboard de administrador."""
    res = client.get(f"/admin/dashboard?as_user={AGENT_USER}")
    assert res.status_code == 403
    assert "administrador" in res.text.lower()

def test_admin_informes_accessible_for_admin():
    """Verifica que el usuario administrador pueda acceder a Informes."""
    res = client.get(f"/admin/informes?as_user={ADMIN_USER}")
    assert res.status_code == 200
    assert "Informes de Tickets" in res.text
    assert "Módulo Posventa:" in res.text
    assert "Descargar CSV" in res.text

def test_admin_dashboard_accessible_for_admin():
    """Verifica que el usuario administrador pueda acceder al Dashboard con sus métricas y gráficas."""
    res = client.get(f"/admin/dashboard?as_user={ADMIN_USER}")
    assert res.status_code == 200
    assert "Dashboard de Rendimiento y Estados" in res.text
    assert "Distribución de Tickets por Estado" in res.text
    assert "statusDoughnutChart" in res.text
    assert "statusBarChart" in res.text
    assert "Módulo a Visualizar:" in res.text

def test_informes_filtering_by_module_and_date():
    """Verifica el filtrado de tickets por módulo y fechas."""
    # Crear dos tickets de prueba
    t1 = repo.create_ticket(
        TicketCreate(
            module=ModuleEnum.INCIDENCIAS_CONTRATOS,
            title="Ticket Backoffice Test Filtros",
            description="Descripción prueba filtros",
            customer_name="Prueba Modulo",
            contract_reference="CNT-MOD-101",
            priority=Priority.MEDIA
        ),
        created_by=ADMIN_USER
    )

    t2 = repo.create_ticket(
        TicketCreate(
            module=ModuleEnum.RECLAMACIONES,
            title="Ticket Reclamaciones Test Filtros",
            description="Descripción prueba filtros 2",
            customer_name="Prueba Reclama",
            contract_reference="REC-MOD-202",
            priority=Priority.ALTA
        ),
        created_by=ADMIN_USER
    )

    all_tickets = repo.list_tickets()
    
    # Filtrar solo Backoffice
    backoffice_only = filter_tickets(all_tickets, module_key=ModuleEnum.INCIDENCIAS_CONTRATOS.value)
    assert any(t.id == t1.id for t in backoffice_only)
    assert not any(t.id == t2.id for t in backoffice_only)

    # Filtrar solo Reclamaciones
    reclamaciones_only = filter_tickets(all_tickets, module_key=ModuleEnum.RECLAMACIONES.value)
    assert any(t.id == t2.id for t in reclamaciones_only)
    assert not any(t.id == t1.id for t in reclamaciones_only)

    # Filtrar por fecha hoy
    today_str = date.today().strftime("%Y-%m-%d")
    today_tickets = filter_tickets(all_tickets, start_date=today_str, end_date=today_str)
    assert any(t.id == t1.id for t in today_tickets)
    assert any(t.id == t2.id for t in today_tickets)

    # Filtrar con fecha pasada (hace 10 días) donde no debe haber tickets creados hoy
    past_date = (date.today() - timedelta(days=10)).strftime("%Y-%m-%d")
    empty_tickets = filter_tickets(all_tickets, start_date=past_date, end_date=past_date)
    assert not any(t.id == t1.id for t in empty_tickets)

def test_csv_export_endpoint():
    """Verifica que la descarga de CSV sea correcta, delimitada por punto y coma y con BOM UTF-8."""
    # Crear un ticket con caracteres especiales en español (tildes, eñe)
    t = repo.create_ticket(
        TicketCreate(
            module=ModuleEnum.INCIDENCIAS_CONTRATOS,
            title="Gestión de Reclamación con Ñ y Acentos",
            description="Explicación detallada del caso del señor Núñez",
            customer_name="Álvaro",
            customer_surname="Núñez Peña",
            customer_email="alvaro.nunez@example.com",
            contract_reference="CNT-ES-99",
            company="Iberdrola España",
            department="Energía",
            cups="ES0031400000000012ZZ",
            priority=Priority.URGENTE
        ),
        created_by=ADMIN_USER
    )

    res = client.get(f"/admin/informes/export?module=incidencias_contratos&as_user={ADMIN_USER}")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert "attachment; filename=" in res.headers["content-disposition"]
    
    csv_text = res.text
    # Verificar BOM UTF-8
    assert csv_text.startswith("\ufeff")
    
    # Verificar cabecera delimitada por ';'
    assert "ID Ticket;ID Contrato;Módulo;Título;Descripción;" in csv_text
    assert "Fecha Actualización" in csv_text

    # Verificar que el registro está presente con sus datos
    assert t.id in csv_text
    assert "CNT-ES-99" in csv_text
    assert "Álvaro Núñez Peña" in csv_text
    assert "Iberdrola España" in csv_text
    assert "Energía" in csv_text

def test_dashboard_metrics_calculation():
    """Verifica los cálculos del agregador de métricas del Dashboard."""
    tickets = repo.list_tickets()
    metrics = calculate_dashboard_metrics(tickets)

    assert "total_tickets" in metrics
    assert "active_tickets" in metrics
    assert "resolved_tickets" in metrics
    assert "closed_tickets" in metrics
    assert "urgent_tickets" in metrics
    assert "resolution_rate" in metrics
    assert "status_counts" in metrics
    assert "priority_counts" in metrics
    assert "module_counts" in metrics

    assert metrics["total_tickets"] >= 6
    assert 0 <= metrics["resolution_rate"] <= 100
    assert metrics["status_counts"]["abierto"]["count"] >= 1
