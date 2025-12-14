


# ResPlanet
### Decentralized Research Collaboration Platform

![License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)
![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?logo=docker&logoColor=white&style=flat-square)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white&style=flat-square)
![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=next.js&logoColor=white&style=flat-square)


<br />

> **ResPlanet** is an open-source platform designed to modernize academic publishing. It combines the rigorous standards of research with the speed of social networking, featuring RAG-powered peer reviews, real-time collaboration rooms, and dynamic trending feeds.




---

## 🏗 System Architecture & RAG Pipeline

ResPlanet implements a **Retrieval-Augmented Generation (RAG)** architecture to ensure AI responses are grounded in the actual content of research papers, minimizing hallucinations and providing context-aware citations.

```mermaid
graph TD
    subgraph Client[" Client Layer"]
        NextJS[Next.js 14 UI]
        Store[Zustand State]
    end

    subgraph Server[" Server Layer"]
        FastAPI[FastAPI Controller]
        WS[WebSocket Manager]
    end

    subgraph RAG[" RAG Engine"]
        Ingest[PDF Processor]
        Embedder[Embedding Service]
        Retriever[Semantic Retriever]
    end

    subgraph Infra[" Infrastructure"]
        DB[(PostgreSQL + pgvector)]
        Gemini[Google Gemini LLM]
    end

    %% Client Interactions
    NextJS <-->|REST API| FastAPI
    NextJS <-->|Real-time WS| WS
    
    %% RAG Ingestion Flow
    FastAPI -- "1. Upload PDF" --> Ingest
    Ingest -- "2. Chunk Text" --> Embedder
    Embedder -- "3. Store Vectors" --> DB

    %% RAG Retrieval Flow
    WS -- "4. User Query" --> Retriever
    FastAPI -- "4. Peer Review Req" --> Retriever
    Retriever <-- "5. Vector Search" --> DB
    Retriever -- "6. Context + Prompt" --> Gemini
    Gemini -- "7. AI Response" --> FastAPI
````

### How the RAG Engine Works

1.  **Ingestion:** When a researcher uploads a PDF, the system parses the text and splits it into semantic chunks.
2.  **Embedding:** These chunks are converted into high-dimensional vectors using Google's embedding models and stored in **pgvector**.
3.  **Retrieval:** When a user asks a question via Chat or requests a Peer Review, the system performs a cosine similarity search to find the most relevant paper sections.
4.  **Generation:** The retrieved context is fed into **Gemini 1.5 Pro**, ensuring the AI's output is strictly based on the paper's content.

-----

## ⚡ Key Features

| Feature | Description |
| :--- | :--- |
| **RAG-Powered Reviewer** | Automated, citation-backed critique of papers. The AI analyzes specific vector chunks to generate summaries, identify methodology gaps, and offer a preliminary verdict (Accept/Reject). |
| **Context-Aware Chat** | Real-time collaboration rooms with an integrated **@bot**. By leveraging RAG, the bot acts as an expert on the specific paper being discussed, answering technical queries instantly. |
| **Smart PDF Parsing** | Seamless ingestion pipeline that automatically cleans, chunks, and vectorizes uploaded documents for immediate semantic search availability. |
| **Granular Access** | Project owners maintain full sovereignty over their intellectual property. A dedicated dashboard allows authors to **Accept** or **Reject** collaboration requests. |
| **Velocity Feed** | A dynamic trending algorithm that surfaces high-impact research based on real-time engagement metrics (view velocity, download rates). |

-----

## 🛠 Tech Stack

### Core Infrastructure

  * **Backend:** FastAPI (Python 3.11)
  * **Frontend:** Next.js 14 (App Router), Tailwind CSS
  * **Database:** PostgreSQL (Async) with `pgvector` extension

### AI & RAG Stack

  * **LLM:** Google Gemini 1.5 Flash / Pro
  * **Orchestration:** LangChain
  * **Embeddings:** Google Generative AI Embeddings
  * **Vector Store:** pgvector

### DevOps

  * **Containerization:** Docker & Docker Compose
  * **Authentication:** OAuth2 (Google) with JWT Session Management

-----


## 🚀 Getting Started

This project is configured for a hybrid development workflow: **Docker** manages the backend services (API + DB), while the **Frontend** runs locally for rapid iteration.

### Prerequisites

  * Docker & Docker Compose
  * Node.js 18+
  * Google Cloud API Key

### 1\. Backend Setup

Create a `.env` file in the `backend/` directory:

```env
DATABASE_URL=postgresql+asyncpg://resplanet:resplanet123@db:5432/resplanet_db
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_API_KEY=your_gemini_api_key
SECRET_KEY=super_secret_key
```

Launch the server and database:

```bash
cd backend
docker-compose up -d --build
```

> The API will be available at `http://localhost:8000`

### 2\. Frontend Setup

Install dependencies and start the client:

```bash
cd frontend
npm install
npm run dev
```

> The application will be live at `http://localhost:3000`

-----


## 📜 License

This project is licensed under the MIT License - see the `LICENSE` file for details
```
