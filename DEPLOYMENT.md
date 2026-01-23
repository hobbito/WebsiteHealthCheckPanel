# Deployment Guide - DigitalOcean Apps con Base de Datos Externa

## Resumen

Esta guía cubre el deployment en DigitalOcean Apps usando una **base de datos PostgreSQL externa** (no managed database de DigitalOcean).

**Costos estimados:**
- DigitalOcean App (basic-xs): **$5/mo**
- Base de datos externa: **Tu elección**

## Requisitos Previos

1. Cuenta de DigitalOcean
2. Repositorio GitHub con el código
3. Base de datos PostgreSQL externa configurada (DigitalOcean Managed DB, AWS RDS, Railway, Supabase, etc.)

## Paso 1: Configurar Base de Datos Externa

### Opción A: DigitalOcean Managed Database

1. Ve a DigitalOcean → Databases → Create Database
2. Selecciona PostgreSQL 16
3. Elige el plan (basic $15/mo o superior)
4. Crea la base de datos

**Obtener connection string:**
```bash
# En el dashboard de DigitalOcean Database, copia la connection string
# Formato: postgresql://user:password@host:port/database?sslmode=require

# Conviértela al formato asyncpg:
postgresql+asyncpg://user:password@host:port/database?ssl=require
```

### Opción B: Otras Opciones

**Railway:**
- Crea proyecto en Railway.app
- Añade PostgreSQL
- Copia la connection string
- Modifica para asyncpg: `postgresql+asyncpg://...`

**Supabase:**
- Proyecto en supabase.com
- Settings → Database → Connection string
- Usa "Session pooler" para mejor performance
- Formato: `postgresql+asyncpg://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres`

**AWS RDS:**
- Crea instancia PostgreSQL en RDS
- Configura security group para permitir conexiones
- Connection string: `postgresql+asyncpg://username:password@endpoint:5432/dbname`

## Paso 2: Preparar el Código

### 2.1 Crear Repositorio GitHub

```bash
cd WebsiteHealthCheckPanel

# Inicializar git
git init
git add .
git commit -m "Initial commit: Health Check Panel"

# Crear repo en GitHub y conectar
git remote add origin https://github.com/tu-usuario/health-check-panel.git
git branch -M main
git push -u origin main
```

### 2.2 Verificar Archivos Críticos

Asegúrate de que existen:
- ✅ `Dockerfile`
- ✅ `.do/app.yaml`
- ✅ `backend/alembic.ini`
- ✅ `backend/requirements.txt`

## Paso 3: Crear App en DigitalOcean

### 3.1 Crear la App

1. Ve a DigitalOcean Dashboard
2. Apps → **Create App**
3. Selecciona **GitHub** como fuente
4. Autoriza DigitalOcean a acceder a tus repos
5. Selecciona tu repositorio: `tu-usuario/health-check-panel`
6. Branch: `main`

### 3.2 Configuración Automática

DigitalOcean detectará automáticamente:
- ✅ `Dockerfile` - Lo usará para el build
- ✅ Puerto 8000 (definido en Dockerfile)
- ✅ Health check endpoint: `/health`

### 3.3 Configurar Variables de Entorno

En la sección **Environment Variables**, añade:

#### Requeridas:

**DATABASE_URL** (Secret)
```
postgresql+asyncpg://user:password@host:port/database?ssl=require
```
⚠️ **Importante**: Usa el formato `asyncpg`, no `psycopg2`

