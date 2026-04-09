# AI Project Setup and Run Guide

## Overview

This document provides step-by-step instructions to run the backend, AI service, and frontend for the project.

---

## Prerequisites

Make sure the following are installed on your system:

* Python (3.10 or above)
* Virtual Environment (venv)
* Ollama (for running LLM models like LLaMA3)
* Required Python dependencies (installed via `requirements.txt`)

---

## Project Structure

```
workbench/
│
├── app/
│   ├── main.py                # Entry point
│   ├── core/                 # Config & settings
│   │   ├── config.py
│   │   ├── security.py
│   │
│   ├── api/                  # Routes
│   │   ├── deps.py
│   │   ├── v1/
│   │   │   ├── api.py
│   │   │   ├── endpoints/
│   │   │   │   ├── user.py
│   │   │   │   ├── auth.py
│   │   │   │  
│   │
│   ├── models/               # DB models (SQLAlchemy)
│   │   ├── user.py
│   │   
│   │
│   ├── schemas/              # Pydantic schemas
│   │   ├── user.py
│   │   
│   │
│   ├── services/             # Business logic
│   │   ├── user_service.py
│   │   ├── interview_service.py
│   │   ├── llm_service.py
│   │
│   ├── db/                   # Database
│   │   ├── base.py
│   │   ├── session.py
│   │   ├── init_db.py
│   │
│   ├── utils/                # Helper functions
│   │   ├── parser.py
│   │   ├── logger.py
│
├── tests/                   # Test cases
│
├── .env
├── requirements.txt
├── Dockerfile
├── README.md   give me structure complete command
```

---

## Setup Instructions

### 1. Activate Virtual Environment

```
env/Scripts/activate
```

This activates the virtual environment so that project dependencies are used.

---

### 2. Start FastAPI Backend

```
uvicorn app.main:app --reload
```

* Starts the backend server
* Runs on: http://127.0.0.1:8000
* Auto-reloads on code changes

---

### 3. Start Ollama (LLM Service)

```
ollama run start
```

* Starts the local AI model service
* Required for chatbot or AI-based responses

Note: Ensure Ollama is properly installed and configured.

---

### 4. Navigate to Frontend Directory

```
cd frontend
```

---

### 5. Run Frontend Server

```
python server.py
```

* Starts the frontend application
* Typically runs on: http://localhost:5000

---

## Execution Flow

Follow this order strictly:

1. Activate virtual environment
2. Start FastAPI backend
3. Start Ollama service
4. Run frontend server
5. Open browser and access the application

---

## Troubleshooting

### Backend not starting

* Check if dependencies are installed:

  ```
  pip install -r requirements.txt
  ```

### Ollama timeout error

* Ensure Ollama is running before sending requests
* Check if model is downloaded:

  ```
  ollama run llama3
  ```

### Frontend not loading

* Verify backend is running
* Check correct API URL in frontend code

---

## Notes

* Always start backend before frontend
* Keep `.env` properly configured
* Ensure ports are not already in use

---


