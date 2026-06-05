import os
import shutil
import json
from typing import List
from fastapi import APIRouter, Request, HTTPException, UploadFile, File, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_core.messages import HumanMessage, AIMessage

from ..vectorstore.db import save_docs_for_user, get_retriever_for_user
from .gemini_chain import create_rag_chain

router = APIRouter(prefix="/rag", tags=["rag"])

def get_current_user(request: Request):
    if not request.session.get("is_authenticated"):
        raise HTTPException(status_code=401, detail="Authentication required")
    return request.session["user_id"]

class ChatRequest(BaseModel):
    message: str
    history: List[dict] = []

@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, user_id: str = Depends(get_current_user)):
    retriever = get_retriever_for_user(user_id)
    if not retriever:
        raise HTTPException(status_code=400, detail="No documents indexed. Please upload a PDF first.")
    
    chain = create_rag_chain(retriever)
    
    # Convert history dicts to LangChain messages
    history_messages = []
    for m in request.history:
        if m["role"] == "user":
            history_messages.append(HumanMessage(content=m["content"]))
        else:
            history_messages.append(AIMessage(content=m["content"]))

    async def generate():
        async for chunk in chain.astream({
            "question": request.message,
            "history": history_messages
        }):
            yield f"data: {json.dumps({'content': chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...), user_id: str = Depends(get_current_user)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDFs allowed")
    
    temp_path = f"storage/temp/{user_id}/{file.filename}"
    os.makedirs(os.path.dirname(temp_path), exist_ok=True)
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        loader = UnstructuredPDFLoader(temp_path, strategy="hi_res")
        docs = loader.load()
        save_docs_for_user(user_id, docs)
        return {"message": "Success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