**SECRET_KEY** (Secret)
```bash
# Genera uno seguro con Python:
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**ENVIRONMENT**
```
production
```

#### Opcionales (para notificaciones por email):

**SMTP_HOST**
```
smtp.gmail.com
```

**SMTP_PORT**
```
587
```

**SMTP_USER** (Secret)
```
tu-email@gmail.com
```

**SMTP_PASSWORD** (Secret)
```
tu-app-password
```

**SMTP_FROM**
```
noreply@tu-dominio.com
```

#### CORS (actualizar después del primer deploy):

**CORS_ORIGINS**
```json
["https://tu-app-nombre.ondigitalocean.app"]
```

### 3.4 Configurar Recursos

**Instance Type:**
- Para empezar: **Basic (512MB RAM, 1 vCPU)** - $5/mo
- Para 100+ sitios: **Basic ($12)** o **Professional ($24)**

**Instance Count:**
- Inicial: **1**
- Escalado: Aumenta según necesites

### 3.5 Región

Elige la región más cercana a:
- Tus usuarios
- Tu base de datos (para minimizar latencia)

Opciones: `nyc1`, `nyc3`, `sfo3`, `fra1`, `lon1`, `sgp1`, `tor1`

## Paso 4: Deploy

1. Click **Next** hasta llegar a Review
2. Verifica la configuración
3. Click **Create Resources**

DigitalOcean hará:
1. ✅ Clonar repo de GitHub
2. ✅ Build Docker image
3. ✅ Ejecutar migraciones (`alembic upgrade head`)
4. ✅ Iniciar aplicación
5. ✅ Asignar URL HTTPS automática

**Tiempo estimado:** 5-10 minutos

## Paso 5: Verificar Deployment

### 5.1 Obtener URL

Una vez completado, verás tu URL:
```
https://health-check-panel-xxxxx.ondigitalocean.app
```

### 5.2 Test de Health Check

```bash
curl https://tu-app.ondigitalocean.app/health
```

Respuesta esperada:
```json
{
  "status": "healthy",
  "app": "Health Check Panel",
  "environment": "production"
}
```

### 5.3 Verificar API Docs

Abre en navegador:
```
https://tu-app.ondigitalocean.app/api/docs
```

## Paso 6: Configuración Post-Deploy

### 6.1 Actualizar CORS

1. Ve a Settings → Environment Variables
2. Actualiza `CORS_ORIGINS`:
```json
["https://tu-app-real.ondigitalocean.app"]
```
3. App se redesplegará automáticamente

### 6.2 Configurar Dominio Personalizado (Opcional)

1. En DigitalOcean App → Settings → Domains
2. Add Domain
3. Ingresa tu dominio: `healthcheck.tudominio.com`
4. Configura DNS (CNAME):
   ```
   healthcheck.tudominio.com → tu-app.ondigitalocean.app
   ```
5. DigitalOcean manejará SSL automáticamente

### 6.3 Crear Primer Usuario

```bash
curl -X POST https://tu-app.ondigitalocean.app/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@tudominio.com",
    "password": "password-seguro-aqui",
    "full_name": "Admin User",
    "organization_name": "Tu Empresa"
  }'
```

## Paso 7: Monitoreo y Logs

### 7.1 Ver Logs en Tiempo Real

En DigitalOcean App Dashboard:
- Runtime Logs → Ver output de aplicación
- Build Logs → Ver proceso de deploy
- Deploy Logs → Ver migraciones

### 7.2 Verificar APScheduler

En los logs deberías ver:
```
✅ APScheduler started
✅ Synced X check schedules
```

### 7.3 Métricas

DigitalOcean muestra:
- CPU usage
- Memory usage
- Request count
- Response times

**Alertas recomendadas:**
- CPU > 80% por 5 minutos
- Memory > 90% por 5 minutos

## Paso 8: Continuous Deployment

### 8.1 Auto-deploy en Push

Ya está configurado en `.do/app.yaml`:
```yaml
github:
  deploy_on_push: true
```

Cada `git push` a `main` despliega automáticamente.

### 8.2 Workflow Recomendado

```bash
# Desarrollo local
git checkout -b feature/nueva-funcionalidad
# ... hacer cambios ...
git commit -m "Add: nueva funcionalidad"
git push origin feature/nueva-funcionalidad

