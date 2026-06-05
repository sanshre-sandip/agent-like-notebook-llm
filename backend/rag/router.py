import os
import shutil
from typing import List
from fastapi import APIRouter, Request, HTTPException, UploadFile, File, Depends
from pydantic import BaseModel
from langchain_community.document_loaders import UnstructuredPDFLoader
from .service import RAGService

router = APIRouter(prefix="/rag", tags=["rag"])

# In-memory service (in production, use a singleton pattern or DI)
# We'll initialize it with dummy values initially, then real ones in main.py
rag_service: RAGService = None

def get_current_user(request: Request):
    user_email = request.session.get("user_email")
    if not user_email:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user_email

class ChatRequest(BaseModel):
    message: str
    history: List[dict] = []

@router.post("/chat")
async def chat(request: ChatRequest, user_email: str = Depends(get_current_user)):
    try:
        response = rag_service.query(user_email, request.message, request.history)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload")
async def upload(file: UploadFile = File(...), user_email: str = Depends(get_current_user)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF allowed")
    
    upload_dir = f"uploads/{user_email.replace('@', '_').replace('.', '_')}"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # Process and index
        loader = UnstructuredPDFLoader(file_path, strategy="hi_res")
        docs = loader.load()
        rag_service.vs_manager.add_documents(user_email, docs)
        return {"message": "File indexed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
