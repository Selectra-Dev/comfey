import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from ..config import settings
from ..models.enums import ModuleEnum, Role, TicketStatus, Priority, MODULE_EMAIL_CONFIG
from ..models.user import User
from ..models.ticket import Ticket, TicketCreate, TicketUpdate, TicketNote, TicketActivity, ActivityType, utc_now
from ..models.email_config import ModuleEmailSetting, EmailTemplate, DEFAULT_RGPD_FOOTER, DEFAULT_SIGNATURE_TEMPLATE

logger = logging.getLogger(__name__)

class DataRepository:
    """
    Capa de acceso a datos que interactúa con Google Cloud Firestore en producción
    (Zero-Key con ADC) y proporciona almacenamiento en memoria con datos de ejemplo
    para desarrollo local cuando no hay credenciales ADC activas.
    """
    def __init__(self):
        self._firestore_client = None
        self._using_fallback = False
        self._memory_users: Dict[str, User] = {}
        self._memory_tickets: Dict[str, Ticket] = {}
        self._memory_email_settings: Dict[str, ModuleEmailSetting] = {}
        self._memory_email_templates: Dict[str, EmailTemplate] = {}
        self._init_client()
        self._seed_default_data()

    def _init_client(self):
        try:
            from google.cloud import firestore
            self._firestore_client = firestore.Client(
                project=settings.project_id,
                database=settings.firestore_database_id
            )
            # Intento de ping simple para verificar si ADC está activo
            self._firestore_client.collection("_ping").limit(1).get()
            logger.info("Conectado con éxito a Google Cloud Firestore (Base: %s)", settings.firestore_database_id)
        except Exception as e:
            logger.warning(
                "Firestore no disponible en entorno local (%s). "
                "Activando repositorio local simulado en memoria para desarrollo.", e
            )
            self._using_fallback = True

    def _seed_default_data(self):
        # Usuario Administrador por defecto
        admin_email = settings.dev_user_email.lower()
        self._memory_users[admin_email] = User(
            email=admin_email,
            name="Carlos Alfageme (Admin)",
            role=Role.ADMIN,
            allowed_modules=list(ModuleEnum),
            is_active=True
        )

        # Usuario Agente de ejemplo para pruebas de permisos
        agent_email = "agente.posventa@selectra.com"
        self._memory_users[agent_email] = User(
            email=agent_email,
            name="Agente Suministros y Reclamaciones",
            role=Role.AGENT,
            allowed_modules=[ModuleEnum.INCIDENCIAS_SUMINISTRO, ModuleEnum.RECLAMACIONES],
            is_active=True
        )

        # Sembrar tickets de ejemplo en memoria para diferentes módulos y canales de correo
        sample_tickets = [
            Ticket(
                id="TCK-1001",
                module=ModuleEnum.INCIDENCIAS_CONTRATOS,
                title="Error en tarifa aplicada contrato Endesa",
                description="El cliente indica que se le prometió tarifa fija y en la confirmación sale indexada.",
                customer_name="María García",
                customer_email="maria.garcia@example.com",
                customer_phone="+34 600 111 222",
                contract_reference="CNT-2026-9812",
                company="Endesa",
                priority=Priority.ALTA,
                status=TicketStatus.EN_PROCESO,
                resolution="Tratando",
                classification="Precios",
                recovery_channel="Llamada",
                created_by=admin_email,
                created_at=utc_now(),
                updated_at=utc_now(),
                activities=[
                    TicketActivity(
                        id="ACT-001",
                        activity_type=ActivityType.CALL,
                        author=admin_email,
                        author_name="Carlos Alfageme",
                        content="Llamada al cliente para contrastar la oferta comercial acordada. Confirma que se pactó tarifa fija a 12 meses.",
                        created_at=utc_now(),
                        metadata={
                            "call_direction": "saliente",
                            "phone": "+34 600 111 222",
                            "outcome": "contactado",
                            "duration": "4 min"
                        }
                    ),
                    TicketActivity(
                        id="ACT-002",
                        activity_type=ActivityType.EMAIL,
                        author=admin_email,
                        author_name="Carlos Alfageme",
                        content="Estimada María,\n\nHemos abierto la reclamación interna ante Endesa para solicitar la corrección a tarifa fija según la grabación de venta.\n\nTe mantendremos informada de cualquier novedad.",
                        created_at=utc_now(),
                        metadata={
                            "sender": "tugestion@selectra.com",
                            "sender_name": "Selectra Posventa - Gestión de Contratos",
                            "channel_type": "google_group",
                            "recipient": "maria.garcia@example.com",
                            "subject": "[#TCK-1001] Gestión de tarifa en contrato Endesa",
                            "status": "enviado"
                        }
                    ),
                    TicketActivity(
                        id="ACT-003",
                        activity_type=ActivityType.NOTE,
                        author=admin_email,
                        author_name="Carlos Alfageme",
                        content="Escalada consulta a soporte de canal indirecto de Endesa con el ID de grabación. Plazo estimado respuesta: 48h.",
                        created_at=utc_now(),
                        metadata={}
                    ),
                    TicketActivity(
                        id="ACT-004",
                        activity_type=ActivityType.WHATSAPP,
                        author=admin_email,
                        author_name="Carlos Alfageme",
                        content="Hola María, te contactamos desde Selectra Posventa para informarte de que estamos gestionando tu consulta sobre el contrato con Endesa (Ref. TCK-1001). Te mantendremos informada por esta vía.",
                        created_at=utc_now(),
                        metadata={
                            "phone": "+34 600 111 222",
                            "template_name": "actualizacion_estado",
                            "template_label": "Actualización de Estado de Gestión",
                            "status": "entregado",
                            "provider": "WhatsApp Business Cloud API (Simulado)"
                        }
                    )
                ]
            ),
            Ticket(
                id="TCK-1002",
                module=ModuleEnum.RECHAZOS_ATR,
                title="Rechazo A3 - Datos de titular erróneos",
                description="Distribuidora i-DE rechaza la solicitud de cambio de titular por discrepancia en el DNI.",
                customer_name="Juan Rodríguez",
                customer_email="juan.rodriguez@example.com",
                customer_phone="+34 611 222 333",
                cups="ES0021000000000001AZ",
                company="Iberdrola / i-DE",
                priority=Priority.URGENTE,
                status=TicketStatus.ABIERTO,
                created_by=admin_email,
                created_at=utc_now(),
                updated_at=utc_now(),
                activities=[]
            ),
            Ticket(
                id="TCK-1003",
                module=ModuleEnum.RECLAMACIONES,
                title="Reclamación cobro indebido servicio adicional",
                description="Cliente reclama cargo indebido de 9,95€ en primera factura por mantenimiento no contratado.",
                customer_name="Roberto Sánchez",
                customer_email="roberto.sanchez@example.com",
                customer_phone="+34 622 333 444",
                contract_reference="REC-GAS-4491",
                company="Naturgy",
                priority=Priority.ALTA,
                status=TicketStatus.EN_PROCESO,
                created_by=admin_email,
                created_at=utc_now(),
                updated_at=utc_now(),
                activities=[
                    TicketActivity(
                        id="ACT-004",
                        activity_type=ActivityType.EMAIL,
                        author=admin_email,
                        author_name="Carlos Alfageme",
                        content="Estimado Roberto,\n\nHemos registrado formalmente tu reclamación solicitando la anulación del servicio y el abono en tu próxima factura.",
                        created_at=utc_now(),
                        metadata={
                            "sender": "teayudamos@selectra.com",
                            "sender_name": "Selectra Reclamaciones - Te Ayudamos",
                            "channel_type": "google_group",
                            "recipient": "roberto.sanchez@example.com",
                            "subject": "[#TCK-1003] Reclamación por cargo de mantenimiento",
                            "status": "enviado"
                        }
                    )
                ]
            ),
            Ticket(
                id="TCK-1004",
                module=ModuleEnum.ATENCION_RETENCION,
                title="Solicitud de baja por contraoferta de otra compañía",
                description="El cliente solicita anular la contratación tras recibir oferta de retención de su compañía anterior.",
                customer_name="Laura Fernández",
                customer_email="laura.fernandez@example.com",
                customer_phone="+34 633 444 555",
                contract_reference="RET-2026-102",
                company="TotalEnergies",
                priority=Priority.URGENTE,
                status=TicketStatus.ABIERTO,
                created_by=admin_email,
                created_at=utc_now(),
                updated_at=utc_now(),
                activities=[
                    TicketActivity(
                        id="ACT-005",
                        activity_type=ActivityType.CALL,
                        author=admin_email,
                        author_name="Carlos Alfageme",
                        content="Llamada entrante de la clienta solicitando la cancelación. Se le explican los términos de potencia y ahorro anual real.",
                        created_at=utc_now(),
                        metadata={
                            "call_direction": "entrante",
                            "phone": "+34 633 444 555",
                            "outcome": "contactado",
                            "duration": "6 min"
                        }
                    )
                ]
            ),
            Ticket(
                id="TCK-1005",
                module=ModuleEnum.INCIDENCIAS_SUMINISTRO,
                title="Retraso en activación acometida eléctrica",
                description="Alta de suministro en vivienda nueva solicitada hace 8 días laborables sin fecha de técnico asignada.",
                customer_name="David Gómez",
                customer_email="david.gomez@example.com",
                customer_phone="+34 644 555 666",
                cups="ES0031400000000012ZZ",
                company="UFD Distribuidora",
                priority=Priority.MEDIA,
                status=TicketStatus.ABIERTO,
                created_by=admin_email,
                created_at=utc_now(),
                updated_at=utc_now(),
                activities=[]
            ),
            Ticket(
                id="TCK-1006",
                module=ModuleEnum.BORRADO_DATOS,
                title="Solicitud ejercicio derecho supresión (RGPD)",
                description="El cliente solicita eliminación total de sus datos de prospección comercial.",
                customer_name="Carlos Martínez",
                customer_email="cmartinez@example.com",
                customer_phone="+34 655 666 777",
                priority=Priority.MEDIA,
                status=TicketStatus.ABIERTO,
                created_by=admin_email,
                created_at=utc_now(),
                updated_at=utc_now(),
                activities=[]
            )
        ]
        for t in sample_tickets:
            self._memory_tickets[t.id] = t

        # Sembrar configuraciones de email por defecto para cada módulo
        for mod, cfg in MODULE_EMAIL_CONFIG.items():
            self._memory_email_settings[mod.value] = ModuleEmailSetting(
                module=mod,
                email=cfg["email"],
                sender_name=cfg["name"],
                account_type=cfg.get("account_type", "google_group"),
                type_label=cfg.get("type_label", "Bandeja de Grupo de Google Workspace"),
                description=cfg.get("description", ""),
                signature=f"Atentamente,\n{cfg['name']}\nTeléfono: 91 123 45 67 | https://selectra.es",
                rgpd_footer=DEFAULT_RGPD_FOOTER
            )

        # Sembrar plantillas de correo por defecto
        default_tpls = [
            EmailTemplate(
                id="tpl-001",
                name="Solicitud de Documentación (Factura / DNI)",
                module="todos",
                subject="[#{{ticket_id}}] Solicitud de documentación adicional - Selectra",
                body=(
                    "Estimado/a {{customer_name}},\n\n"
                    "Para poder avanzar en la tramitación de tu expediente con {{company}}, necesitamos que nos facilites la siguiente documentación:\n\n"
                    "- Copia de la última factura recibida\n"
                    "- Copia del DNI/NIE del titular\n\n"
                    "Puedes responder directamente a este correo adjuntando los archivos solicitados.\n\n"
                    "Gracias por tu colaboración."
                )
            ),
            EmailTemplate(
                id="tpl-002",
                name="Trámite en Curso con Compañía",
                module="todos",
                subject="[#{{ticket_id}}] Actualización: Tu gestión está en curso - Selectra",
                body=(
                    "Estimado/a {{customer_name}},\n\n"
                    "Te informamos de que hemos trasladado tu gestión a {{company}} con referencia interna de contrato {{contract_reference}}.\n\n"
                    "El plazo de respuesta estimado por la compañía es de 48 a 72 horas hábiles. En cuanto recibamos novedades o confirmación oficial, nos pondremos de nuevo en contacto contigo."
                )
            ),
            EmailTemplate(
                id="tpl-003",
                name="Resolución Favorable del Caso",
                module="todos",
                subject="[#{{ticket_id}}] Resolución favorable de tu gestión - Selectra",
                body=(
                    "Estimado/a {{customer_name}},\n\n"
                    "Nos complace comunicarte que la incidencia referida en el ticket #{{ticket_id}} ha sido resuelta satisfactoriamente con {{company}}.\n\n"
                    "No dudes en responder a este correo si tienes cualquier duda adicional o requieres soporte extra.\n\n"
                    "Gracias por confiar en Selectra."
                )
            ),
            EmailTemplate(
                id="tpl-004",
                name="Subsanación de Rechazo ATR de Distribuidora",
                module=ModuleEnum.RECHAZOS_ATR.value,
                subject="[#{{ticket_id}}] Subsanación de anomalía en solicitud de acometida / ATR con distribuidora",
                body=(
                    "Estimado/a {{customer_name}},\n\n"
                    "La empresa distribuidora nos ha trasladado una discrepancia en el trámite de acceso para el CUPS {{cups}}.\n\n"
                    "Desde Selectra Posventa estamos gestionando activamente la subsanación técnica ante {{company}} para reactivar el suministro en el menor plazo posible."
                )
            ),
            EmailTemplate(
                id="tpl-005",
                name="Confirmación de Supresión de Datos (RGPD)",
                module=ModuleEnum.BORRADO_DATOS.value,
                subject="[#{{ticket_id}}] Confirmación de trámite de derechos de protección de datos (RGPD)",
                body=(
                    "Estimado/a {{customer_name}},\n\n"
                    "Acusamos recibo de su solicitud de supresión y cese de comunicaciones en relación al expediente #{{ticket_id}}.\n\n"
                    "Le confirmamos que nuestro Delegado de Protección de Datos (DPO) ha procesado la baja técnica de sus datos conforme al RGPD y la LOPDGDD."
                )
            )
        ]
        for tpl in default_tpls:
            self._memory_email_templates[tpl.id] = tpl

    def get_user(self, email: str) -> Optional[User]:
        email_clean = email.lower()
        if not self._using_fallback and self._firestore_client:
            try:
                doc = self._firestore_client.collection("users").document(email_clean).get()
                if doc.exists:
                    return User(**doc.to_dict())
            except Exception as e:
                logger.error("Error al consultar usuario en Firestore: %s", e)

        # Fallback local o bootstrap si es el admin configurado
        if email_clean in self._memory_users:
            return self._memory_users[email_clean]
        
        # Si es un nuevo usuario corporativo que entra por primera vez, crearlo como Agente básico
        new_user = User(
            email=email_clean,
            name=email_clean.split("@")[0].replace(".", " ").title(),
            role=Role.ADMIN if email_clean == settings.dev_user_email.lower() else Role.AGENT,
            allowed_modules=list(ModuleEnum) if email_clean == settings.dev_user_email.lower() else [],
            is_active=True
        )
        self.save_user(new_user)
        return new_user

    def save_user(self, user: User) -> User:
        user_dict = user.model_dump()
        email_clean = user.email.lower()
        self._memory_users[email_clean] = user

        if not self._using_fallback and self._firestore_client:
            try:
                self._firestore_client.collection("users").document(email_clean).set(user_dict)
            except Exception as e:
                logger.error("Error al persistir usuario en Firestore: %s", e)
        return user

    def list_users(self) -> List[User]:
        if not self._using_fallback and self._firestore_client:
            try:
                docs = self._firestore_client.collection("users").stream()
                users = [User(**doc.to_dict()) for doc in docs]
                if users:
                    return users
            except Exception as e:
                logger.error("Error al listar usuarios en Firestore: %s", e)
        return list(self._memory_users.values())

    def create_ticket(self, ticket_in: TicketCreate, created_by: str) -> Ticket:
        ticket_id = f"TCK-{uuid.uuid4().hex[:6].upper()}"
        # Para tickets de Backoffice (incidencias_contratos), la resolución por defecto es 'Nuevo'
        default_resolution = "Nuevo" if ticket_in.module == ModuleEnum.INCIDENCIAS_CONTRATOS else None
        ticket = Ticket(
            id=ticket_id,
            module=ticket_in.module,
            title=ticket_in.title,
            description=ticket_in.description,
            customer_name=ticket_in.customer_name,
            customer_surname=ticket_in.customer_surname,
            customer_email=ticket_in.customer_email,
            customer_phone=ticket_in.customer_phone,
            contract_reference=ticket_in.contract_reference,
            cups=ticket_in.cups,
            company=ticket_in.company,
            department=ticket_in.department,
            priority=ticket_in.priority,
            resolution=ticket_in.resolution or default_resolution,
            classification=ticket_in.classification,
            recovery_channel=ticket_in.recovery_channel,
            metadata=ticket_in.metadata,
            status=TicketStatus.ABIERTO,
            created_by=created_by,
            created_at=utc_now(),
            updated_at=utc_now(),
            notes=[]
        )
        self._memory_tickets[ticket_id] = ticket

        if not self._using_fallback and self._firestore_client:
            try:
                ticket_data = ticket.model_dump()
                # Serializar datetimes a strings ISO para Firestore
                ticket_data["created_at"] = ticket.created_at.isoformat()
                ticket_data["updated_at"] = ticket.updated_at.isoformat()
                self._firestore_client.collection("tickets").document(ticket_id).set(ticket_data)
            except Exception as e:
                logger.error("Error al persistir ticket en Firestore: %s", e)
        return ticket

    def get_ticket(self, ticket_id: str) -> Optional[Ticket]:
        if not self._using_fallback and self._firestore_client:
            try:
                doc = self._firestore_client.collection("tickets").document(ticket_id).get()
                if doc.exists:
                    return Ticket(**doc.to_dict())
            except Exception as e:
                logger.error("Error al consultar ticket en Firestore: %s", e)
        return self._memory_tickets.get(ticket_id)

    def list_tickets(
        self,
        module: Optional[ModuleEnum] = None,
        status: Optional[TicketStatus] = None
    ) -> List[Ticket]:
        tickets = []
        if not self._using_fallback and self._firestore_client:
            try:
                query = self._firestore_client.collection("tickets")
                if module:
                    query = query.where("module", "==", module.value)
                if status:
                    query = query.where("status", "==", status.value)
                docs = query.stream()
                tickets = [Ticket(**doc.to_dict()) for doc in docs]
                return sorted(tickets, key=lambda x: x.created_at, reverse=True)
            except Exception as e:
                logger.error("Error al listar tickets en Firestore: %s", e)

        # Fallback local en memoria
        tickets = list(self._memory_tickets.values())
        if module:
            tickets = [t for t in tickets if t.module == module]
        if status:
            tickets = [t for t in tickets if t.status == status]
        return sorted(tickets, key=lambda x: x.created_at, reverse=True)

    def update_ticket(self, ticket_id: str, update: TicketUpdate, updated_by: str) -> Optional[Ticket]:
        ticket = self.get_ticket(ticket_id)
        if not ticket:
            return None

        update_dict = update.model_dump(exclude_unset=True)
        for key, val in update_dict.items():
            if val is not None and hasattr(ticket, key):
                setattr(ticket, key, val)

        ticket.updated_at = utc_now()
        self._memory_tickets[ticket_id] = ticket

        if not self._using_fallback and self._firestore_client:
            try:
                ticket_data = ticket.model_dump()
                ticket_data["created_at"] = ticket.created_at.isoformat()
                ticket_data["updated_at"] = ticket.updated_at.isoformat()
                self._firestore_client.collection("tickets").document(ticket_id).set(ticket_data)
            except Exception as e:
                logger.error("Error actualizando ticket en Firestore: %s", e)
        return ticket

    def add_activity(
        self,
        ticket_id: str,
        activity_type: ActivityType,
        author: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        author_name: Optional[str] = None
    ) -> Optional[Ticket]:
        ticket = self.get_ticket(ticket_id)
        if not ticket:
            return None

        activity = TicketActivity(
            activity_type=activity_type,
            author=author,
            author_name=author_name or author.split("@")[0].replace(".", " ").title(),
            content=content,
            created_at=utc_now(),
            metadata=metadata or {}
        )
        ticket.activities.insert(0, activity)  # Más recientes al principio
        ticket.updated_at = utc_now()

        if activity_type == ActivityType.NOTE:
            ticket.notes.insert(0, TicketNote(author=author, content=content, created_at=activity.created_at))

        self._memory_tickets[ticket_id] = ticket

        if not self._using_fallback and self._firestore_client:
            try:
                ticket_data = ticket.model_dump()
                ticket_data["created_at"] = ticket.created_at.isoformat()
                ticket_data["updated_at"] = ticket.updated_at.isoformat()
                self._firestore_client.collection("tickets").document(ticket_id).set(ticket_data)
            except Exception as e:
                logger.error("Error persistiendo actividad en Firestore: %s", e)
        return ticket

    def add_note(self, ticket_id: str, author: str, content: str) -> Optional[Ticket]:
        return self.add_activity(
            ticket_id=ticket_id,
            activity_type=ActivityType.NOTE,
            author=author,
            content=content
        )

    # =========================================================================
    # GESTIÓN DE CONFIGURACIÓN DE CORREOS Y PLANTILLAS
    # =========================================================================

    def get_email_settings(self) -> Dict[str, ModuleEmailSetting]:
        if not self._using_fallback and self._firestore_client:
            try:
                docs = self._firestore_client.collection("email_settings").stream()
                loaded = {}
                for doc in docs:
                    data = doc.to_dict()
                    setting = ModuleEmailSetting(**data)
                    loaded[setting.module.value] = setting
                if loaded:
                    self._memory_email_settings.update(loaded)
                    return self._memory_email_settings
            except Exception as e:
                logger.error("Error al obtener email_settings en Firestore: %s", e)
        return self._memory_email_settings

    def get_module_email_setting(self, module: ModuleEnum) -> ModuleEmailSetting:
        all_settings = self.get_email_settings()
        if module.value in all_settings:
            return all_settings[module.value]

        base_cfg = MODULE_EMAIL_CONFIG.get(module, MODULE_EMAIL_CONFIG[ModuleEnum.INCIDENCIAS_CONTRATOS])
        setting = ModuleEmailSetting(
            module=module,
            email=base_cfg["email"],
            sender_name=base_cfg["name"],
            account_type=base_cfg.get("account_type", "google_group"),
            type_label=base_cfg.get("type_label", "Bandeja de Grupo de Google Workspace"),
            description=base_cfg.get("description", ""),
            signature=f"Atentamente,\n{base_cfg['name']}\nTeléfono: 91 123 45 67 | https://selectra.es",
            rgpd_footer=DEFAULT_RGPD_FOOTER
        )
        self._memory_email_settings[module.value] = setting
        return setting

    def save_module_email_setting(self, setting: ModuleEmailSetting) -> ModuleEmailSetting:
        self._memory_email_settings[setting.module.value] = setting
        if not self._using_fallback and self._firestore_client:
            try:
                data = setting.model_dump()
                data["module"] = setting.module.value
                self._firestore_client.collection("email_settings").document(setting.module.value).set(data)
            except Exception as e:
                logger.error("Error guardando email_setting en Firestore: %s", e)
        return setting

    def list_email_templates(self, module: Optional[str] = None) -> List[EmailTemplate]:
        templates = list(self._memory_email_templates.values())
        if not self._using_fallback and self._firestore_client:
            try:
                docs = self._firestore_client.collection("email_templates").stream()
                loaded = []
                for doc in docs:
                    d = doc.to_dict()
                    if "created_at" in d and isinstance(d["created_at"], str):
                        d["created_at"] = datetime.fromisoformat(d["created_at"])
                    if "updated_at" in d and isinstance(d["updated_at"], str):
                        d["updated_at"] = datetime.fromisoformat(d["updated_at"])
                    loaded.append(EmailTemplate(**d))
                if loaded:
                    templates = loaded
                    self._memory_email_templates = {t.id: t for t in templates}
            except Exception as e:
                logger.error("Error al listar plantillas en Firestore: %s", e)

        if module and module != "todos":
            templates = [t for t in templates if t.module in ("todos", module)]
        return sorted(templates, key=lambda x: x.created_at, reverse=False)

    def get_email_template(self, template_id: str) -> Optional[EmailTemplate]:
        templates = self.list_email_templates()
        for t in templates:
            if t.id == template_id:
                return t
        return None

    def save_email_template(self, template: EmailTemplate) -> EmailTemplate:
        template.updated_at = utc_now()
        self._memory_email_templates[template.id] = template
        if not self._using_fallback and self._firestore_client:
            try:
                data = template.model_dump()
                data["created_at"] = template.created_at.isoformat()
                data["updated_at"] = template.updated_at.isoformat()
                self._firestore_client.collection("email_templates").document(template.id).set(data)
            except Exception as e:
                logger.error("Error guardando plantilla en Firestore: %s", e)
        return template

    def delete_email_template(self, template_id: str) -> bool:
        if template_id in self._memory_email_templates:
            del self._memory_email_templates[template_id]
        if not self._using_fallback and self._firestore_client:
            try:
                self._firestore_client.collection("email_templates").document(template_id).delete()
            except Exception as e:
                logger.error("Error eliminando plantilla en Firestore: %s", e)
        return True

repo = DataRepository()
