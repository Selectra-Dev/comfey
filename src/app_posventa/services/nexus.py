"""
Cliente del microservicio Nexus - Query API - Assets (Selectra-Dev/nexus-query-api-assets).
Permite consultar contratos y activos en Nexus mediante contract_id (ID de documento).
Cumple con la arquitectura Zero-Key de Safari Zone en Google Cloud Run.
"""
import os
import logging
from typing import Optional, Dict, Any
import httpx

logger = logging.getLogger(__name__)

# Catálogo mock de contratos realistas para desarrollo local y pruebas
MOCK_CONTRACTS: Dict[str, Dict[str, Any]] = {
    "cnt_8f93a102b4c5": {
        "contract_id": "cnt_8f93a102b4c5",
        "status": "active",
        "status_label": "Activo",
        "commodity": "electricity",
        "commodity_label": "Electricidad",
        "department": "Electricidad",
        "provider": {
            "id": "prov_totalenergies",
            "name": "TotalEnergies",
            "tariff_code": "PLAN_SIEMPRE_LUZ",
            "tariff_name": "Plan Siempre Luz"
        },
        "customer": {
            "customer_id": "cust_129841",
            "full_name": "Juan Pérez Gómez",
            "first_name": "Juan",
            "last_name": "Pérez Gómez",
            "doc_type": "DNI",
            "doc_number": "12345678Z",
            "email": "juan.perez@example.com",
            "phone": "+34 600 112 233"
        },
        "supply_details": {
            "cups": "ES0031405999999999AB0F",
            "address": "Calle Gran Vía 28, 4º B, 28013 Madrid",
            "power_p1_kw": 4.6,
            "power_p2_kw": 4.6
        },
        "billing": {
            "iban_masked": "ES91••••••••••••1234",
            "payment_method": "direct_debit"
        },
        "lifecycle": {
            "signed_at": "2024-03-15T11:20:00Z",
            "activation_date": "2024-03-20",
            "created_at": "2024-03-15T10:45:22Z",
            "updated_at": "2024-04-01T08:12:05Z"
        },
        "metadata": {
            "source_channel": "web_comparator",
            "agent_id": "posventa-agent-12"
        }
    },
    "DOC-2024-8831": {
        "contract_id": "DOC-2024-8831",
        "status": "pending_validation",
        "status_label": "Pendiente Validación",
        "commodity": "electricity",
        "commodity_label": "Electricidad",
        "department": "Electricidad",
        "provider": {
            "id": "prov_iberdrola",
            "name": "Iberdrola Clientes",
            "tariff_code": "PLAN_ONLINE_LUZ",
            "tariff_name": "Plan Online Luz 24h"
        },
        "customer": {
            "customer_id": "cust_445890",
            "full_name": "María García López",
            "first_name": "María",
            "last_name": "García López",
            "doc_type": "DNI",
            "doc_number": "45678912K",
            "email": "maria.garcia@example.com",
            "phone": "+34 699 888 777"
        },
        "supply_details": {
            "cups": "ES0021000001234567AB",
            "address": "Calle Alcalá 45, 2º Izq, 28014 Madrid",
            "power_p1_kw": 3.45,
            "power_p2_kw": 3.45
        },
        "billing": {
            "iban_masked": "ES44••••••••••••5678",
            "payment_method": "direct_debit"
        },
        "lifecycle": {
            "signed_at": "2024-04-02T14:10:00Z",
            "activation_date": None,
            "created_at": "2024-04-02T14:05:00Z",
            "updated_at": "2024-04-02T14:15:00Z"
        },
        "metadata": {
            "source_channel": "telesales",
            "agent_id": "gestor-selectra-04"
        }
    },
    "DOC-2024-9942": {
        "contract_id": "DOC-2024-9942",
        "status": "active",
        "status_label": "Activo",
        "commodity": "gas",
        "commodity_label": "Gas Natural",
        "department": "Gas Natural",
        "provider": {
            "id": "prov_naturgy",
            "name": "Naturgy",
            "tariff_code": "POR_USO_GAS_RL2",
            "tariff_name": "Tarifa Por Uso Gas RL.2"
        },
        "customer": {
            "customer_id": "cust_771902",
            "full_name": "Carlos Sánchez Ruiz",
            "first_name": "Carlos",
            "last_name": "Sánchez Ruiz",
            "doc_type": "DNI",
            "doc_number": "34567890M",
            "email": "carlos.sanchez@example.com",
            "phone": "+34 611 223 344"
        },
        "supply_details": {
            "cups": "ES0230000009876543CD",
            "address": "Avinguda Diagonal 200, 5º 1ª, 08018 Barcelona",
            "power_p1_kw": 0.0,
            "power_p2_kw": 0.0
        },
        "billing": {
            "iban_masked": "ES12••••••••••••9012",
            "payment_method": "direct_debit"
        },
        "lifecycle": {
            "signed_at": "2024-02-18T09:30:00Z",
            "activation_date": "2024-02-23",
            "created_at": "2024-02-18T09:00:00Z",
            "updated_at": "2024-02-24T10:00:00Z"
        },
        "metadata": {
            "source_channel": "backoffice",
            "agent_id": "gestor-selectra-09"
        }
    }
}


class NexusClient:
    """Cliente para interactuar con la Query API de Assets de Nexus."""

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.base_url = (base_url or os.getenv("NEXUS_QUERY_API_ASSETS_URL", "")).rstrip("/")
        self.api_key = api_key or os.getenv("NEXUS_API_KEY", "")

    def is_mock_mode(self) -> bool:
        """Determina si debemos operar en modo simulado para desarrollo local."""
        if not self.base_url or "xxxxx" in self.base_url or "localhost" in self.base_url:
            return True
        return False

    def _get_auth_headers(self) -> Dict[str, str]:
        """Genera las cabeceras de autenticación (OIDC en GCP / API Key fallback)."""
        headers = {"Accept": "application/json"}
        if self.is_mock_mode():
            return headers

        # Intentar obtener Google ID Token (OIDC) para invocación Cloud Run a Cloud Run
        try:
            from google.auth.transport.requests import Request
            from google.oauth2 import id_token
            auth_req = Request()
            bearer_token = id_token.fetch_id_token(auth_req, self.base_url)
            headers["Authorization"] = f"Bearer {bearer_token}"
            return headers
        except Exception as e:
            logger.warning(f"No se pudo obtener Google ID Token para Nexus: {e}")

        # Fallback si se utiliza API Key
        if self.api_key:
            headers["X-API-Key"] = self.api_key

        return headers

    def get_contract(self, contract_id: str) -> Optional[Dict[str, Any]]:
        """
        Consulta un contrato por su identificador único (ID de documento en Nexus).
        Devuelve el diccionario con los datos del contrato o None si no existe.
        """
        contract_id = (contract_id or "").strip()
        if not contract_id:
            return None

        # 1. Modo Simulado / Mock para desarrollo local
        if self.is_mock_mode():
            # Si coincide con uno de los ejemplos predefinidos
            if contract_id in MOCK_CONTRACTS:
                return self._normalize_contract_data(dict(MOCK_CONTRACTS[contract_id]))

            # Si el usuario introduce cualquier otro contract_id no vacío, generamos un contrato realista
            # derivado de ese ID para facilitarle pruebas inmediatas
            contract = {
                "contract_id": contract_id,
                "status": "active",
                "status_label": "Activo",
                "commodity": "electricity",
                "commodity_label": "Electricidad",
                "department": "Electricidad",
                "provider": {
                    "id": "prov_selectra_partner",
                    "name": "Iberdrola Clientes",
                    "tariff_code": "PLAN_FLEXIBLE_ONLINE",
                    "tariff_name": "Plan Flexible Online"
                },
                "customer": {
                    "customer_id": f"cust_{abs(hash(contract_id)) % 1000000}",
                    "full_name": f"Titular {contract_id}",
                    "first_name": "Titular",
                    "last_name": f"{contract_id}",
                    "doc_type": "DNI",
                    "doc_number": f"{10000000 + (abs(hash(contract_id)) % 89999999)}A",
                    "email": f"cliente.{contract_id.lower().replace('-', '').replace('_', '')[:10]}@example.com",
                    "phone": "+34 650 000 111"
                },
                "supply_details": {
                    "cups": f"ES00210000{abs(hash(contract_id)) % 10000000000:010d}AB",
                    "address": "Calle Gran Vía 10, 28013 Madrid",
                    "power_p1_kw": 4.6,
                    "power_p2_kw": 4.6
                },
                "billing": {
                    "iban_masked": "ES88••••••••••••4321",
                    "payment_method": "direct_debit"
                },
                "lifecycle": {
                    "signed_at": "2024-04-01T10:00:00Z",
                    "activation_date": "2024-04-05",
                    "created_at": "2024-04-01T09:45:00Z",
                    "updated_at": "2024-04-05T12:00:00Z"
                },
                "metadata": {
                    "source_channel": "nexus_query_api_assets",
                    "mock_generated": True
                }
            }
            return self._normalize_contract_data(contract)

        # 2. Conexión Real al endpoint de Cloud Run
        url = f"{self.base_url}/v1/contracts/{contract_id}"
        headers = self._get_auth_headers()

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, headers=headers)
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                payload = response.json()
                # Adaptar estructura si viene envuelta en {"data": ...}
                if isinstance(payload, dict) and "data" in payload:
                    contract = payload["data"]
                else:
                    contract = payload
                return self._normalize_contract_data(contract)
        except Exception as e:
            logger.error(f"Error al consultar contrato en Nexus Query API ({url}): {e}")
            raise RuntimeError(f"Error de comunicación con Nexus Query API: {e}")

    def _normalize_contract_data(self, contract: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Asegura que campos clave como first_name, last_name, company y department estén normalizados."""
        if not contract or not isinstance(contract, dict):
            return contract

        cust = contract.setdefault("customer", {})
        if "first_name" not in cust or "last_name" not in cust:
            full = (cust.get("full_name") or "").strip()
            if full:
                parts = full.split(" ", 1)
                cust["first_name"] = parts[0]
                cust["last_name"] = parts[1] if len(parts) > 1 else ""
            else:
                cust["first_name"] = ""
                cust["last_name"] = ""

        prov = contract.get("provider", {})
        if "company" not in contract:
            contract["company"] = prov.get("name") or ""

        if "department" not in contract:
            contract["department"] = contract.get("commodity_label") or contract.get("commodity") or "Electricidad"

        return contract

# Instancia singleton del cliente para toda la aplicación
nexus_client = NexusClient()
