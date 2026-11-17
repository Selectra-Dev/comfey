---
description: Estándares de persistencia de datos (Cloud Storage y Firestore) y principio stateless para Cloud Run.
trigger: always_on
---

# Regla de Persistencia de Datos y Principio Stateless en Selectra Safari Zone

1. **Cloud Run es Stateless**:
   - Todo disco local (`/tmp`) es efímero y se destruye al reiniciar o escalar instancias.
   - Prohibido utilizar SQLite en disco local o guardar archivos asumiendo persistencia local entre peticiones.

2. **Persistencia Oficial y Homologada en Google Cloud**:
   - **Archivos y Blobs**: Google Cloud Storage (`google-cloud-storage`).
     * Bucket dedicado por aplicación: `safari-zone-app-posventa-data` en `europe-west1`.
   - **Datos Estructurados / NoSQL**: Cloud Firestore (`google-cloud-firestore`).
     * Base de datos dedicada (*Named Database*): `app-posventa` en modo nativo en `europe-west1`.
   - **Cloud SQL Descartado**: Prohibido crear instancias de Cloud SQL (MySQL/PostgreSQL) por costes fijos innecesarios, complejidad y necesidad de conectores VPC.

3. **Principio Universal Zero-Key (IAM & ADC)**:
   - NUNCA introduzcas credenciales, claves de API o passwords de base de datos en el código fuente.
   - La autenticación la realiza automáticamente la Service Account asignada al servicio en Cloud Run mediante Application Default Credentials (ADC).
   - En desarrollo local se utiliza `gcloud auth application-default login`.

4. **Variables de Configuración en .env.example**:
   - Declara las variables de persistencia necesarias (no son secretos):
     `GCS_BUCKET_NAME=safari-zone-app-posventa-data`
     `FIRESTORE_DATABASE_ID=app-posventa`

5. **Etiquetado Obligatorio de Recursos (GCP Labels)**:
   - Todo recurso en GCP perteneciente a una aplicación de Power User (Cloud Run, Buckets GCS, BDs Firestore, Cloud Build Triggers) debe llevar etiquetas estandarizadas para filtrado y facturación:
     * `app`: app-posventa
     * `owner`: carlos_alfageme_selectra_com
     * `user`: carlos-alfageme
     * `managed-by`: safari-zone
