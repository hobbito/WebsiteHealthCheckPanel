# DigitalOcean Droplet Setup Guide

Guía completa para deployar Health Check Panel en un Droplet de DigitalOcean con auto-deploy desde GitHub.

## 📋 Requisitos

- Cuenta de DigitalOcean
- Cuenta de GitHub
- Dominio (opcional)

## 💰 Costos Estimados

- **Droplet Basic (2GB RAM, 1 vCPU)**: $12/mo
- **Dominio**: $10-15/año (opcional)
- **Total**: ~$12-13/mo

## 🚀 Paso 1: Crear Droplet

### 1.1 En DigitalOcean Dashboard

1. Click **Create** → **Droplets**
2. Configuración:
   - **Image**: Ubuntu 22.04 LTS
   - **Plan**: Basic Regular ($12/mo - 2GB RAM, 1 vCPU)
   - **Datacenter**: Elige el más cercano a tus usuarios
   - **Authentication**: SSH Key (recomendado) o Password
   - **Hostname**: `healthcheck-prod`

3. Click **Create Droplet**

### 1.2 Guardar IP

Una vez creado, guarda la IP pública:
```
Droplet IP: XXX.XXX.XXX.XXX
```

## 🔧 Paso 2: Configurar Droplet

### 2.1 Conectar por SSH

```bash
ssh root@YOUR_DROPLET_IP
```

### 2.2 Actualizar Sistema

```bash
apt update && apt upgrade -y
```

### 2.3 Instalar Docker

```bash
# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Verificar instalación
docker --version
```

### 2.4 Instalar Docker Compose

```bash
# Instalar Docker Compose
apt install docker-compose-plugin -y

# Verificar instalación
docker compose version
```

### 2.5 Instalar Git

```bash
apt install git -y
```

### 2.6 Crear Directorio del Proyecto

```bash
mkdir -p /opt/healthcheck
cd /opt/healthcheck
```

## 📦 Paso 3: Clonar Repositorio

### 3.1 Clonar el Código

```bash
cd /opt/healthcheck
git clone https://github.com/YOUR-USERNAME/health-check-panel.git .
git checkout main
```

### 3.2 Configurar Variables de Entorno

```bash
# Copiar ejemplo
cp .env.example .env

# Editar con tus valores
nano .env
```

**Valores a configurar:**

```bash
# PostgreSQL
POSTGRES_PASSWORD=tu-password-seguro-aqui

# Application
SECRET_KEY=$(openssl rand -hex 32)

# CORS (actualizar con tu dominio/IP)
CORS_ORIGINS=["http://YOUR_DROPLET_IP","https://yourdomain.com"]

# SMTP (opcional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@yourdomain.com
```

Guardar: `Ctrl+X`, `Y`, `Enter`

## 🐳 Paso 4: Iniciar Servicios

```bash
# Levantar servicios
docker compose -f docker-compose.prod.yml up -d

# Ver logs
docker compose -f docker-compose.prod.yml logs -f

# Verificar que todo esté corriendo
docker compose -f docker-compose.prod.yml ps
```

Deberías ver:
```
healthcheck-db      running
healthcheck-app     running
healthcheck-nginx   running
```

## 🗄️ Paso 5: Configurar Base de Datos

```bash
# Ejecutar migraciones
docker compose -f docker-compose.prod.yml exec app alembic upgrade head

# Verificar
docker compose -f docker-compose.prod.yml exec app alembic current
```

## ✅ Paso 6: Verificar Instalación

### 6.1 Health Check

```bash
curl http://localhost:8000/health
```

Deberías ver:
```json
{
  "status": "healthy",
  "app": "Health Check Panel",
  "environment": "production"
}
```

### 6.2 Acceder desde el Navegador

Abre en tu navegador:
```
http://YOUR_DROPLET_IP
```

Deberías ver la página de login.

### 6.3 Crear Primer Usuario

```bash
curl -X POST http://YOUR_DROPLET_IP/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@yourdomain.com",
    "password": "secure-password-here",
    "full_name": "Admin User",
    "organization_name": "Your Company"
  }'
```

## 🔐 Paso 7: Configurar Firewall

```bash
# Permitir SSH, HTTP, HTTPS
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp

# Activar firewall
ufw --force enable

# Verificar
ufw status
```

## 🤖 Paso 8: Configurar Auto-Deploy con GitHub Actions

### 8.1 Generar SSH Key para GitHub Actions

En el Droplet:

```bash
# Generar nueva key
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/github_actions -N ""

# Ver clave privada (la copiarás a GitHub)
cat ~/.ssh/github_actions

# Añadir clave pública a authorized_keys
cat ~/.ssh/github_actions.pub >> ~/.ssh/authorized_keys
```

### 8.2 Configurar GitHub Secrets

1. Ve a tu repositorio en GitHub
2. Settings → Secrets and variables → Actions
3. Click **New repository secret**

Añade estos secrets:

**DROPLET_HOST**
```
YOUR_DROPLET_IP
```

**DROPLET_USER**
```
root
```

**DROPLET_SSH_KEY**
```
(pega el contenido de ~/.ssh/github_actions - la clave PRIVADA)
```

### 8.3 Actualizar deploy.sh

Edita el archivo `deploy.sh` en tu repositorio local:

