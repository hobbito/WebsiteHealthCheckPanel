# Changelog

Registro de cambios importantes del proyecto.

## [2026-01-24] - Refactoring Arquitectura por Dominios

### Added
- ✅ Nueva estructura de dominios en `backend/app/domains/`
  - `domains/auth/` - Autenticación y usuarios
  - `domains/sites/` - Gestión de sitios
  - `domains/checks/` - Sistema de health checks + plugins
  - `domains/notifications/` - (Estructura preparada para futuro)

- ✅ Documentación completa
  - `backend/ARCHITECTURE.md` - Documentación técnica detallada
  - `REFACTORING.md` - Documento de refactoring con checklist completo
  - README.md actualizado con nueva estructura

- ✅ Tests organizados
  - Directorio `tests/integration/` creado
  - `test_health_check.sh` movido a su ubicación correcta

- ✅ Método `is_registered()` añadido a `CheckRegistry`
  - Corrige error en creación de checks via API

### Changed
- ✅ `config.py` y `database.py` movidos a `core/`
- ✅ Todos los modelos consolidados por dominio
  - `auth/models.py`: User + Organization
  - `sites/models.py`: Site
  - `checks/models.py`: CheckConfiguration + CheckResult + Incident

- ✅ Todos los schemas consolidados por dominio
  - `auth/schemas.py`: UserRegister, Token, UserResponse
  - `sites/schemas.py`: SiteCreate, SiteUpdate, SiteResponse
  - `checks/schemas.py`: CheckConfigurationCreate, CheckResultResponse

- ✅ Todos los routers movidos a sus dominios
  - `auth/api.py`: Router de /auth
  - `sites/api.py`: Router de /sites
  - `checks/api.py`: Router de /checks

- ✅ Plugins de checks reorganizados en `domains/checks/plugins/`
  - `base.py`, `registry.py`, `http_check.py`

- ✅ Services consolidados en dominios
  - `checks/service.py`: SchedulerService

### Fixed
- ✅ Todos los imports actualizados
  - `main.py` usa nuevos imports de dominios
  - `seed.py` actualizado
  - `tasks/checks.py` actualizado
  - `core/security.py` actualizado
  - `core/database.py` actualizado
  - `core/scheduler.py` actualizado
  - `api/v1/stream.py` actualizado

### Technical Debt Removed
- ❌ Eliminada duplicación de models en múltiples archivos
- ❌ Eliminada mezcla de schemas en un solo directorio sin organización
- ❌ Eliminada confusión entre api/ y models/schemas separados

### Breaking Changes
- ✅ **NINGUNO** - Todas las rutas de API permanecen iguales
- ✅ Frontend NO requiere cambios
- ✅ Migraciones de DB funcionan sin cambios
- ✅ Tests existentes funcionan sin modificación

### Migration Guide
Para código nuevo, usar los nuevos imports:
```python
# ANTES
from app.models.user import User
from app.models.site import Site
from app.schemas.auth import UserRegister
from app.checks.registry import CheckRegistry

# AHORA
from app.domains.auth.models import User
from app.domains.sites.models import Site
from app.domains.auth.schemas import UserRegister
from app.domains.checks.plugins.registry import CheckRegistry
```

### Verification
```bash
# Test que imports funcionan
cd backend
./venv/bin/python -c "from app.main import app; print('✓ OK')"

# Output esperado:
# ✓ Registered check type: http
# ✓ OK
```

### Documentation
- Ver `backend/ARCHITECTURE.md` para documentación completa de arquitectura
- Ver `REFACTORING.md` para detalles del proceso de refactoring
- Ver `README.md` actualizado con nueva estructura

---

## [2026-01-23] - Infraestructura Inicial

### Added
- ✅ Backend FastAPI con PostgreSQL
- ✅ Sistema de autenticación JWT
- ✅ APScheduler con PostgreSQL jobstore
- ✅ EventBus in-memory para SSE
- ✅ Check plugin architecture
- ✅ HTTPCheck implementation
- ✅ Frontend Astro + React Islands
- ✅ Dashboard básico con navbar
- ✅ Login flow completo
- ✅ Sites CRUD completo
- ✅ Checks CRUD completo
- ✅ Modal component reutilizable
- ✅ Makefile para desarrollo
- ✅ Docker Compose para PostgreSQL local

### Features Completados
- Sistema de checks extensible
- Sites management
- User authentication
- Real-time updates infrastructure (SSE)
- Scheduling infrastructure (APScheduler)

### Pending Features
- Notifications system
- DNS check implementation
- Email check implementation
- Charts and analytics
- Public status pages
- Incident tracking
