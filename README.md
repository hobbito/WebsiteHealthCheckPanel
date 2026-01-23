# Health Check Panel

Multi-user website health monitoring system with extensible checks, real-time notifications, and comprehensive dashboard.

## Features

- **Extensible Check System**: Plugin architecture for different check types (HTTP, DNS, Email, Custom Tests)
- **Real-time Updates**: Server-Sent Events (SSE) for live dashboard updates
- **Multi-user Support**: Organization-based access with role management
- **Scheduled Monitoring**: APScheduler with PostgreSQL persistence (no Redis required)
- **Smart Notifications**: Multi-channel notifications (Email, Slack, Discord, Webhook)
- **Historical Analytics**: Full check result history with charts and uptime calculations
- **Cost-effective**: Single-container deployment optimized for DigitalOcean Apps (~$20/mo)

## Tech Stack

### Backend
- **FastAPI 0.109+** - Modern async Python framework
- **PostgreSQL 16** - Primary database with JSONB support
- **APScheduler 3.10+** - In-process task scheduling (no Redis/Celery)
- **SQLAlchemy 2.0+** - Async ORM
- **SSE-Starlette** - Server-Sent Events for real-time updates

### Frontend
- **Astro 4** - Modern web framework with React Islands
- **React 18** - UI library for interactive components
- **TanStack Query v5** - Server state management
- **Tremor** - Dashboard components
- **TailwindCSS** - Styling
- **Zustand** - Client-side state management

## Quick Start (Local Development)

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker & Docker Compose (for PostgreSQL)

### Option 1: Automated Setup (Recommended)

```bash
# Complete setup (install dependencies + database + migrations + seed)
make setup

# Start all services (backend + frontend + database)
make up-bg

# Access the application
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/api/docs

# Default login credentials:
# Email: admin@admin.com
# Password: admin
```

### Option 2: Manual Setup

```bash
# 1. Install dependencies
make install  # or: make install-backend && make install-frontend

# 2. Start PostgreSQL
make db-up

# 3. Run migrations
make migrate

# 4. Seed default admin user
make seed

# 5. Start services
make up-bg  # Run in background
# OR
make up-interactive  # Interactive mode (shows frontend logs)
```

### Available Make Commands

```bash
make help           # Show all available commands
make status         # Check status of all services
make down           # Stop all services
make logs           # Show all logs
make clean          # Clean all generated files
```

### Access Points

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/docs
- **Default Credentials**: admin@admin.com / admin

## API Usage Examples

### Register a User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "securepassword123",
    "full_name": "Admin User",
    "organization_name": "My Company"
  }'
```

### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=securepassword123"
```

### Create a Site

```bash
curl -X POST http://localhost:8000/api/v1/sites \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Google",
    "url": "https://google.com",
    "description": "Search engine"
  }'
```

### List Available Check Types

```bash
curl http://localhost:8000/api/v1/checks/types \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Create an HTTP Check

```bash
curl -X POST http://localhost:8000/api/v1/checks \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "site_id": 1,
    "check_type": "http",
    "name": "Homepage Status Check",
    "interval_seconds": 300,
    "configuration": {
      "expected_status_code": 200,
      "timeout_seconds": 10,
      "follow_redirects": true,
      "verify_ssl": true,
      "max_response_time_ms": 3000
    }
  }'
```

### Real-time Updates (SSE)

```bash
# Connect to SSE stream (in browser or with curl)
curl -N http://localhost:8000/api/v1/stream/updates \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Available Check Types

### 1. HTTP Check (`http`)
Monitors HTTP status codes and response times.

**Configuration:**
```json
{
  "expected_status_code": 200,
  "timeout_seconds": 10,
  "follow_redirects": true,
  "verify_ssl": true,
  "max_response_time_ms": 3000
}
```

### 2. DNS Check (`dns`)
Verifies DNS records against expected values.

**Configuration:**
```json
{
  "record_type": "A",
  "expected_values": ["142.250.185.46"],
  "nameserver": "8.8.8.8",
  "timeout_seconds": 5
}
```

Record types: `A`, `AAAA`, `CNAME`, `MX`, `TXT`, `NS`

## Architecture

### Check Plugin System

All checks implement the `BaseCheck` interface:

```python
class BaseCheck(ABC):
    @abstractmethod
    async def execute(self, url: str, config: Dict[str, Any]) -> CheckResult:
        """Execute the check"""
        pass

    @classmethod
    @abstractmethod
    def get_config_schema(cls) -> Dict[str, Any]:
        """Return JSON schema for configuration"""
        pass
```

### Scheduling (APScheduler)

