# SANDYLLM - Production Vertex AI RAG

This is a production-ready RAG (Retrieval-Augmented Generation) application using **Google Vertex AI (Gemini 1.5 Pro)** and **Google OAuth**.

## 🚀 Key Upgrades
- **Authentication**: Fully integrated Google OAuth 2.0. Users are isolated based on their email.
- **Embeddings**: `text-embedding-004` (Vertex AI).
- **LLM**: `gemini-1.5-pro` (Vertex AI).
- **Architecture**: Modular structure for scalability and maintainability.
- **User Isolation**: Private vector stores and chat histories per user.

## 📁 Structure
- `/backend/auth`: OAuth login, callback, and session management.
- `/backend/rag`: Gemini orchestration and API endpoints.
- `/backend/vectorstore`: User-isolated FAISS indices.
- `/backend/main.py`: FastAPI entry point.

## 🛠️ Setup

### 1. Google Cloud Configuration
- Enable **Vertex AI API** in your GCP Console.
- Create **OAuth 2.0 Client ID** (Web application).
- Download `client_secret.json` and place it in the project root.
- Add `http://localhost:8000/auth/callback` to the **Authorized redirect URIs**.

### 2. Environment Variables (`.env`)
Ensure your `.env` contains:
```env
GCP_PROJECT_ID=your-project-id
GCP_LOCATION=us-central1
SESSION_SECRET_KEY=a-random-string-for-sessions
# GROQ_API_KEY is no longer required
```

### 3. Running the Backend
```bash
cd backend
pip install -r requirements.txt
python main.py
```

### 4. Running the Frontend
```bash
cd frontend
npm install
npm run dev
```

## 🧪 Flow
1. Visit `http://localhost:8000/auth/login` to authenticate.
2. After callback, you will be redirected to the React UI.
3. Upload PDFs in the UI (they will be processed with Vertex AI and stored in your private index).
4. Chat with SANDYLLM about your private sources.
