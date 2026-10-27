# TaskFlow AI — Django Task Management & AI Support Platform

> A Django task management web application with an AI assistant, FAQ system, error guide, and support ticket management.

Built with **Django 6**, **Google Gemini GenAI**, **MongoDB (NoSQL)**, **SQLite / PostgreSQL (SQL)**, and a **Dark Glassmorphism** user interface.

## 🌐 Live Demo

- **Website**: [https://taskflow-omega-ruddy-39.vercel.app](https://taskflow-omega-ruddy-39.vercel.app/)
- **Health Check**: [https://taskflow-omega-ruddy-39.vercel.app/health/](https://taskflow-omega-ruddy-39.vercel.app/health/)

| Page / Feature | Live Production URL | Local Development URL |
| :--- | :--- | :--- |
| **Dashboard** | [https://taskflow-omega-ruddy-39.vercel.app/dashboard/](https://taskflow-omega-ruddy-39.vercel.app/dashboard/) | `http://127.0.0.1:8000/dashboard/` |
| **Tasks Board** | [https://taskflow-omega-ruddy-39.vercel.app/tasks/](https://taskflow-omega-ruddy-39.vercel.app/tasks/) | `http://127.0.0.1:8000/tasks/` |
| **Categories** | [https://taskflow-omega-ruddy-39.vercel.app/categories/](https://taskflow-omega-ruddy-39.vercel.app/categories/) | `http://127.0.0.1:8000/categories/` |
| **FAQs** | [https://taskflow-omega-ruddy-39.vercel.app/faqs/](https://taskflow-omega-ruddy-39.vercel.app/faqs/) | `http://127.0.0.1:8000/faqs/` |
| **Error Guide** | [https://taskflow-omega-ruddy-39.vercel.app/errors/](https://taskflow-omega-ruddy-39.vercel.app/errors/) | `http://127.0.0.1:8000/errors/` |
| **Support Hub** | [https://taskflow-omega-ruddy-39.vercel.app/support/](https://taskflow-omega-ruddy-39.vercel.app/support/) | `http://127.0.0.1:8000/support/` |
| **About Platform** | [https://taskflow-omega-ruddy-39.vercel.app/about/](https://taskflow-omega-ruddy-39.vercel.app/about/) | `http://127.0.0.1:8000/about/` |
| **System Health API** | [https://taskflow-omega-ruddy-39.vercel.app/health/](https://taskflow-omega-ruddy-39.vercel.app/health/) | `http://127.0.0.1:8000/health/` |
| **Django Admin** | [https://taskflow-omega-ruddy-39.vercel.app/admin/](https://taskflow-omega-ruddy-39.vercel.app/admin/) | `http://127.0.0.1:8000/admin/` |

---

## 📖 Table of Contents
1. [Live Demo](#-live-demo)
2. [Project Overview](#-project-overview)
3. [Actual Implemented Features](#-actual-implemented-features)
4. [Architecture & Technology Stack](#-architecture--technology-stack)
5. [Prerequisites](#-prerequisites)
6. [Windows Setup & Installation Instructions](#-windows-setup--installation-instructions)
7. [Environment Variables Configuration](#-environment-variables-configuration)
8. [Database Setup & Migrations](#-database-setup--migrations)
9. [Creating a Django Superuser](#-creating-a-django-superuser)
10. [Running the Development Server](#-running-the-development-server)
11. [Automated Testing & Health Checks](#-automated-testing--health-checks)
12. [Deploying to Vercel (Native Django Support)](#-deploying-to-vercel-native-django-support)
13. [Data Preservation Notice (Local SQLite)](#-data-preservation-notice-local-sqlite)
14. [Known Limitations & Future Improvement](#-known-limitations--future-improvement)
15. [License & Credits](#-license--credits)

---

## 🎯 Project Overview

**TaskFlow AI** is a full-stack web application combining productivity task management with an integrated developer support hub. It delivers a modern, dark glassmorphism dashboard (deep navy `#080D1A`, translucent glass panels with backdrop blur, electric blue `#38bdf8` accents), and integrates multi-database architecture:
- **Relational SQL Database (SQLite / PostgreSQL)**: Powers structured data including Tasks, FAQs, Error Code Guides, and Support Tickets.
- **Document NoSQL Database (MongoDB)**: Stores chat logs and user feedback ratings with graceful fail-soft fallback when unconfigured or offline.
- **Google Gemini AI Assistant**: Provides context-grounded assistance referencing verified database records with fallback handling.

---

## ✨ Actual Implemented Features

### 1. Task Management & Productivity
- **Dashboard (`/` or `/dashboard/`)**: Task metric cards (*Total Tasks*, *Completed*, *Pending*, *Overdue*), live Task Completion Progress bar, Daily Focus task highlight, Upcoming Deadlines (next 7 days), and a Quick Add Task form.
- **My Tasks (`/tasks/`)**: Complete CRUD task operations:
  - Add tasks with priority (*High*, *Medium*, *Low*), category (*Work*, *Study*, *Personal*, *Other*), due date, and estimated duration.
  - Interactive status toggling, in-place edit, and deletion.
  - Status filters (*All*, *Pending*, *Completed*, *Overdue*), real-time search by title, and sorting (by due date, priority, date added).
- **Categories (`/categories/`)**: Workstream grouping (*Work*, *Study*, *Personal*, *Other*) with individual completion progress bars and quick task entry per category.

### 2. Developer Support & Knowledge Base
- **FAQs (`/faqs/`)**: 12 verified questions and answers stored in SQL, categorized by Django, Python, Database, Web/HTTP, and Security, featuring category pills and search filtering.
- **Error Code Guide (`/errors/` & `/errors/<code>/`)**: Reference documentation for HTTP status codes (400, 401, 403, 404, 429, 500, 503) and application error codes (DEV001) with root causes, diagnostic pointers, and remediation code snippets.
- **Support Ticketing (`/support/`)**: SQL-persisted support tickets with honeypot anti-spam protection, CSRF validation, automated unique reference code generation (`TICK-XXXXXXXX`), and private reference status lookup.
- **About (`/about/`)**: Platform overview, architectural breakdown, technology stack, developer background, and support ticket submission form.

### 3. Database-Grounded AI Support Assistant
- **Shared Floating Widget**: Compact, dark glass chat assistant widget accessible across all application pages and custom error pages.
- **Context-Grounded Intelligence**: Queries verified SQL FAQ and Error Code records to answer technical inquiries without hallucinations.
- **Escalation Workflow**: Offers support ticket creation when uncertain, escalating only upon explicit user confirmation.
- **MongoDB Persistence**: Stores chat session logs and user feedback (thumbs up / thumbs down) in MongoDB with fail-soft offline handling.
- **Quick Prompts & Reset**: One-click prompt pills for common questions and conversation reset button.

### 4. Custom Error Handling & Health Monitoring
- **Custom Error Pages**: Styled 400, 403, 404, 429, 500, and 503 error pages maintaining full branding and assistant launcher.
- **Health Check (`/health/`)**: Diagnostic JSON endpoint checking SQL database connectivity, MongoDB connection status, and Gemini AI configuration.

---

## 🏗 Architecture & Technology Stack

- **Backend Framework**: Python 3.14, Django 6.0.6
- **Relational Database (SQL)**: SQLite locally (`db.sqlite3`), PostgreSQL support in production via `DATABASE_URL`
- **Document Database (NoSQL)**: MongoDB / MongoDB Atlas via `pymongo` 4.19 and `dnspython`
- **AI Integration**: Official Google GenAI Python SDK (`google-genai` 2.33+) using Gemini models
- **Frontend**: Semantic HTML5, Django Template Engine, Vanilla CSS (Dark Glassmorphic Design System), Vanilla JavaScript (zero heavy JS framework overhead)
- **Static Assets**: WhiteNoise for static file serving
- **Security**: Django CSRF protection, anti-spam honeypot inputs, finite timeouts on external API calls, secure credential separation

---

## 📋 Prerequisites

Before installing the project, ensure you have:
- **Python**: Version 3.10 to 3.14 installed ([python.org](https://www.python.org/downloads/)). Verify with `python --version`.
- **Git**: Version 2.x installed ([git-scm.com](https://git-scm.com/)). Verify with `git --version`.
- *(Optional)* **Google Gemini API Key**: Free API key from [Google AI Studio](https://aistudio.google.com/app/apikey).
- *(Optional)* **MongoDB Connection URI**: Free cluster on [MongoDB Atlas](https://www.mongodb.com/atlas) or a local MongoDB instance (`mongodb://localhost:27017/`).

---

## 💻 Windows Setup & Installation Instructions

Follow these step-by-step instructions in PowerShell or Windows Command Prompt:

### 1. Clone the Repository
```powershell
git clone https://github.com/mithra4325/TaskFlow-AI.git
cd TaskFlow-AI
```

### 2. Create and Activate a Virtual Environment
```powershell
# Create virtual environment
python -m venv venv

# Activate on Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Or activate on Windows (CMD)
.\venv\Scripts\activate.bat
```
*(If PowerShell displays an ExecutionPolicy error, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first).*

### 3. Install Dependencies
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🔑 Environment Variables Configuration

Copy the example configuration file to create your local `.env`:

```powershell
# In PowerShell:
Copy-Item .env.example .env

# Or in CMD:
copy .env.example .env
```

Open `.env` in your text editor and configure the variables:

```ini
# Google Gemini API key (from https://aistudio.google.com/app/apikey)
GEMINI_API_KEY=your_gemini_api_key_here

# MongoDB connection string (Optional - app gracefully handles offline MongoDB)
MONGODB_URI=your_mongodb_connection_string_here

# Django Secret Key & Debug Mode
SECRET_KEY=django-insecure-taskflow-ai-development-key-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,.onrender.com,.railway.app
```

> **Note**: Never commit your `.env` file to version control. It is strictly excluded by `.gitignore`.

---

## 🗄 Database Setup & Migrations

Because the local SQLite database (`db.sqlite3`) is excluded from version control to prevent data and credential exposure, initialize your database and seed initial knowledge base records on a fresh clone:

```powershell
# 1. Apply Django database schema migrations
python manage.py migrate

# 2. Seed initial FAQs and Error Code Knowledge Base records
python manage.py seed_devhelp
```

This will automatically populate the SQL database with 12 curated FAQs and 8 error code guides.

---

## 👤 Creating a Django Superuser

To access the Django Admin portal (`/admin/`):

```powershell
python manage.py createsuperuser
```

Follow the prompts to specify a username, email, and password.

---

## 🚀 Running the Development Server

Start the local Django development server:

```powershell
python manage.py runserver
```

### 🌐 Live Production Application
Access the deployed application on Vercel:
- **Website**: [https://taskflow-omega-ruddy-39.vercel.app](https://taskflow-omega-ruddy-39.vercel.app/)
- **Health Check**: [https://taskflow-omega-ruddy-39.vercel.app/health/](https://taskflow-omega-ruddy-39.vercel.app/health/)

### 💻 Local Development URLs
When running locally, navigate to:
- **Application Dashboard**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/) or [http://127.0.0.1:8000/dashboard/](http://127.0.0.1:8000/dashboard/)
- **My Tasks**: [http://127.0.0.1:8000/tasks/](http://127.0.0.1:8000/tasks/)
- **Categories**: [http://127.0.0.1:8000/categories/](http://127.0.0.1:8000/categories/)
- **FAQs**: [http://127.0.0.1:8000/faqs/](http://127.0.0.1:8000/faqs/)
- **Error Guide**: [http://127.0.0.1:8000/errors/](http://127.0.0.1:8000/errors/)
- **Support Hub**: [http://127.0.0.1:8000/support/](http://127.0.0.1:8000/support/)
- **About**: [http://127.0.0.1:8000/about/](http://127.0.0.1:8000/about/)
- **System Health**: [http://127.0.0.1:8000/health/](http://127.0.0.1:8000/health/)
- **Django Admin**: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## 🧪 Automated Testing & Health Checks

Run the automated test suite covering models, views, forms, ticket generation, Gemini fallback, security, and error pages:

```powershell
# Run all automated unit and integration tests
python manage.py test

# Run Django system integrity check
python manage.py check
```

You should see:
```text
Ran 27 tests in X.XXs
OK
System check identified no issues (0 silenced).
```

To verify health status programmatically:
```powershell
# Check live production deployment health
curl https://taskflow-omega-ruddy-39.vercel.app/health/

# Or check local development server health
curl http://127.0.0.1:8000/health/
```

---

## 🚀 Deploying to Vercel (Native Django Support)

TaskFlow AI is configured for Vercel's native Django framework support via `vercel.json` and WSGI entrypoint `myproject.wsgi:application`.

### 🌐 Live Production Deployment
- **Website**: [https://taskflow-omega-ruddy-39.vercel.app](https://taskflow-omega-ruddy-39.vercel.app/)
- **Health Check**: [https://taskflow-omega-ruddy-39.vercel.app/health/](https://taskflow-omega-ruddy-39.vercel.app/health/)
- **Status**: Live & Healthy (connected to PostgreSQL, MongoDB Atlas, and Gemini AI).

### Step 1: Provision a Persistent Production PostgreSQL Database
Because Vercel Functions run in a serverless, ephemeral, read-only environment, **do not use local SQLite in production**.
1. Create a free PostgreSQL database on [Neon.tech](https://neon.tech), [Supabase](https://supabase.com), or [Vercel Postgres](https://vercel.com/docs/storage/vercel-postgres).
2. Copy your pooled connection string (e.g., `postgresql://user:password@ep-xyz.neon.tech/neondb?sslmode=require`).

### Step 2: Migrate and Seed the Production Database (From Local Terminal)
Run migrations and populate the production database with **only the 12 FAQs and 8 error code guides** (your local tasks, users, and tickets are never copied):
```powershell
# Set the remote DATABASE_URL in your local session and apply schema
$env:DATABASE_URL="postgresql://user:password@host/dbname?sslmode=require"
python manage.py migrate

# Seed only the legitimate verified FAQs and Error Codes into production SQL
python manage.py seed_devhelp

# Clear the variable to return to local SQLite
$env:DATABASE_URL=""
```

### Step 3: Import Project into Vercel
1. Log in to your [Vercel Dashboard](https://vercel.com/dashboard) and click **Add New...** -> **Project**.
2. Select your GitHub repository: **`mithra4325/TaskFlow-AI`**.
3. Vercel automatically detects the **Django** framework preset. Keep Root Directory as `./`.
4. In **Environment Variables**, add:
   - `SECRET_KEY`: A secure random secret string (e.g. `django-insecure-taskflow-prod-key-...`).
   - `DEBUG`: `False`
   - `ALLOWED_HOSTS`: `.vercel.app`
   - `CSRF_TRUSTED_ORIGINS`: `https://*.vercel.app`
   - `DATABASE_URL`: Your production PostgreSQL connection string from Step 1.
   - `GEMINI_API_KEY`: Your Google Gemini API key.
   - `MONGODB_URI`: Your MongoDB Atlas connection URI (for chat logs and feedback).
5. Click **Deploy**. Vercel will install dependencies from `requirements.txt`, automatically collect static files to Vercel CDN, and serve your application.

---

## 🔒 Data Preservation Notice (Local SQLite)

- **Database Files Excluded**: In accordance with security and database best practices, local SQLite database files (`db.sqlite3`, `db.sqlite3-journal`, `*.backup`) are ignored by Git and **never uploaded to GitHub**.
- **Schema & Seeding Preserved**: The repository contains all Django schema migrations (`myapp/migrations/`) and the seeding management command (`seed_devhelp`), enabling any developer to reproduce the database in seconds.
- **Zero Data Loss on Host Machine**: The developer's local `db.sqlite3` remains untouched on the local filesystem.

---

## ⚠️ Known Limitations & Future Improvement

### Known Limitations
1. **MongoDB Atlas IP Whitelisting**: If connecting to a remote MongoDB Atlas cluster, the host's current public IP must be whitelisted in MongoDB Atlas **Network Access**. If the IP is absent, Atlas terminates the SSL handshake (`TLSV1_ALERT_INTERNAL_ERROR`). The application handles this gracefully without crashing, continuing in fail-soft mode.
2. **Gemini Free Tier Quotas**: Live Gemini requests depend on Google AI Studio API rate limits (15 requests per minute on free tier). When offline or unconfigured, the assistant defaults to verified SQL knowledge base records.

### Realistic Future Improvement
- **WebSocket-Based Real-Time Chat & Task Sync**: Transition the AI assistant and task board from HTTP polling/fetch requests to Django Channels with WebSockets, enabling real-time streaming tokens from Gemini and live multi-tab task synchronization.

---

## 📄 License & Credits

- Developed with Django, Google Gemini AI, and PyMongo.
- Icons by SVG Feather / Lucide.
- Typography: Inter by Google Fonts.
