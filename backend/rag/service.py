import os
from typing import Annotated, TypedDict, List
from langchain_google_vertexai import ChatVertexAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from ..vectorstore.manager import VectorStoreManager

# --- LANGGRAPH STATE ---
class ChatState(TypedDict):
    messages: Annotated[list, add_messages]

class RAGService:
    def __init__(self, project: str, location: str):
        self.project = project
        self.location = location
        self.vs_manager = VectorStoreManager(project, location)
        self.llm = ChatVertexAI(
            model_name="gemini-1.5-pro",
            project=project,
            location=location,
            temperature=0
        )

    def _get_chatbot(self, user_email: str):
        retriever = self.vs_manager.get_retriever(user_email)
        
        @tool
        def rag_tool(query: str) -> str:
            """
            Retrieves relevant information from your uploaded PDF documents.
            Use this tool whenever you need to answer questions based on the user's files.
            """
            if not retriever:
                return "No documents indexed for this user."
            
            docs = retriever.invoke(query)
            context = "\n\n".join([f"--- Document Excerpt ---\n{d.page_content}" for d in docs])
            return context

        tools = [rag_tool]
        tool_node = ToolNode(tools)
        llm_with_tools = self.llm.bind_tools(tools)

        def chat_node(state: ChatState):
            sys_msg = SystemMessage(content=(
                "You are SANDYLLM, a production-ready AI assistant powered by Google Gemini and Vertex AI. "
                "You have access to 'rag_tool' to search the user's private documents. "
                "Always use the tool if the question involves user data. "
                "If the tool returns no info, be honest and say it's not in the documents."
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
        
        return graph.compile()

    def query(self, user_email: str, message: str, history: List[dict]):
        chatbot = self._get_chatbot(user_email)
        
        msgs = []
        for m in history:
            if m["role"] == "user": msgs.append(HumanMessage(content=m["content"]))
            else: msgs.append(AIMessage(content=m["content"]))
        
        msgs.append(HumanMessage(content=message))
        
        result = chatbot.invoke({"messages": msgs})
        final_msg = result["messages"][-1]
        
        return final_msg.content
