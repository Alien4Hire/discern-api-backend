# Discern API – Backend

The **Discern API** powers the Discern spiritual assistant — an agentic AI platform that provides Bible-based, context-aware guidance using Retrieval-Augmented Generation (RAG), integrated subscriptions, and secure authentication.

---

## Features

- **Chatbot with Agentic AI**
  - Uses multi-agent AI to interpret user context and craft spiritually grounded responses.
  - Integrates **Elasticsearch** for RAG, enabling scripture-based answers with contextual retrieval.
  - Supports responses from multiple Bible translations.

- **Subscriptions & Payments**
  - Integrated with **Stripe** for secure subscription handling.
  - Endpoints for starting trials, subscribing, cancelling, and accessing the billing portal.
  - Webhook support for real-time subscription status updates.

- **Authentication**
  - **Google OAuth** and **Email/Password** authentication.
  - JWT-based session management.
  - User preferences, roles, and account management endpoints.

- **Database & Search**
  - **MongoDB** for user data, preferences, and subscription records.
  - **Elasticsearch** for scripture search and fast verse retrieval.

- **API Endpoints**
  - **Auth** – create account, sign in, get user data.
  - **User** – manage profile, preferences, and password.
  - **Agent** – send messages to AI.
  - **Subscription** – trial, subscribe, cancel, billing portal, webhook.
  - **Scripture** – search for verses.
  - **Health** – system health checks.

---

## Running with Docker Compose

Make sure Docker and Docker Compose are installed.  
From the project root, run:

```bash
docker compose up --build
```

This will start the following services:

- **Elasticsearch** – scripture search engine (port `9200`)
- **Kibana** – Elasticsearch UI (port `5601`)
- **MongoDB** – primary database (port `27017`)
- **API** – FastAPI backend (port `8000`)
- **Loader** – seeds Elasticsearch with Bible verse data

Once running, the API will be available at:

`http://localhost:8000`

OpenAPI/Swagger docs are at:

`http://localhost:8000/docs`

---

## Example API Flow

1. **Sign Up or Sign In** using `/auth/create-account` or `/auth/login`
2. **Send Messages** to AI via `/agent/send-message`
3. **Search Scripture** with `/scripture/search`
4. **Manage Subscription** using `/subscription` endpoints
5. **Update Preferences** via `/users/me/preferences`

---

## Tech Stack

- **FastAPI** – API framework
- **CrewAI** – Agent orchestration
- **Elasticsearch** – Retrieval-Augmented Generation (RAG)
- **MongoDB** – User and subscription storage
- **Stripe API** – Subscription billing
- **Docker Compose** – Container orchestration

---

## License

This project is proprietary and intended for internal use by the Discern team.
