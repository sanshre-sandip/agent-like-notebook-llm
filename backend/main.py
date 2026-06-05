import os
from typing import Annotated, TypedDict, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, BaseMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

# Load environment variables
load_dotenv()

app = FastAPI(title="RAG LangGraph API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- RAG Setup ---

# Initialize LLM
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY")
)

# Load and Index Documents
# We'll check for both PDFs mentioned in the directory
pdf_files = ["ra.pdf", "AI_Report_1000plus_Words.pdf"]
all_docs = []

for pdf in pdf_files:
    if os.path.exists(pdf):
        loader = PyPDFLoader(pdf)
        all_docs.extend(loader.load())

if not all_docs:
    print("Warning: No PDF files found for indexing.")
else:
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(all_docs)
    embeddings = HuggingFaceEmbeddings()
    vector_store = FAISS.from_documents(chunks, embeddings)
    retriever = vector_store.as_retriever(search_type='similarity', search_kwargs={'k': 2})

    @tool
    def rag_tool(query: str):
        """Search the vector database and return relevant documents."""
        result = retriever.invoke(query)
        context = [doc.page_content for doc in result]
        metadata = [doc.metadata for doc in result]
        return {
            "query": query,
            "context": context,
            "metadata": metadata
        }

    tools = [rag_tool]
    llm_with_tools = llm.bind_tools(tools)

    # --- LangGraph Setup ---

    class ChatState(TypedDict):
        messages: Annotated[list, add_messages]

    def chat_node(state: ChatState):
        messages = state.get("messages", [])
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    tool_node = ToolNode(tools)

    graph = StateGraph(ChatState)
    graph.add_node('chat_node', chat_node)
    graph.add_node('tools', tool_node)

    graph.add_edge(START, 'chat_node')
    graph.add_conditional_edges('chat_node', tools_condition)
    graph.add_edge('tools', 'chat_node')

    chatbot = graph.compile()

# --- API Endpoints ---

class ChatRequest(BaseModel):
    message: str
    history: List[dict] = []

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    if not all_docs:
        raise HTTPException(status_code=500, detail="No documents indexed.")
    
    try:
        # Convert history to LangChain messages
        messages = []
        for msg in request.history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))
        
        messages.append(HumanMessage(content=request.message))
        
        # Run chatbot
        result = chatbot.invoke({"messages": messages})
        
        # Get the last message
        last_message = result["messages"][-1]
        
        return {
            "response": last_message.content,
            "history": request.history + [
                {"role": "user", "content": request.message},
                {"role": "assistant", "content": last_message.content}
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
