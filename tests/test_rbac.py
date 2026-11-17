from fastapi.testclient import TestClient
from src.app_posventa.main import app
from src.app_posventa.models.enums import ModuleEnum, Role
from src.app_posventa.models.user import User
from src.app_posventa.database.firestore import repo

client = TestClient(app)

def test_rbac_module_forbidden_for_unauthorized_user():
    """Un agente sin permisos para rechazos_atr recibe un 403 Forbidden."""
    agent_email = "agente.limitado@selectra.com"
    repo.save_user(User(
        email=agent_email,
        name="Agente Sin Acceso ATR",
        role=Role.AGENT,
        allowed_modules=[ModuleEnum.RECLAMACIONES],  # Solo reclamaciones
        is_active=True
    ))

    # Intento de acceso a rechazos_atr simulando el agente limitado
    response = client.get("/api/v1/rechazos_atr", params={"as_user": agent_email})
    assert response.status_code == 403
    assert "no dispones de permisos" in response.json()["detail"]

def test_rbac_module_allowed_for_authorized_user():
    """El mismo agente sí puede consultar reclamaciones porque tiene acceso."""
    agent_email = "agente.limitado@selectra.com"
    response = client.get("/api/v1/reclamaciones", params={"as_user": agent_email})
    assert response.status_code == 200

def test_admin_can_update_permissions():
    """El Administrador puede otorgar nuevos módulos a un agente."""
    target_email = "agente.posventa@selectra.com"
    payload = {
        "role": "agent",
        "allowed_modules": [
            ModuleEnum.INCIDENCIAS_CONTRATOS.value,
            ModuleEnum.RECHAZOS_ATR.value
        ]
    }
    response = client.post(
        f"/api/v1/admin/users/{target_email}/permissions",
        json=payload,
        params={"as_user": "carlos.alfageme@selectra.com"}  # Admin
    )
    assert response.status_code == 200
    updated_user = response.json()
    assert ModuleEnum.RECHAZOS_ATR.value in updated_user["allowed_modules"]