```bash
# Cambiar esta línea
REPO_URL="https://github.com/YOUR-USERNAME/health-check-panel.git"
```

### 8.4 Hacer Deploy Automático

Ahora cada vez que hagas push a `main`:

```bash
git add .
git commit -m "Update configuration"
git push origin main
```

GitHub Actions automáticamente:
1. ✅ Conecta al Droplet por SSH
2. ✅ Hace `git pull`
3. ✅ Reconstruye containers
4. ✅ Ejecuta migraciones
5. ✅ Reinicia servicios

Ver el progreso en: GitHub → Actions tab

## 🌐 Paso 9: Configurar Dominio (Opcional)

### 9.1 Configurar DNS

En tu proveedor de dominio (Namecheap, GoDaddy, etc.):

```
Tipo: A
Host: @
Value: YOUR_DROPLET_IP
TTL: 3600

Tipo: A
Host: www
Value: YOUR_DROPLET_IP
TTL: 3600
```

### 9.2 Configurar SSL con Let's Encrypt

```bash
# Instalar Certbot
apt install certbot python3-certbot-nginx -y

# Generar certificado
certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Verificar auto-renovación
certbot renew --dry-run
```

### 9.3 Actualizar CORS

Edita `.env` en el Droplet:

```bash
CORS_ORIGINS=["https://yourdomain.com","https://www.yourdomain.com"]
```

Reiniciar:

```bash
docker compose -f docker-compose.prod.yml restart app
```

## 📊 Paso 10: Monitoreo

### Ver Logs

```bash
# Todos los servicios
docker compose -f docker-compose.prod.yml logs -f

# Solo app
docker compose -f docker-compose.prod.yml logs -f app

# Solo nginx
docker compose -f docker-compose.prod.yml logs -f nginx

# Solo PostgreSQL
docker compose -f docker-compose.prod.yml logs -f postgres
```

### Verificar Estado

```bash
docker compose -f docker-compose.prod.yml ps
```

### Recursos del Sistema

```bash
# CPU y RAM
htop

# Espacio en disco
df -h

# Uso de Docker
docker system df
```

## 🔄 Comandos Útiles

### Reiniciar Servicios

```bash
# Reiniciar todo
docker compose -f docker-compose.prod.yml restart

# Reiniciar solo app
docker compose -f docker-compose.prod.yml restart app
```

### Actualizar Manualmente

```bash
cd /opt/healthcheck
./deploy.sh
```

### Hacer Backup de Base de Datos

```bash
# Crear backup
docker compose -f docker-compose.prod.yml exec postgres pg_dump -U healthcheck healthcheck > backup_$(date +%Y%m%d).sql

# Restaurar backup
docker compose -f docker-compose.prod.yml exec -T postgres psql -U healthcheck healthcheck < backup_20260123.sql
```

### Limpiar Docker

```bash
# Eliminar containers no usados
docker system prune -a

# Liberar espacio
docker volume prune
```

## 🆘 Troubleshooting

### Error: "Cannot connect to Docker daemon"

```bash
systemctl start docker
systemctl enable docker
```

### Error: "Port 80 already in use"

```bash
# Ver qué usa el puerto
lsof -i :80

# Matar proceso si es necesario
kill -9 PID
```

### Error: "Database connection failed"

```bash
# Verificar que PostgreSQL está corriendo
docker compose -f docker-compose.prod.yml ps postgres

# Ver logs
docker compose -f docker-compose.prod.yml logs postgres

# Reiniciar
docker compose -f docker-compose.prod.yml restart postgres
```

### Error: "Health check failed"

```bash
# Ver logs de la app
docker compose -f docker-compose.prod.yml logs app

# Verificar variables de entorno
docker compose -f docker-compose.prod.yml exec app env | grep DATABASE

# Reiniciar
docker compose -f docker-compose.prod.yml restart app
```

### GitHub Actions falla en deploy

1. Verificar secrets en GitHub
2. Verificar SSH key en Droplet
3. Ver logs en GitHub Actions tab
4. Probar conexión SSH manual:
   ```bash
   ssh -i ~/.ssh/github_actions root@YOUR_DROPLET_IP
   ```

## 🔒 Seguridad

### Checklist

- [ ] Firewall configurado (`ufw status`)
- [ ] SSH key authentication (no password)
- [ ] SSL/HTTPS configurado
- [ ] Secrets en `.env` no en código
- [ ] Backups configurados
- [ ] Monitoreo activo

### Recomendaciones

1. **Cambiar passwords regularmente**
2. **No usar root** - crear usuario dedicado
3. **Fail2ban** para prevenir ataques SSH
4. **Actualizar sistema** regularmente
5. **Backups automáticos** diarios

## 📈 Próximos Pasos

1. ✅ Droplet configurado
2. ✅ Auto-deploy funcionando
3. 🔄 Configurar dominio y SSL
4. 🔄 Crear usuarios y sitios
5. 🔄 Configurar checks
6. 🔄 Configurar notificaciones
7. 📊 Añadir monitoreo avanzado

## 🆘 Soporte

- **DigitalOcean Docs**: https://docs.digitalocean.com
- **Docker Docs**: https://docs.docker.com
- **GitHub Actions**: https://docs.github.com/actions

---

¡Listo! Tu Health Check Panel está corriendo en producción con auto-deploy. 🚀
