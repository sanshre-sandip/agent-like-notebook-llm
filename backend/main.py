import os
import shutil
from typing import Annotated, TypedDict, List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Core AI/RAG imports
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

# Advanced PDF Processing
from langchain_community.document_loaders import UnstructuredPDFLoader
import nltk

# NLTK requirements for unstructured
try:
    nltk.download('punkt')
    nltk.download('averaged_perceptron_tagger')
    nltk.download('punkt_tab')
    nltk.download('averaged_perceptron_tagger_eng')
except Exception as e:
    print(f"NLTK download warning: {e}")

load_dotenv()

app = FastAPI(title="SANDYLLM RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

embeddings = HuggingFaceEmbeddings()
vector_store = None
chatbot = None

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0
)

# --- RAG TOOL DEFINITION ---
@tool
def rag_tool(query: str) -> str:
    """
    Retrieves relevant information from uploaded PDF documents to answer user queries.
    Use this tool whenever the user asks about the content of their files, reports, or data.
    """
    global vector_store
    if vector_store is None:
        return "No documents have been uploaded or indexed yet. Please upload a PDF first."
    
    # Increase k for better coverage of complex documents
    docs = vector_store.as_retriever(search_kwargs={'k': 5}).invoke(query)
    
    if not docs:
        return "No relevant information found in the documents for this query."

    # Format the context clearly for the LLM
    context_parts = []
    for i, doc in enumerate(docs):
        source = doc.metadata.get('source', 'Unknown')
        content = doc.page_content.strip()
        context_parts.append(f"--- Document Excerpt {i+1} (Source: {source}) ---\n{content}")
    
    return "\n\n".join(context_parts)

tools = [rag_tool]
tool_node = ToolNode(tools)
llm_with_tools = llm.bind_tools(tools)

# --- LANGGRAPH SETUP ---
class ChatState(TypedDict):
    messages: Annotated[list, add_messages]

def chat_node(state: ChatState):
    # Ensure system prompt is present for agent behavior
    sys_msg = SystemMessage(content=(
        "You are SANDYLLM, a helpful AI research assistant. "
        "You have access to a RAG tool called 'rag_tool' which searches through the user's uploaded PDF documents. "
        "When a user asks a question about their files or data, ALWAYS use 'rag_tool' to find the answer. "
        "If the information is not in the documents, state that clearly."
    ))
    
    msgs = [sys_msg] + state["messages"]
    response = llm_with_tools.invoke(msgs)
    return {"messages": [response]}

graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_node("tools", tool_node)
graph.add_edge(START, "chat_node")
graph.add_conditional_edges("chat_node", tools_condition)
graph.add_edge("tools", "chat_node")
chatbot = graph.compile()

# --- PDF PROCESSING ---
def process_and_index_pdf(file_path: str):
    global vector_store
    
    # Try high-res (OCR + Table aware)
    # We set strategy="hi_res" and specify model_name to avoid repeated downloads if possible
    # We also ensure ocr_languages is set if needed (default is English)
    try:
        print(f"Processing {file_path} with hi_res strategy...")
        loader = UnstructuredPDFLoader(
            file_path,
            strategy="hi_res",
            infer_table_structure=True,
            chunking_strategy="by_title",
            max_characters=2000,
            overlap=200
        )
        docs = loader.load()
    except Exception as e:
        print(f"Hi-res failed for {file_path}, falling back to fast. Error: {e}")
        loader = UnstructuredPDFLoader(
            file_path,
            strategy="fast",
            chunking_strategy="by_title",
            max_characters=2000
        )
        docs = loader.load()
    
    if not docs:
        print(f"No text extracted from {file_path}")
        return

    if vector_store is None:
        vector_store = FAISS.from_documents(docs, embeddings)
    else:
        vector_store.add_documents(docs)

# Initial Indexing
for pdf in ["ra.pdf", "AI_Report_1000plus_Words.pdf"]:
    if os.path.exists(pdf):
        try: process_and_index_pdf(pdf)
        except Exception as e: print(f"Error indexing {pdf}: {e}")

# --- API ENDPOINTS ---
@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        process_and_index_pdf(file_path)
        return {"message": f"File {file.filename} indexed with OCR and layout support."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ChatRequest(BaseModel):
    message: str
    history: List[dict] = []

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        msgs = []
        for m in request.history:
            if m["role"] == "user": msgs.append(HumanMessage(content=m["content"]))
            else: msgs.append(AIMessage(content=m["content"]))
        
        msgs.append(HumanMessage(content=request.message))
        
        # Invoke LangGraph
        result = chatbot.invoke({"messages": msgs})
        final_msg = result["messages"][-1]
        
        return {
            "response": final_msg.content,
            "history": request.history + [
                {"role": "user", "content": request.message},
                {"role": "assistant", "content": final_msg.content}
            ]
        }
    except Exception as e:
        print(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
