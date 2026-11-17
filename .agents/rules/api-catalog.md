---
description: Estándares de consumo y publicación en el Catálogo de APIs y Microservicios internos en GCS.
trigger: always_on
---

# Regla del Catálogo de APIs y Microservicios Propios en Selectra Safari Zone

1. **Catálogo Dinámico Centralizado en GCS**:
   - Todas las especificaciones OpenAPI de las aplicaciones y microservicios internos residen en el bucket:
     `gs://safari-zone-api-catalog/<nombre-servicio>/`
   - Cada servicio cuenta con `openapi.json` y opcionalmente `metadata.json`.
   - Las tuberías CI/CD de las aplicaciones propietarias se encargan de publicar y mantener actualizados esos ficheros.

2. **Descubrimiento en Tiempo de Desarrollo**:
   - Antes de implementar un cliente o conector para una herramienta propia, consulta las capacidades existentes con las herramientas del agente:
     * `list_internal_apis`: Lista todos los servicios, tags y endpoints disponibles.
     * `get_api_service_details`: Obtiene la definición de endpoints, esquemas de payload y código cliente listo para usar.

3. **Principio Universal Zero-Key para Cloud Run (IAM OIDC)**:
   - Los microservicios en Cloud Run se autentican internamente mediante Identity Tokens OIDC emitidos por la Service Account (`google.oauth2.id_token.fetch_id_token`).
   - NUNCA generes ni solicites API Keys estáticas para comunicar microservicios entre sí en Cloud Run.

4. **Prohibición de URLs Quemadas (Hardcoded URLs)**:
   - NUNCA quemes URLs directas (`https://<service>.run.app`) dentro del código fuente.
   - Declara la URL base en `.env.example` y léela con `os.getenv()`.

5. **Auditoría Pre-Despliegue (CI/CD)**:
   - Utiliza la herramienta `audit_api_connections` para verificar que los endpoints y métodos coincidan con el catálogo.
