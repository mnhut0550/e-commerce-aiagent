# 🏗️ System Architecture

## High-Level Flow

```
User
 ↓
Frontend (Next.js)
 ↓
Backend API
 ↓
Agent System (Graph Execution)
 ↓
Database / Redis / External Services
 ↓
Response → Frontend
```

---

## Components

### 1. Frontend

* User interface for interaction
* Sends requests to backend API

---

### 2. Backend API

* Entry point for all requests
* Handles routing and validation
* Triggers agent execution

---

### 3. Agent System

* Core intelligence layer
* Executes node-based workflow
* Maintains state across steps

---

### 4. Task Queue (Celery)

* Handles asynchronous processing
* Improves scalability

---

### 5. Redis

* Queue broker
* Caching layer

---

### 6. Database

* Stores products, orders, logs

---

## Data Flow

1. User sends request from frontend
2. Backend receives and validates input
3. Router node determines intent
4. Relevant nodes process request
5. Response node formats output
6. Result returned to frontend

---

## Design Principles

* Modular architecture
* Separation of concerns
* Scalable processing via async tasks
* Extensible agent pipeline

---

## Deployment Considerations

* Containerized backend (Docker)
* Environment-based configuration
* Secret management via `.env`

---

## Limitations

* Agent logic is not fully owned in this repository
* Limited observability (can be improved with tracing/logging)
