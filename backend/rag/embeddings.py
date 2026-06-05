from langchain_google_vertexai import VertexAIEmbeddings
from ..utils.config import settings

def get_embeddings():
    return VertexAIEmbeddings(
        model_name="text-embedding-004",
        project=settings.GCP_PROJECT_ID,
        location=settings.GCP_LOCATION
    )
