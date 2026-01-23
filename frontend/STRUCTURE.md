# Frontend Structure

## Arquitectura

Frontend construido con **Astro 4 + React Islands** para óptimo rendimiento.

## Estructura de Directorios

```
src/
├── components/           # Componentes React (client-side)
│   ├── auth/            # Componentes de autenticación
│   │   └── LoginForm.tsx
│   ├── dashboard/       # Componentes del dashboard
│   │   ├── Dashboard.tsx
│   │   ├── DashboardHeader.tsx
│   │   ├── DashboardStats.tsx
│   │   └── SitesList.tsx
│   └── common/          # Componentes reutilizables
│       └── LoadingSpinner.tsx
├── layouts/             # Layouts de Astro
│   ├── BaseLayout.astro
│   └── DashboardLayout.astro
├── pages/               # Rutas (Astro file-based routing)
│   ├── index.astro      # Redirect a login
│   ├── login.astro      # Página de login
│   └── dashboard/
│       └── index.astro  # Dashboard principal
├── lib/                 # Utilidades y tipos
│   ├── api.ts           # Cliente API Axios
│   └── types.ts         # TypeScript types compartidos
└── env.d.ts             # Tipos de entorno Astro
```

## Principios de Diseño

### 1. **Componentes Pequeños y Enfocados**
Cada componente tiene una responsabilidad única:
- `LoginForm`: Solo maneja el formulario de login
- `DashboardHeader`: Solo el header con usuario y logout
- `DashboardStats`: Solo las tarjetas de estadísticas
- `SitesList`: Solo la lista de sitios

### 2. **Separation of Concerns**
- **Páginas (.astro)**: Routing y estructura HTML mínima
- **Componentes React**: Lógica interactiva y UI
- **lib/**: Lógica de negocio y tipos compartidos

### 3. **Client Islands**
Solo los componentes que necesitan interactividad son React:
```astro
<LoginForm client:only="react" />
<Dashboard client:only="react" />
```

### 4. **TypeScript Types Centralizados**
Todos los tipos en `lib/types.ts`:
- `User`
- `Site`
- `Check`
- `CheckResult`

## Flujo de Datos

### Login
1. Usuario envía formulario (`LoginForm.tsx`)
2. POST a `/api/v1/auth/login`
3. Guarda tokens en `localStorage`
4. GET a `/api/v1/auth/me` para obtener usuario
5. Redirect a `/dashboard`

### Dashboard
1. Carga y verifica token (`Dashboard.tsx`)
2. GET a `/api/v1/auth/me` para usuario
3. GET a `/api/v1/sites/` para sitios
4. Distribuye datos a componentes hijos:
   - `DashboardHeader`: recibe `user`
   - `DashboardStats`: recibe `sites` y `user`
   - `SitesList`: recibe `sites`

## Añadir Nuevas Funcionalidades

### Ejemplo: Añadir página de "Site Detail"

1. **Crear componente**:
```tsx
// src/components/dashboard/SiteDetail.tsx
export default function SiteDetail({ siteId }: { siteId: number }) {
  // Lógica del componente
}
```

2. **Crear página**:
```astro
---
// src/pages/dashboard/sites/[id].astro
import SiteDetail from '@/components/dashboard/SiteDetail'
const { id } = Astro.params
---

<SiteDetail siteId={Number(id)} client:only="react" />
```

3. **Actualizar tipos** (si necesario):
```ts
// src/lib/types.ts
export interface SiteDetail extends Site {
  checks: Check[]
  last_result?: CheckResult
}
```

## Comandos

```bash
# Desarrollo
npm run dev

# Build para producción
npm run build

# Preview build
npm run preview
```

## Notas Técnicas

- **No SSR para componentes React**: Usamos `client:only="react"` para evitar problemas de hidratación
- **Axios directo**: Sin abstracciones complejas, llamadas HTTP directas
- **LocalStorage**: Para tokens y estado de autenticación
- **No state management**: Estado local en cada componente (suficiente para esta escala)
