# Backend Architecture

## Estructura por Dominios (Domain-Driven Design)

El backend está organizado por dominios de negocio, cada uno con su propia responsabilidad clara.

```
backend/app/
├── core/                   # Infraestructura compartida
│   ├── config.py          # Configuración de la aplicación
│   ├── database.py        # Setup de base de datos (SQLAlchemy)
│   ├── security.py        # Autenticación JWT y passwords
│   ├── event_bus.py       # Sistema de eventos in-memory para SSE
│   └── scheduler.py       # APScheduler setup
│
├── domains/                # Lógica de negocio por dominio
│   ├── auth/              # Autenticación y usuarios
│   │   ├── models.py      # User, Organization (SQLAlchemy)
│   │   ├── schemas.py     # Pydantic schemas (validation)
│   │   └── api.py         # FastAPI routes (/auth/*)
│   │
│   ├── sites/             # Gestión de sitios web a monitorear
│   │   ├── models.py      # Site
│   │   ├── schemas.py     # SiteCreate, SiteResponse
│   │   └── api.py         # FastAPI routes (/sites/*)
│   │
│   ├── checks/            # Sistema de health checks
│   │   ├── models.py      # CheckConfiguration, CheckResult, Incident
│   │   ├── schemas.py     # Check schemas
│   │   ├── service.py     # SchedulerService (lógica de negocio)
│   │   ├── api.py         # FastAPI routes (/checks/*)
│   │   └── plugins/       # Implementaciones de checks extensibles
│   │       ├── base.py         # BaseCheck (interfaz)
│   │       ├── registry.py     # CheckRegistry (patrón Registry)
│   │       └── http_check.py   # HTTPCheck implementation
│   │
│   └── notifications/     # Sistema de notificaciones (TODO)
│       ├── models.py
│       ├── schemas.py
│       ├── service.py
│       ├── api.py
│       └── channels/      # Email, Slack, Discord
│
├── api/v1/                # API routes que no pertenecen a un dominio específico
│   └── stream.py          # Server-Sent Events endpoint
│
├── tasks/                 # Background tasks
│   └── checks.py          # execute_check(), sync_check_schedules()
│
├── shared/                # Utilidades compartidas (si necesario)
│
└── main.py                # FastAPI app entry point
```

## Principios de la Arquitectura

### 1. Separación por Dominios
Cada dominio es autónomo y contiene:
- **models.py**: Modelos de base de datos (SQLAlchemy)
- **schemas.py**: Schemas de validación (Pydantic)
- **api.py**: Rutas de API (FastAPI)
- **service.py**: Lógica de negocio compleja (opcional)

### 2. Dependencias
- **Dominios NO dependen entre sí directamente**
- Usan imports explícitos cuando es necesario: `from app.domains.auth.models import User`
- Core puede ser usado por cualquier dominio

### 3. Plugin Architecture
El sistema de checks usa un patrón de plugins:
- **BaseCheck**: Interfaz que todos los checks deben implementar
- **CheckRegistry**: Registry pattern para autodiscovery de checks
- **Decorator `@register_check`**: Registra checks automáticamente

Ejemplo de nuevo check:
```python
from app.domains.checks.plugins.base import BaseCheck, CheckResult
from app.domains.checks.plugins.registry import register_check

@register_check
class DNSCheck(BaseCheck):
    check_type = "dns"
    display_name = "DNS Check"
    description = "Verify DNS records"

    async def execute(self, url: str, config: dict) -> CheckResult:
        # Implementation
        pass
```

### 4. Scheduler Service
- Usa **APScheduler** con PostgreSQL jobstore (no requiere Redis/Celery)
- Jobs persisten en DB (sobreviven restarts)
- Ejecuta `execute_check(check_id)` según interval configurado
- Ver `domains/checks/service.py`

### 5. Real-time Updates
- **EventBus** in-memory (ver `core/event_bus.py`)
- Publica eventos cuando checks completan
- SSE endpoint (`/api/v1/stream/updates`) consume eventos
- **No requiere Redis** (simple pub/sub in-memory)

## Flujo de un Health Check

1. Usuario crea check via API (`POST /api/v1/checks/`)
2. CheckConfiguration se guarda en DB
3. `SchedulerService.add_check_job()` registra job en APScheduler
4. APScheduler ejecuta `execute_check(check_id)` cada `interval_seconds`
5. `execute_check()`:
   - Carga CheckConfiguration desde DB
   - Obtiene plugin del CheckRegistry
   - Ejecuta check
   - Guarda CheckResult en DB
   - Publica evento a EventBus
6. Clientes conectados via SSE reciben update en tiempo real

## Migrations

Usa Alembic:
```bash
# Crear nueva migración
alembic revision --autogenerate -m "Add new field"

# Aplicar migraciones
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Testing

Tests están en `/tests/`:
```
tests/
├── integration/
│   └── test_health_check_flow.sh   # Test end-to-end
└── unit/
    └── ...
```

Ejecutar test E2E:
```bash
cd /Users/alex/Sites/WebsiteHealthCheckPanel
bash tests/integration/test_health_check_flow.sh
```

## Beneficios de esta Arquitectura

### Mantenibilidad
- ✅ Código organizado por responsabilidad de negocio
- ✅ Fácil encontrar dónde está cada funcionalidad
- ✅ Cambios en un dominio no afectan a otros

### Escalabilidad
- ✅ Nuevos checks se añaden sin tocar código core
- ✅ Nuevos dominios se añaden fácilmente
- ✅ Services extraen lógica compleja de los endpoints

### Testabilidad
- ✅ Cada dominio puede testearse independientemente
- ✅ Services pueden mockearse fácilmente
- ✅ Plugins tienen interfaces claras

### Simplicidad
- ✅ No usa microservicios (innecesario para la escala)
- ✅ No usa capas excesivas (no hexagonal full)
- ✅ Simple pero robusto

## Próximos Pasos

1. **Implementar dominio de notifications**:
   - `domains/notifications/models.py` (NotificationChannel, NotificationRule)
   - `domains/notifications/channels/` (EmailChannel, SlackChannel)
   - `domains/notifications/service.py` (NotificationService)

2. **Añadir más check plugins**:
   - `domains/checks/plugins/dns_check.py`
   - `domains/checks/plugins/email_check.py`

3. **Testing**:
   - Unit tests para cada dominio
   - Integration tests para flujos completos

## Comandos Útiles

```bash
# Iniciar backend
cd backend
./venv/bin/uvicorn app.main:app --reload

# Ver jobs de APScheduler (en Python shell)
from app.core.scheduler import get_scheduler
scheduler = get_scheduler()
scheduler.get_jobs()

# Seed database
./venv/bin/python app/seed.py
```
