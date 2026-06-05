# RAG LangGraph React Application

This project is a full-stack RAG (Retrieval-Augmented Generation) application using LangGraph, Groq, FAISS, and React.

## Project Structure

- `backend/`: FastAPI application.
  - `main.py`: Main API logic, LangGraph workflow, and PDF indexing.
  - `requirements.txt`: Python dependencies.
- `frontend/`: React application (Vite + TypeScript).
  - `src/App.tsx`: Chat interface.
  - `src/App.css`: Styles.

## How to Run

### Backend
1. Ensure your `.env` file has the `GROQ_API_KEY`.
2. Use the existing virtual environment:
   ```bash
   ./ragg/bin/python backend/main.py
   ```
   The backend will start at `http://localhost:8000`.

### Frontend
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   The frontend will start at `http://localhost:5173`.

## Features
- **Document Indexing**: Automatically indexes `ra.pdf` and `AI_Report_1000plus_Words.pdf` on startup.
- **Agentic RAG**: Uses LangGraph to manage the conversation flow and tool usage.
- **Streaming-like UI**: Simple and responsive chat interface.
