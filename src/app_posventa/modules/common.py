from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from ..models.enums import ModuleEnum, TicketStatus
from ..models.ticket import Ticket, TicketCreate, TicketUpdate, TicketNote
from ..models.user import User
from ..auth.rbac import require_module_access
from ..database.firestore import repo

def create_module_router(module: ModuleEnum, tags: List[str]) -> APIRouter:
    """
    Crea un router FastAPI para un módulo específico con control RBAC automático.
    """
    router = APIRouter(
        prefix=f"/api/v1/{module.value}",
        tags=tags,
        dependencies=[Depends(require_module_access(module))]
    )

    @router.get("", response_model=List[Ticket])
    def list_module_tickets(
        status_filter: Optional[TicketStatus] = None,
        current_user: User = Depends(require_module_access(module))
    ):
        """Lista todos los tickets asociados a este módulo con filtrado opcional."""
        return repo.list_tickets(module=module, status=status_filter)

    @router.post("", response_model=Ticket, status_code=status.HTTP_201_CREATED)
    def create_module_ticket(
        ticket_in: TicketCreate,
        current_user: User = Depends(require_module_access(module))
    ):
        """Crea un nuevo ticket en este módulo asignando al creador."""
        # Forzar el módulo correspondiente al endpoint
        ticket_in.module = module
        if ticket_in.contract_reference:
            try:
                from ..services.nexus import nexus_client
                nexus_contract = nexus_client.get_contract(ticket_in.contract_reference)
                if nexus_contract:
                    cust = nexus_contract.get("customer", {})
                    prov = nexus_contract.get("provider", {})
                    supply = nexus_contract.get("supply_details", {})
                    if not ticket_in.customer_name:
                        ticket_in.customer_name = cust.get("first_name") or cust.get("full_name")
                    if not ticket_in.customer_surname:
                        ticket_in.customer_surname = cust.get("last_name")
                    if not ticket_in.customer_email:
                        ticket_in.customer_email = cust.get("email")
                    if not ticket_in.company:
                        ticket_in.company = prov.get("name") or nexus_contract.get("company")
                    if not ticket_in.department:
                        ticket_in.department = nexus_contract.get("department") or nexus_contract.get("commodity_label")
                    if not ticket_in.cups and supply.get("cups"):
                        ticket_in.cups = supply.get("cups")
            except Exception:
                pass
        return repo.create_ticket(ticket_in=ticket_in, created_by=current_user.email)

    @router.get("/{ticket_id}", response_model=Ticket)
    def get_module_ticket(
        ticket_id: str,
        current_user: User = Depends(require_module_access(module))
    ):
        """Obtiene el detalle completo de un ticket."""
        ticket = repo.get_ticket(ticket_id)
        if not ticket or ticket.module != module:
            raise HTTPException(status_code=404, detail="Ticket no encontrado en este módulo.")
        return ticket

    @router.patch("/{ticket_id}", response_model=Ticket)
    def update_module_ticket(
        ticket_id: str,
        update_in: TicketUpdate,
        current_user: User = Depends(require_module_access(module))
    ):
        """Actualiza el estado, prioridad o asignación del ticket."""
        ticket = repo.get_ticket(ticket_id)
        if not ticket or ticket.module != module:
            raise HTTPException(status_code=404, detail="Ticket no encontrado en este módulo.")
        
        updated = repo.update_ticket(ticket_id, update_in, updated_by=current_user.email)
        return updated

    @router.post("/{ticket_id}/notes", response_model=Ticket)
    def add_ticket_note(
        ticket_id: str,
        note_text: str,
        current_user: User = Depends(require_module_access(module))
    ):
        """Añade una nota o comentario al historial del ticket."""
        ticket = repo.get_ticket(ticket_id)
        if not ticket or ticket.module != module:
            raise HTTPException(status_code=404, detail="Ticket no encontrado en este módulo.")
        
        updated = repo.add_note(ticket_id, author=current_user.email, content=note_text)
        return updated

    return router
