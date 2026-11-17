# COMFEY - APP POSVENTA - Selectra Safari Zone

Herramienta interna modular para la gestión integral de operaciones posventa en **Selectra**, diseñada bajo los estándares de gobernanza y arquitectura de **Safari Zone** (Google Cloud Run + Buildpacks + Zero-Key ADC).

---

## 🎯 Alcance y Módulos de Operaciones

La aplicación está diseñada bajo una arquitectura modular donde cada tipología de gestión opera de manera independiente con su propio sistema de tickets y control de acceso:

1. **Incidencias de Contratos Finalizados** (`incidencias_contratos`): Resolución de problemas tras la firma o formalización de contratos.
2. **Atención al Cliente, Retención y Fidelización** (`atencion_retencion`): Tramitación de peticiones críticas de retención de cartera y fidelización.
3. **Gestión de Reclamaciones** (`reclamaciones`): Tramitación de reclamaciones formales de clientes hacia compañías o distribuidoras.
4. **Peticiones de Borrado de Datos** (`borrado_datos`): Ejercicio de derechos ARCO / RGPD de supresión de datos.
5. **Incidencias en Altas de Suministro** (`incidencias_suministro`): Seguimiento técnico de altas de Luz y Gas.
6. **Rechazos ATR de Compañías** (`rechazos_atr`): Gestión de errores de distribuidoras en solicitudes de acceso a la red (ATR).
7. **Panel de Administración y RBAC** (`admin`): Asignación granular de módulos a usuarios y control de roles.

---

## 🔐 Autenticación y Control de Roles (RBAC)

- **Acceso Corporativo Google Workspace**: En entorno de producción (Cloud Run), el acceso está securizado mediante **Google Cloud Identity-Aware Proxy (IAP)**, permitiendo únicamente el inicio de sesión con cuentas `@selectra.com` y `@selectra.info`.
- **Cero contraseñas en código**: La identidad del usuario se obtiene de la cabecera autenticada `X-Goog-Authenticated-User-Email`.
- **Roles y Permisos**:
  - `Administrador`: Acceso irrestricto a todos los módulos actuales y futuros, además de gestionar los permisos de los demás usuarios en `/admin/roles`.
  - `Agente`: Solo puede visualizar y gestionar tickets en los módulos que el Administrador le haya habilitado explícitamente.
- **Modo Desarrollo Local (`DEV_MODE=true`)**: Permite simular el entorno sin conexión IAP y probar la experiencia de diferentes roles desde el desplegable del encabezado o mediante el parámetro `?as_user=correo@selectra.com`.

---

## 🏗️ Arquitectura Safari Zone (Cero Infraestructura)

- **Cloud Native Buildpacks**: No requiere `Dockerfile`, `docker-compose` ni configuraciones de Kubernetes/Terraform. DevOps gestiona el despliegue automático desde GitHub.
- **Punto de Entrada (`Procfile`)**:
  ```text
  web: uvicorn src.app_posventa.main:app --host 0.0.0.0 --port $PORT
  ```
- **Persistencia Stateless Zero-Key**:
  - **Base de Datos NoSQL**: Cloud Firestore (`app-posventa`) en modo nativo en `europe-west1`.
  - **Almacenamiento de Archivos**: Google Cloud Storage (`gs://safari-zone-app-posventa-data`).
  - **Sin API Keys**: Ambos servicios se autentican automáticamente mediante Application Default Credentials (ADC) vinculadas a la Service Account de la aplicación.

---

## 💻 Puesta en Marcha Local

### 1. Clonar o acceder al directorio
```bash
cd C:\Users\carlos.alfageme_sele\.gemini\antigravity\scratch\app-posventa
```

### 2. Crear entorno virtual e instalar dependencias
```bash
python -m venv .venv
# En Windows (PowerShell):
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

### 3. Copiar archivo de entorno
```bash
copy .env.example .env
```

### 4. Ejecutar el servidor en desarrollo
```bash
uvicorn src.app_posventa.main:app --reload --port 8080
```
Abre tu navegador en: [http://localhost:8080](http://localhost:8080)

### 5. Ejecutar Pruebas Unitarias
```bash
pytest tests/ -v
```

---

## 🚀 Despliegue en Safari Zone (Google Cloud Run)

### Inicialización y Push en GitHub Selectra-Dev
```bash
git init
git remote add origin https://github.com/Selectra-Dev/app-posventa.git
git branch -M main
git add .
git commit -m "feat(scaffold): estructura inicial para Selectra Safari Zone"
git push -u origin main
```

### Solicitud de Persistencia (DevOps)
Publicar en el canal de Google Chat `Safari Zone`:
- GCS Bucket: `gs://safari-zone-app-posventa-data`
- Firestore Named DB: `app-posventa`
- Service Account: `app-posventa-sa@safari-zone-selectra.iam.gserviceaccount.com`