# Crear Pull Request en GitHub
# Merge a main → Auto-deploy!
```

### 8.3 Rollback

Si algo sale mal:
1. En DigitalOcean App → Deployments
2. Encuentra el deployment anterior funcionando
3. Click **Rollback**

## Troubleshooting

### Error: "Database connection failed"

**Causa:** DATABASE_URL incorrecta o base de datos inaccesible

**Solución:**
1. Verifica format: `postgresql+asyncpg://...`
2. Verifica que la BD permite conexiones externas
3. Chequea firewall/security groups
4. Test de conexión:
   ```bash
   # Desde tu máquina local
   psql "postgresql://user:pass@host:port/db"
   ```

### Error: "Module not found"

**Causa:** Dependencia faltante en `requirements.txt`

**Solución:**
1. Verifica `backend/requirements.txt`
2. Push cambios
3. Redeploy automático

### APScheduler no ejecuta checks

**Causa:** Jobs no persistidos o scheduler no inició

**Solución:**
1. Verifica logs: "APScheduler started"
2. Chequea tabla en DB:
   ```sql
   SELECT * FROM apscheduler_jobs;
   ```
3. Si vacía, crea un check vía API

### SSE no conecta

**Causa:** CORS mal configurado

**Solución:**
1. Actualiza `CORS_ORIGINS` con URL correcta
2. Incluye protocolo: `https://...`
3. Sin trailing slash

## Escalado

### Vertical Scaling (Recomendado inicialmente)

Cuando CPU/Memory > 70%:
1. Settings → Resources
2. Cambiar instance size:
   - Basic → Basic ($12) - 1GB RAM
   - Basic → Professional ($24) - 2GB RAM

### Horizontal Scaling (Avanzado)

Para escalar a múltiples instancias:

1. **Migrar EventBus a PostgreSQL LISTEN/NOTIFY:**
```python
# Reemplazar in-memory event bus
# Ver plan para implementación
```

2. **Aumentar Instance Count:**
- Settings → Resources
- Instance Count: 2 o más

3. **Configurar Session Affinity** (si es necesario)

## Costos Mensuales Estimados

### Configuración Básica
- App (basic-xs): **$5/mo**
- Base de datos externa:
  - DigitalOcean Managed DB (basic): $15/mo
  - Railway: $5-10/mo
  - Supabase: Free-$25/mo
- **Total: $5-20/mo**

### Escalado (100-500 sitios)
- App (basic): **$12/mo**
- Base de datos (1GB): $15-25/mo
- **Total: $27-37/mo**

### Producción (500+ sitios)
- App (professional-xs): **$24/mo**
- Base de datos (2GB+): $25-50/mo
- **Total: $49-74/mo**

## Backups

### Base de Datos

**DigitalOcean Managed DB:**
- Backups diarios automáticos incluidos
- Retención: 7 días (configurable)

**Otras opciones:**
- Configura backups según tu proveedor
- Considera exportar a S3/Spaces semanalmente

### Código

- Ya está en GitHub ✅
- Tags para releases:
  ```bash
  git tag -a v1.0.0 -m "Release 1.0.0"
  git push origin v1.0.0
  ```

## Seguridad

### Checklist Post-Deploy

- [ ] `SECRET_KEY` es aleatorio y único
- [ ] Database credentials en variables de entorno (no en código)
- [ ] CORS configurado correctamente
- [ ] HTTPS habilitado (automático en DO Apps)
- [ ] Firewall de base de datos permite solo DO App IPs
- [ ] Backups configurados
- [ ] Monitoreo y alertas activos

### Recomendaciones

1. **Cambiar passwords periódicamente**
2. **Habilitar 2FA en DigitalOcean**
3. **Limitar acceso a DB** solo desde DO App
4. **Implementar rate limiting** (TODO en código)
5. **Logs de auditoría** para acciones críticas

## Próximos Pasos

1. ✅ Deploy completado
2. 🔄 Crear usuarios y sitios
3. 🔄 Configurar checks
4. 🔄 Configurar notificaciones
5. 📊 Monitorear performance
6. 🚀 Desarrollar frontend (Next.js)

## Soporte

- **DigitalOcean Status:** https://status.digitalocean.com
- **Community:** https://www.digitalocean.com/community
- **Docs:** https://docs.digitalocean.com/products/app-platform/
