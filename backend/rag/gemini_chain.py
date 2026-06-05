from langchain_google_vertexai import ChatVertexAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from ..utils.config import settings

def get_gemini_model():
    return ChatVertexAI(
        model_name="gemini-1.5-pro",
        project=settings.GCP_PROJECT_ID,
        location=settings.GCP_LOCATION,
        streaming=True,
        temperature=0.2
    )

def create_rag_chain(retriever):
    llm = get_gemini_model()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are SANDYLLM, a senior research assistant. Use the following context to answer the user's question accurately. If the context doesn't contain the answer, say you don't know based on the provided files.\n\nContext:\n{context}"),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}"),
    ])
    
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    chain = (
        {
            "context": retriever | format_docs,
            "question": RunnablePassthrough(),
            "history": lambda x: x.get("history", [])
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain
