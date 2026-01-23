# Health Check Panel - Astro Frontend

Dashboard ultra-rápido construido con Astro + React Islands.

## ⚡ Por qué Astro

- **Menos JavaScript**: Solo carga JS donde es necesario (islas)
- **Más Rápido**: Server-side rendering por defecto
- **Flexible**: Usa React solo para componentes interactivos
- **Mejor SEO**: HTML renderizado en servidor
- **Build pequeño**: ~40% menos bundle que Next.js

## 🚀 Quick Start

```bash
cd frontend

# Instalar dependencias
npm install

# Desarrollo
npm run dev
```

Abre http://localhost:3000

## 📦 Dependencias

- **Astro 4** - Framework principal
- **React 18** - Para componentes interactivos (islas)
- **TanStack Query** - Data fetching
- **Tremor** - Charts y dashboard
- **TailwindCSS** - Estilos
- **Zustand** - Auth state

## 🏗️ Arquitectura

### Astro Components (.astro)
- Páginas estáticas
- Layouts
- Renderizado en servidor
- Zero JS por defecto

### React Islands (.tsx con client:*)
- Forms interactivos
- Real-time updates (SSE)
- Data fetching con TanStack Query
- Auth state

## 📁 Estructura

```
src/
├── pages/                  # Rutas Astro
│   ├── index.astro         # Home (redirect)
│   ├── login.astro         # Login page
│   └── dashboard/
│       └── index.astro     # Dashboard
├── layouts/
│   ├── BaseLayout.astro    # Layout base
│   └── DashboardLayout.astro
├── components/
│   ├── DashboardNav.tsx    # React Island
│   ├── DashboardContent.tsx
│   ├── LoginForm.tsx
│   └── QueryProvider.tsx
└── lib/
    ├── api.ts              # API client
    └── auth-store.ts       # Zustand auth
```

## 🎯 Directivas de Cliente

### `client:load`
Carga inmediatamente, hidrata al cargar:
```astro
<DashboardNav client:load />
```

### `client:only="react"`
Solo client-side (no SSR):
```astro
<LoginForm client:only="react" />
```

### `client:visible`
Carga cuando es visible:
```astro
<Chart client:visible />
```

## 🔐 Autenticación

Login con credenciales por defecto:
- **Email**: admin@admin.com
- **Password**: admin

## 📊 Estado vs Next.js

| Feature | Next.js | Astro |
|---------|---------|-------|
| Bundle size | ~200KB | ~80KB |
| Time to Interactive | ~2s | ~0.5s |
| JavaScript | Todo | Solo islas |
| SSR | Sí | Sí |
| Hidratación | Total | Parcial |

## 🛠️ Scripts

```bash
npm run dev      # Development
npm run build    # Build para producción
npm run preview  # Preview build
```

## 🚢 Deploy

Build crea carpeta `dist/` con static files + server functions.

Compatible con:
- Vercel
- Netlify
- DigitalOcean Apps
- Cloudflare Pages

## ✨ Próximos Pasos

- [ ] Completar todas las páginas
- [ ] SSE real-time updates
- [ ] Gráficas con Tremor
- [ ] Forms dinámicos
- [ ] Optimizar bundle
