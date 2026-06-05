import os
from typing import List
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from .embeddings import get_embeddings

VECTOR_ROOT = "storage/vectorstore"

def get_user_db_path(user_id: str):
    safe_id = user_id.replace("@", "_").replace(".", "_")
    path = os.path.join(VECTOR_ROOT, safe_id)
    os.makedirs(path, exist_ok=True)
    return path

def save_docs_for_user(user_id: str, docs: List[Document]):
    db_path = get_user_db_path(user_id)
    embeddings = get_embeddings()
    
    index_file = os.path.join(db_path, "index.faiss")
    if os.path.exists(index_file):
        vectorstore = FAISS.load_local(db_path, embeddings, allow_dangerous_deserialization=True)
        vectorstore.add_documents(docs)
    else:
        vectorstore = FAISS.from_documents(docs, embeddings)
    
    vectorstore.save_local(db_path)

def get_retriever_for_user(user_id: str, k: int = 5):
    db_path = get_user_db_path(user_id)
    index_file = os.path.join(db_path, "index.faiss")
    
    if not os.path.exists(index_file):
        return None
    
    embeddings = get_embeddings()
    vectorstore = FAISS.load_local(db_path, embeddings, allow_dangerous_deserialization=True)
    return vectorstore.as_retriever(search_kwargs={"k": k})
