import os
from typing import List
from langchain_google_vertexai import VertexAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

VECTOR_STORE_BASE_PATH = "vectorstore/users"

class VectorStoreManager:
    def __init__(self, project: str, location: str):
        self.embeddings = VertexAIEmbeddings(
            model_name="text-embedding-004",
            project=project,
            location=location
        )

    def _get_user_path(self, user_email: str):
        # Sanitize email for folder name
        safe_email = user_email.replace("@", "_").replace(".", "_")
        path = os.path.join(VECTOR_STORE_BASE_PATH, safe_email)
        os.makedirs(path, exist_ok=True)
        return path

    def add_documents(self, user_email: str, docs: List[Document]):
        user_path = self._get_user_path(user_email)
        index_path = os.path.join(user_path, "faiss_index")
        
        if os.path.exists(index_path):
            vector_store = FAISS.load_local(index_path, self.embeddings, allow_dangerous_deserialization=True)
            vector_store.add_documents(docs)
        else:
            vector_store = FAISS.from_documents(docs, self.embeddings)
        
        vector_store.save_local(index_path)

    def get_retriever(self, user_email: str, k: int = 5):
        user_path = self._get_user_path(user_email)
        index_path = os.path.join(user_path, "faiss_index")
        
        if not os.path.exists(index_path):
            return None
        
        vector_store = FAISS.load_local(index_path, self.embeddings, allow_dangerous_deserialization=True)
        return vector_store.as_retriever(search_kwargs={"k": k})