- **No Redis/Celery required** - APScheduler uses PostgreSQL for job persistence
- **Async execution** - Non-blocking check execution with asyncio
- **Dynamic scheduling** - Add/remove/update jobs at runtime
- **Perfect for PaaS** - Single-process deployment (ideal for DigitalOcean Apps)

### Real-time Updates (SSE + In-Memory Event Bus)

```python
# Backend publishes events
await event_bus.publish(f'org:{org_id}', {
    'type': 'check_result',
    'site_id': site.id,
    'status': 'success',
    'response_time_ms': 123
})

# Frontend subscribes via SSE
const eventSource = new EventSource('/api/v1/stream/updates');
eventSource.addEventListener('check_result', (event) => {
    const data = JSON.parse(event.data);
    // Update dashboard in real-time
});
```

## Deployment to DigitalOcean Apps

### 1. Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/your-username/health-check-panel.git
git push -u origin main
```

### 2. Create App in DigitalOcean

1. Go to DigitalOcean Dashboard → Apps
2. Click "Create App" → Connect GitHub repository
3. DigitalOcean auto-detects `Dockerfile`
4. Add PostgreSQL database (creates `DATABASE_URL` automatically)
5. Set environment variables:
   - `SECRET_KEY`: Generate random string
   - `ENVIRONMENT`: `production`
   - `CORS_ORIGINS`: Your app URL
6. Deploy!

### 3. Cost Estimate

- **App (basic-xs)**: $5/mo
- **PostgreSQL (basic)**: $15/mo
- **Total**: ~$20/mo

Can handle 100-500 domains easily. Upgrade to professional-xs ($12/mo) for larger scale.

## Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

## Project Structure

```
/Users/alex/Sites/WebsiteHealthCheckPanel/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API endpoints
│   │   ├── checks/          # Check plugins
│   │   ├── core/            # Security, scheduler, event bus
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   ├── tasks/           # Background tasks
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── main.py
│   │   └── seed.py          # Database seeder
│   ├── alembic/             # Database migrations
│   └── requirements.txt
├── frontend/                # Astro + React Islands
│   ├── src/
│   │   ├── components/      # React components (islands)
│   │   ├── layouts/         # Astro layouts
│   │   ├── lib/             # API client, stores
│   │   └── pages/           # Astro pages
│   ├── astro.config.mjs
│   └── package.json
├── .do/
│   └── app.yaml            # DigitalOcean config
├── Dockerfile
├── docker-compose.yml
├── Makefile                # Development commands
└── README.md
```

## Adding New Check Types

1. Create new file in `backend/app/checks/`:

```python
from app.checks.base import BaseCheck, CheckResult
from app.checks.registry import CheckRegistry

@CheckRegistry.register
class MyCustomCheck(BaseCheck):
    @classmethod
    def get_display_name(cls) -> str:
        return "My Custom Check"

    @classmethod
    def get_config_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "my_param": {"type": "string"}
            }
        }

    async def execute(self, url: str, config: Dict[str, Any]) -> CheckResult:
        # Implement check logic
        return CheckResult(
            status=CheckStatus.SUCCESS,
            response_time_ms=100
        )
```

2. Import in `main.py` to register:

```python
from app.checks import mycustom_check  # noqa: F401
```

That's it! The check will automatically appear in `/api/v1/checks/types`.

## Development Roadmap

**Completed:**
- ✅ Backend infrastructure (FastAPI + PostgreSQL)
- ✅ Authentication system (JWT)
- ✅ Site management API
- ✅ Check plugin architecture
- ✅ HTTP and DNS checks
- ✅ APScheduler integration with PostgreSQL jobstore
- ✅ Real-time SSE updates with in-memory event bus
- ✅ Docker & Docker Compose configuration
- ✅ Default admin seeder
- ✅ Makefile for easy development
- ✅ Frontend infrastructure (Astro + React Islands)
- ✅ Login and authentication flow
- ✅ Basic dashboard structure

**In Progress:**
- 🚧 Complete dashboard pages (sites list, check configuration)
- 🚧 Real-time updates in frontend
- 🚧 Charts and analytics

**Coming Soon:**
- 📋 Notification system (Email, Slack, Discord)
- 📋 Incident tracking and alerting
- 📋 Historical analytics & charts
- 📋 Email delivery checks
- 📋 Custom test execution
- 📋 Public status pages
- 📋 User management UI

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - See LICENSE file for details

## Support

For issues and questions:
- GitHub Issues: [Create an issue](https://github.com/your-username/health-check-panel/issues)
- Documentation: [API Docs](http://localhost:8000/api/docs) (when running locally)
