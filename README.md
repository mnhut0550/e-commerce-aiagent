# 🛍️ E-commerce AI Agent System

## 🚀 Overview

A fullstack AI-powered e-commerce assistant that supports:

* Product consultation
* Context-aware reasoning
* Order processing

This project integrates a multi-agent architecture into a production-ready backend and a modern frontend interface.

> ⚠️ Note: The AI agent core logic is adapted from an existing system. This repository focuses on integration, orchestration, and deployment.

---

## 🧠 Key Highlights

* Multi-agent workflow (graph-based execution)
* Stateful conversation memory
* Modular node architecture (Router, Consultant, Order, Reasoning, Response)
* Async processing with task queue (Celery)
* Fullstack integration (API + UI)

---

## 🏗️ Tech Stack

### Backend

* Python (FastAPI-style architecture)
* Celery (background jobs)
* Redis (queue & caching)

### Frontend

* Next.js

### AI Layer

* LLM-based agent system
* Graph-based execution pipeline

---

## 📦 Project Structure

```id="r5r6p8"
backend/
  ├── agent/
  ├── routes/
  ├── services/
  ├── database/
  └── docker-compose.yml

store-frontend/
```

---

## ⚙️ Setup

### 1. Clone repository

```id="v1u5mk"
git clone <your-repo-url>
cd <project-folder>
```

---

### 2. Backend Setup

```id="7k2zfr"
cd backend
cp .env.example .env
docker-compose up --build
```

---

### 3. Frontend Setup

```id="7bnqg2"
cd store-frontend
npm install
npm run dev
```

---

## 🔐 Environment & Credentials

### 1. Environment Variables

Create `.env` from template:

```id="q2m6hw"
cp .env.example .env
```

Fill in required values such as:

* Database connection
* Redis URL
* API keys

---

### 2. Google Service Account (Required)

This project uses Google Cloud APIs (e.g., Sheets integration).

#### Step-by-step:

1. Go to Google Cloud Console
2. Create a Service Account
3. Generate a JSON key

Rename file to:

```id="c6n7tp"
service-account.json
```

Place it at:

```id="j3r8lk"
backend/backend/services/
```

---

### ⚠️ Security Rules (IMPORTANT)

* ❌ DO NOT commit `service-account.json`
* ❌ DO NOT commit `.env`
* ✅ Use `.gitignore` (already configured)
* ✅ Use `service-account.json.example` as reference

---

### 3. Recommended (Production-safe)

Use environment variable instead of storing file in repo:

```id="m9p2xz"
GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/service-account.json
```

---

### 4. Example Templates

* `.env.example` → environment config template
* `service-account.json.example` → service account structure template

---

## ✨ Features

* AI-powered product recommendation
* Intent routing via agent system
* Order processing pipeline
* Context-aware responses

---

## 📊 System Flow

```id="i3k9pl"
User → Frontend → Backend API → Agent System → Database / Redis → Response
```

---

## 📌 Credits

The AI agent core logic is derived from an existing system.
This project focuses on:

* System integration
* Backend orchestration
* Deployment architecture

---

## 📈 Future Improvements

* Observability (logging, tracing)
* Scalable deployment (Kubernetes)
* Memory optimization for agent system

---

## 🛡️ Security Notes

This project follows best practices:

* No secrets stored in repository
* Environment-based configuration
* External credential management
