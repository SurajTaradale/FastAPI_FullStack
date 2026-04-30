# HelpDesk App

An OTRS/OTOBO-inspired helpdesk application built with **FastAPI** (Python) and **ReactJS**. It supports two user types — **Agents** (staff) and **Customer Users** — each with separate authentication, dashboards, and JWT-secured API access.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Backend Setup](#2-backend-setup)
  - [3. Frontend Setup](#3-frontend-setup)
- [Environment Variables](#environment-variables)
  - [Backend (.env)](#backend-env)
  - [Frontend (.env)](#frontend-env)
- [Running the Application](#running-the-application)
  - [Start Backend](#start-backend)
  - [Start Frontend](#start-frontend)
- [API Reference](#api-reference)
  - [Auth Endpoints](#auth-endpoints)
  - [Agent User Endpoints](#agent-user-endpoints)
  - [Customer User Endpoints](#customer-user-endpoints)
- [Authentication Flow](#authentication-flow)
- [Database](#database)
- [Caching](#caching)
- [Contributing](#contributing)

---

## Overview

HelpDesk App provides:

- **Agent Portal** — Staff login, user management (create / edit / search agents), admin dashboard.
- **Customer Portal** — Customer user login, customer dashboard, support ticket access.
- **JWT Authentication** — Separate tokens for agents and customer users; `user_type` claim in token controls access.
- **Role-based Route Protection** — Frontend routes are guarded by user type; backend middleware validates every request.
- **Caching** — DiskCache or Redis for user and preferences data.

---

## Architecture

```
helpdesk_app/
├── itsm/
│   ├── backend/       ← FastAPI Python backend
│   └── frontend/      ← ReactJS frontend
```

```
Browser (React)
    │
    │  HTTP + Bearer JWT
    ▼
FastAPI (uvicorn :8001)
    │  AuthMiddleware validates token on every request
    │
    ├── /auth/token            → Agent login
    ├── /auth/customer/login   → Customer login
    ├── /api/v1/agent/...      → Agent-protected routes
    └── /api/v1/...            → System routes
    │
    ▼
MySQL Database (OTOBO schema)
    + DiskCache / Redis
```

---

## Project Structure

```
itsm/
├── backend/
│   ├── .env.example               ← Copy to .env and configure
│   └── app/
│       ├── main.py                ← FastAPI app entry point, CORS, routers
│       ├── requirements.txt
│       ├── api/v1/
│       │   ├── auth.py            ← /auth/token and /auth/customer/login
│       │   ├── user.py            ← Agent user CRUD endpoints
│       │   ├── customeruser.py    ← Customer user CRUD endpoints
│       │   └── system.py          ← Log viewer endpoint
│       ├── controller/
│       │   ├── user_controller.py
│       │   └── customeruser_controller.py
│       ├── middleware/
│       │   └── auth_middleware.py ← JWT validation on every request
│       ├── models/
│       │   ├── user.py
│       │   ├── user_preferences.py
│       │   ├── customeruser.py
│       │   ├── customer_preferences.py
│       │   ├── customer_company.py
│       │   └── valid.py
│       ├── schemas/
│       │   ├── user.py
│       │   └── customeruserSchema.py
│       ├── core/
│       │   ├── config.py          ← All settings (reads from .env)
│       │   ├── cache.py           ← Redis / DiskCache abstraction
│       │   └── logging.py
│       ├── db/
│       │   ├── base.py
│       │   └── session.py
│       └── utils.py               ← bcrypt hashing, password generator
│
└── frontend/
    ├── .env.example               ← Copy to .env and configure
    └── src/
        ├── App.js                 ← Route definitions
        ├── api/
        │   ├── agentapiClient.js      ← Axios client (agent token)
        │   └── customerapiClient.js   ← Axios client (customer token)
        ├── auth/
        │   ├── AgentAuth.js
        │   ├── CustomerAuth.js
        │   ├── PrivateRoute.js        ← Guards routes by user type + cookie
        │   └── PublicRoute.js
        ├── services/
        │   ├── AuthService.js         ← Login / logout API calls
        │   └── UserService.js
        ├── pages/
        │   ├── AgentLogin.js
        │   ├── CustomerLogin.js
        │   ├── AgentDashboard.js
        │   ├── CustomerDashboard.js
        │   └── user/
        │       ├── UserTable.js
        │       ├── UserCreateEdit.jsx
        │       └── UsersDialog.jsx
        ├── layout/
        │   ├── AgentLayout.js
        │   └── CustomerLayout.js
        └── store/                     ← Redux slices (agentSlice, customerSlice)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend framework | FastAPI (Python 3.9+) |
| ASGI server | Uvicorn |
| ORM | SQLAlchemy |
| Database | MySQL (OTOBO schema) |
| Password hashing | passlib + bcrypt |
| Auth tokens | python-jose (JWT / HS256) |
| Cache | DiskCache or Redis |
| Frontend framework | React 18 |
| State management | Redux Toolkit |
| HTTP client | Axios |
| UI components | MUI (Material UI v6) |
| Routing | React Router v6 |
| Auth cookies | js-cookie |

---

## Prerequisites

Make sure the following are installed on your system before starting:

| Tool | Minimum version |
|---|---|
| Python | 3.9+ |
| pip | 21+ |
| Node.js | 16+ |
| npm | 8+ |
| MySQL | 5.7+ / 8.0+ |
| Git | Any recent version |

> **Note:** The database uses the existing OTOBO MySQL schema. Tables `users`, `user_preferences`, `customer_user`, `customer_preferences`, `customer_company`, and `valid` must exist.

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/SurajTaradale/helpdesk_app.git
cd helpdesk_app
```

---

### 2. Backend Setup

**Step 1 — Go to the backend directory**

```bash
cd itsm/backend
```

**Step 2 — Create and activate a Python virtual environment**

```bash
python3 -m venv venv
source venv/bin/activate        # Linux / macOS
# venv\Scripts\activate         # Windows
```

**Step 3 — Install dependencies**

```bash
pip install -r app/requirements.txt
```

**Step 4 — Create your environment file**

```bash
cp .env.example .env
```

Then open `.env` and fill in your values (see [Environment Variables](#environment-variables) below).

**Step 5 — Verify the database connection**

Make sure MySQL is running and the OTOBO database is accessible with the credentials in your `.env`.

```bash
mysql -u <db_user> -p <db_name> -e "SHOW TABLES;"
```

You should see tables like `users`, `customer_user`, `customer_company`, `valid`.

---

### 3. Frontend Setup

**Step 1 — Go to the frontend directory**

```bash
cd itsm/frontend
```

**Step 2 — Install Node dependencies**

```bash
npm install
```

**Step 3 — Create your environment file**

```bash
cp .env.example .env
```

Then set `REACT_APP_API_URL` to point to your backend (see [Environment Variables](#environment-variables)).

---

## Environment Variables

### Backend (`itsm/backend/.env`)

```env
# ── JWT ────────────────────────────────────────────────────────────────────
# Generate a strong random key:  python3 -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=replace-with-a-long-random-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# ── Database ────────────────────────────────────────────────────────────────
DATABASE_URL=mysql+pymysql://db_user:db_password@localhost/db_name

# ── CORS ────────────────────────────────────────────────────────────────────
# Comma-separated list of allowed frontend origins
CORS_ORIGINS=http://localhost:3000,http://192.168.1.8:3000

# ── Cache ────────────────────────────────────────────────────────────────────
CACHE_TYPE=diskcache                          # or "redis"
DISKCACHE_DIR=/opt/helpdesk_app/itsm/cache   # path for diskcache
REDIS_URL=redis://localhost:6379/0            # used only when CACHE_TYPE=redis
```

> **How to generate a strong SECRET_KEY:**
> ```bash
> python3 -c "import secrets; print(secrets.token_hex(32))"
> ```

### Frontend (`itsm/frontend/.env`)

```env
# URL of your FastAPI backend (no trailing slash)
REACT_APP_API_URL=http://localhost:8001
```

---

## Running the Application

### Start Backend

```bash
cd itsm/backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

The API will be available at:
- **API base:** `http://localhost:8001`
- **Interactive docs (Swagger UI):** `http://localhost:8001/docs`
- **OpenAPI schema:** `http://localhost:8001/openapi.json`

### Start Frontend

```bash
cd itsm/frontend
npm start
```

The React app will open at `http://localhost:3000`.

Default routes:
- `http://localhost:3000/agent/login` — Agent login
- `http://localhost:3000/customer/login` — Customer login
- `http://localhost:3000/agent/dashboard` — Agent dashboard (protected)
- `http://localhost:3000/customer/dashboard` — Customer dashboard (protected)

---

## API Reference

All protected endpoints require the `Authorization: Bearer <token>` header.

### Auth Endpoints

| Method | URL | Description | Auth required |
|---|---|---|---|
| `POST` | `/auth/token` | Agent login — returns JWT with `user_type: agent` | No |
| `POST` | `/auth/customer/login` | Customer login — returns JWT with `user_type: customer` | No |
| `GET` | `/auth/me/` | Get current agent profile | Yes (agent) |

**Request body for both login endpoints** (`application/x-www-form-urlencoded`):
```
username=your_login&password=your_password
```

**Response:**
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "user_type": "agent"
}
```

---

### Agent User Endpoints

Base path: `/api/v1/agent` — all require agent JWT.

| Method | URL | Description |
|---|---|---|
| `POST` | `/users` | Create a new agent user |
| `GET` | `/user?id=1` | Get agent user by ID |
| `GET` | `/user?login=john` | Get agent user by login |
| `GET` | `/userslist?page_no=1&count_per_page=10` | Paginated list of agent users |
| `GET` | `/userssearch/?Search=john` | Search agents by name or login |
| `PUT` | `/users/{user_id}/` | Update an agent user |

**Create / Update agent user body:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "login": "john.doe",
  "email": "john@example.com",
  "password": "secret123",
  "mobile": "9876543210",
  "title": "Mr",
  "valid_id": 1
}
```

---

### Customer User Endpoints

Base path: `/api/v1/agent` — all require agent JWT.

| Method | URL | Description |
|---|---|---|
| `POST` | `/customeruser/` | Create a new customer user |
| `GET` | `/customeruser/?id=1` | Get customer user by ID |
| `GET` | `/customeruser/?login=jane` | Get customer user by login |
| `GET` | `/customeruserssearch/?Search=jane` | Search customer users |
| `PUT` | `/customeruser/{user_id}/` | Update a customer user |

**Create / Update customer user body:**
```json
{
  "first_name": "Jane",
  "last_name": "Smith",
  "login": "jane.smith",
  "email": "jane@company.com",
  "password": "secret123",
  "customer_id": "COMP001",
  "phone": "9876543210",
  "mobile": "9876543211",
  "fax": "",
  "street": "123 Main Street",
  "zip": "411001",
  "city": "Pune",
  "country": "India",
  "comments": "",
  "title": "Ms",
  "valid_id": 1
}
```

---

## Authentication Flow

```
Agent Login
──────────────────────────────────────────────
1. POST /auth/token  { username, password }
2. Backend verifies bcrypt hash from users table
3. Returns JWT:  { sub: "login", user_type: "agent" }
4. Frontend stores token in cookie: agent_token
5. Every subsequent request sends:
   Authorization: Bearer <agent_token>
6. AuthMiddleware decodes token → reads user_type=agent
   → loads user from DB → attaches to request.state.user


Customer Login
──────────────────────────────────────────────
1. POST /auth/customer/login  { username, password }
2. Backend verifies bcrypt hash from customer_user table
3. Returns JWT:  { sub: "login", user_type: "customer" }
4. Frontend stores token in cookie: customeruser_token
5. Every subsequent request sends:
   Authorization: Bearer <customeruser_token>
6. AuthMiddleware decodes token → reads user_type=customer
   → loads user from customer_user table
```

Token expiry is controlled by `ACCESS_TOKEN_EXPIRE_MINUTES` in `.env` (default: 60 minutes).

---

## Database

The app uses the **OTOBO MySQL schema**. Key tables:

| Table | Purpose |
|---|---|
| `users` | Agent / staff accounts |
| `user_preferences` | Agent email, mobile (stored as key-value, values in bytes) |
| `customer_user` | Customer user accounts |
| `customer_preferences` | Customer user preferences |
| `customer_company` | Customer company / organisation records |
| `valid` | Validity states (1 = valid, 2 = invalid, 3 = temporarily invalid) |

> **Password Migration (SHA256 → bcrypt):**
> Older versions of this app stored passwords as plain SHA256 hashes. The current version uses **bcrypt**. No manual migration is required — passwords are automatically re-hashed to bcrypt the next time each user logs in. Until a user logs in again, their old SHA256 hash continues to work transparently.

---

## Caching

User data and preferences are cached after first load to reduce DB queries.

| Setting | Value |
|---|---|
| `CACHE_TYPE=diskcache` | Uses local disk (default, no extra service needed) |
| `CACHE_TYPE=redis` | Uses Redis — set `REDIS_URL` in `.env` |
| Cache TTL | 3600 seconds (1 hour) |

Cache is automatically invalidated on user create or update.

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes and commit: `git commit -m "feat: describe your change"`
4. Push to your fork: `git push origin feature/your-feature-name`
5. Open a Pull Request against `main`

Please follow the existing code style and add comments for any non-obvious logic.
