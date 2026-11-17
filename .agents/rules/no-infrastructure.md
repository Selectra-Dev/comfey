# Regla de Abstracción de Infraestructura Selectra

1. No generes ni modifiques:
   - `Dockerfile` o `Dockerfile.*`
   - `docker-compose.yml`
   - `cloudbuild.yaml`
   - Manifiestos de Kubernetes o Terraform
2. El despliegue de las aplicaciones en `safari-zone-selectra` se realiza de forma 100% transparente
   por la tubería CI/CD de DevOps de Selectra mediante Cloud Native Buildpacks.
3. Si el usuario pide un Dockerfile, explícale que en Selectra la infraestructura está automatizada
   por DevOps y que solo requiere su código Python y `requirements.txt`.
