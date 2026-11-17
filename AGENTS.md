# Directrices de Desarrollo de Selectra para Asistentes de IA (Claude, Cursor, Antigravity)

Este repositorio es una herramienta interna creada por Power Users de Selectra.
Cualquier asistente de IA (Claude, Cursor, Windsurf, Antigravity) DEBE acatar estrictamente las siguientes directivas:

## 1. Regla de Oro de Infraestructura (CRÍTICA)
- **NUNCA crees ni sugieras crear `Dockerfile`, `docker-compose.yml`, `cloudbuild.yaml`, ni scripts de despliegue.**
- Los Power Users NO deben preocuparse de la infraestructura ni de los contenedores.
- La empresa cuenta con una tubería CI/CD centralizada gestionada por DevOps que compila automáticamente el código con **Cloud Native Buildpacks** y lo despliega en Cloud Run en el proyecto `safari-zone-selectra`.
- Céntrate **100% en la lógica de negocio, pruebas unitarias y experiencia de usuario**.

## 2. Alojamiento Exclusivo en GitHub (Selectra-Dev) y Prohibición de ZIPs (CRÍTICA)
- **NUNCA ofrezcas descargar un archivo ZIP ni entregues proyectos como archivos comprimidos locales.**
- **ESTÁ PROHIBIDO crear proyectos en repositorios de cuentas personales de GitHub.**
- Todo proyecto de Power User DEBE residir dentro de la organización oficial de GitHub: `https://github.com/Selectra-Dev/<nombre-repositorio>`.
- Si el Power User no tiene cuenta en GitHub o no pertenece a `Selectra-Dev`, guíale de inmediato para crearla con su correo corporativo (`@selectra.com` o `@selectra.info`), activar 2FA y solicitar invitación en `Safari Zone`.

## 3. Servidor MCP de Gobernanza
- Este espacio de trabajo está respaldado por el servidor central de gobernanza (`safari-zone-governance`).
- **Autenticación Zero-Config**: El servidor MCP en Cloud Run implementa FastMCP Google OAuth Proxy (RFC 8414 / RFC 9728). No requiere configurar Client ID ni Client Secret en el IDE; basta con introducir la URL del servidor y autorizar en el navegador con la cuenta corporativa (`@selectra.com` o `@selectra.info`).
- Utiliza las herramientas MCP para scaffolding, asistencia de GitHub, auditoría de seguridad, catálogo de APIs y validación de commits.

## 4. Persistencia de Datos y Principio Stateless para Cloud Run
- **Cloud Run es Stateless**: El disco local es efímero y en memoria (`/tmp`). Se destruye al reiniciar o escalar instancias.
- **Persistencia de Archivos y Blobs (GCS)**: Para almacenar CSVs, PDFs, exportaciones, imágenes o documentos, utiliza **Google Cloud Storage** (`google-cloud-storage`) con el bucket dedicado de la aplicación (`safari-zone-app-posventa-data`).
- **Persistencia de Datos Estructurados / NoSQL (Firestore)**: Para bases de datos, colecciones, catálogos o entidades de negocio, utiliza **Cloud Firestore** (`google-cloud-firestore`) con la base de datos dedicada (*Named Database*) de la aplicación (`app-posventa`).
- **Cloud SQL Descartado**: Descartado por complejidad y costes fijos. No crees ni pidas bases de datos relacionales en Cloud SQL.
- **Principio Universal Zero-Key**: GCS y Firestore se autentican automáticamente mediante la identidad de la Service Account (Application Default Credentials - ADC) sin necesidad de API keys ni contraseñas.
- **Aprovisionamiento Bajo Demanda**: Utiliza la herramienta MCP `generate_persistence_request` para generar la solicitud y los comandos exactos que DevOps ejecutará en el canal `Safari Zone`.

## 5. Seguridad, Secretos y Credenciales
- **PROHIBIDO quemar credenciales, API keys o tokens en el código fuente.**
- Utiliza variables de entorno (`os.getenv(...)`) o la identidad gestionada por GCP (Application Default Credentials).
- **Catálogo Dinámico de Secretos y Declaración en .env.example**:
  * En desarrollo local, utiliza un archivo `.env` basado en `.env.example` con tus credenciales de prueba (ignorado por Git).
  * **Regla de Declaración**: Si tu aplicación requiere un secreto o API key, decláralo descomentado en `.env.example`.
  * Al desplegar en Cloud Run (`safari-zone-selectra`), el pipeline de CI/CD descubre dinámicamente los secretos activos en Secret Manager y monta exclusivamente los requeridos mediante `--set-secrets`.
- **Principio Universal Zero-Key para Servicios de Google Cloud (GCP)**:
  * Cualquier servicio de GCP (Vertex AI / Gemini, BigQuery, Cloud Storage, Firestore, etc.) **NO utiliza API Keys**.
  * Cloud Run se autentica automáticamente mediante la identidad de la Service Account asignada (Application Default Credentials - ADC).
- No configures CORS permisivo (`allow_origins=["*"]`).
- La autenticación corporativa está resuelta por Google Cloud Identity-Aware Proxy (IAP) para `@selectra.com` y `@selectra.info`. La app lee la identidad del usuario mediante la cabecera `X-Goog-Authenticated-User-Email`.

## 6. Convención de Git y Commits
- Todo commit debe seguir **Conventional Commits**: `<tipo>(<alcance opcional>): <descripción concisa>`.
- Tipos válidos: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`.
- Nunca uses mensajes como "wip", "update", o "cambios".
