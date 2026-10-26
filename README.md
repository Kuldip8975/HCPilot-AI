# HCPilot AI

<img width="747" height="333" alt="firlsd" src="https://github.com/user-attachments/assets/52708b90-5dc7-445e-8b16-ccb84e80bd1a" />


**AI-powered CRM for pharmaceutical sales representatives** — helping reps prioritize healthcare provider (HCP) visits, log interactions, and get AI-driven insights, all in one place.

🔗 **Live Demo:** https://hcpilot-frontend.pages.dev

---

## Overview

HCPilot AI helps pharma sales reps manage their relationships with doctors and healthcare providers more effectively. Instead of manually tracking who to visit and when, the app uses AI to analyze past interactions and surface who needs attention this week — with a clear, explainable reason for each recommendation.

## Key Features

- **AI Priority Dashboard** — Ranks HCPs by urgency using engagement scores, follow-up status, and interaction history, with AI-generated reasoning for each priority
- **Smart Day Planning** — Suggests an optimal visit route based on priorities and real travel time (map integration via Leaflet)
- **AI Chat Assistant** — Conversational interface to log interactions, search records, and answer questions using LangChain + Groq LLM
- **Smart Search (RAG)** — Ask natural-language questions grounded only in your own logged interaction history
- **Interaction Logging** — Manual and AI-assisted logging of HCP visits/calls
- **Role-based Dashboards** — Separate views for Sales Reps and Doctors
- **Analytics & Activity Log** — Track engagement trends and team activity over time

## Tech Stack

**Frontend**
- React 18 + Vite
- Redux Toolkit (state management)
- React Router, React Hook Form + Yup (validation)
- Leaflet (maps)

**Backend**
- FastAPI (async Python web framework)
- SQLAlchemy (async ORM) + PostgreSQL
- LangChain + LangGraph + Groq (LLM orchestration)
- Alembic (database migrations)
- JWT authentication, rate limiting (slowapi)

**Infrastructure & DevOps**
- **Frontend hosting:** Cloudflare Pages
- **Backend hosting:** AWS EC2 (Docker + Docker Compose)
- **Database:** AWS RDS (PostgreSQL)
- **Infrastructure as Code:** Terraform (EC2, RDS, Security Groups, networking)
- **Reverse proxy + SSL:** nginx + Let's Encrypt (Certbot)
- **Containerization:** Docker

## Architecture

┌─────────────────┐ ┌──────────────────────────────────┐
│ Cloudflare │ HTTPS │ AWS EC2 │
│ Pages │ ──────► │ ┌────────┐ ┌─────────────┐ │
│ (React/Vite) │ │ │ nginx │──►│ FastAPI │ │
│ │ │ │ (SSL) │ │ (Docker) │ │
└─────────────────┘ │ └────────┘ └──────┬──────┘ │
└──────────────────────┼───────────┘
│
┌────────▼────────┐
│ AWS RDS │
│ (PostgreSQL) │
└──────────────────┘


## Local Development Setup

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
cp .env.example .env           # fill in your own values
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env           # fill in your own values
npm run dev
```

## Deployment

- Backend is containerized with Docker and deployed to an AWS EC2 instance provisioned via Terraform. nginx handles TLS termination with a Let's Encrypt certificate.
- Frontend is built with Vite and deployed to Cloudflare Pages via Wrangler CLI.
- Infrastructure (EC2, RDS, security groups) is fully defined as code in the `terraform/` directory for reproducible provisioning.

## Project Structure

.
├── backend/ # FastAPI application
│ ├── app/
│ │ ├── api/ # Route handlers
│ │ ├── models/ # SQLAlchemy models
│ │ ├── services/ # Business logic
│ │ ├── schemas/ # Pydantic schemas
│ │ └── mcp/ # MCP server integration
│ └── migrations/ # Alembic migrations
├── frontend/ # React + Vite application
│ └── src/
│ ├── pages/ # Route-level pages
│ ├── components/ # Reusable UI components
│ ├── redux/ # State management
│ └── services/ # API client layer
└── terraform/ # AWS infrastructure as code


## License

This project is for portfolio/demonstration purposes.
