# Deployment Guide - Supabase + Vercel

This guide explains how to deploy the Health Check Panel using Supabase for the database and Vercel for hosting.

## Prerequisites

- [Supabase](https://supabase.com) account
- [Vercel](https://vercel.com) account
- [GitHub](https://github.com) account (for connecting to Vercel)

---

## 1. Supabase Setup (Database)

### Step 1: Create a Supabase Project

1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Click "New Project"
3. Fill in the details:
   - **Name**: `healthcheck-panel`
   - **Database Password**: Generate a secure password (save this!)
   - **Region**: Choose closest to your users
4. Click "Create new project"

### Step 2: Run the Database Schema

1. In your Supabase project, go to **SQL Editor**
2. Copy the contents of `supabase/schema.sql`
3. Paste and run the SQL
4. Verify tables were created in **Table Editor**

### Step 3: Get Connection String

1. Go to **Settings** > **Database**
2. Find **Connection string** section
3. Copy the **URI** (starts with `postgresql://`)
4. Replace `[YOUR-PASSWORD]` with your database password
5. Add `+asyncpg` after `postgresql`:
   ```
   postgresql+asyncpg://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
   ```

---

## 2. Backend Deployment

The backend (FastAPI) can be deployed to various platforms:

### Option A: Railway (Recommended)

1. Go to [Railway](https://railway.app)
2. Create new project from GitHub repo
3. Add environment variables:
   ```
   DATABASE_URL=postgresql+asyncpg://...your-supabase-url...
   SECRET_KEY=your-secret-key-generate-with-openssl-rand-hex-32
   ENVIRONMENT=production
   CORS_ORIGINS=["https://your-vercel-app.vercel.app"]
   ```
4. Deploy and get the backend URL

### Option B: Render

1. Go to [Render](https://render.com)
2. Create new Web Service from GitHub
3. Set build command: `pip install -r backend/requirements.txt`
4. Set start command: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables (same as Railway)

### Option C: Fly.io

1. Install Fly CLI: `curl -L https://fly.io/install.sh | sh`
2. Create `fly.toml` in backend directory
3. Deploy: `fly deploy`

---

## 3. Frontend Deployment (Vercel)

### Step 1: Connect Repository

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click "Add New" > "Project"
3. Import your GitHub repository
4. Select the repository

### Step 2: Configure Project

1. Set **Framework Preset**: `Astro`
2. Set **Root Directory**: `frontend`
3. Add environment variables:
   ```
   PUBLIC_API_URL=https://your-backend-url.com/api/v1
   ```

### Step 3: Deploy

1. Click "Deploy"
2. Wait for build to complete
3. Your app will be available at `https://your-project.vercel.app`

---

## 4. Environment Variables Reference

### Backend (.env)

```env
# Database (Supabase)
DATABASE_URL=postgresql+asyncpg://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres

# Security
SECRET_KEY=your-32-char-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Environment
ENVIRONMENT=production

# CORS (your Vercel frontend URL)
CORS_ORIGINS=["https://your-app.vercel.app"]

# Email (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@yourdomain.com
```

### Frontend (Vercel Environment Variables)

```
PUBLIC_API_URL=https://your-backend-url.com/api/v1
```

---

## 5. Default Login Credentials

After deploying, use these credentials to log in:

- **Email**: `admin@admin.com`
- **Password**: `adminadmin`

**Important**: Change the password after first login!

---

## 6. Post-Deployment Checklist

- [ ] Database schema created in Supabase
- [ ] Backend deployed and accessible
- [ ] Frontend deployed to Vercel
- [ ] Environment variables configured
- [ ] CORS configured correctly
- [ ] Login working with default credentials
- [ ] Password changed from default

---

## Troubleshooting

### CORS Errors
- Ensure `CORS_ORIGINS` in backend includes your Vercel URL
- Include both `https://` versions

### Database Connection Issues
- Verify `DATABASE_URL` uses `postgresql+asyncpg://`
- Check Supabase is not in paused state
- Verify password is correct

### 500 Errors
- Check backend logs in your hosting platform
- Verify all environment variables are set
- Check database connection

### Build Failures
- Run `npm run build` locally to check for errors
- Check Node.js version compatibility (18+)

---

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│     Vercel      │────▶│  Backend API    │────▶│    Supabase     │
│   (Frontend)    │     │  (Railway/etc)  │     │   (PostgreSQL)  │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
      Astro              FastAPI + Python         PostgreSQL
```
