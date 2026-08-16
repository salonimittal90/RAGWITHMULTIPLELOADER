from langgraph.graph import StateGraph, START, MessagesState, END
from langchain_core.documents import Document
from typing_extensions import List
from langchain_core.tools import tool
from config import vector_store, llm, aclient
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import ToolNode, tools_condition


import os
from repos.checkpointer import async_memory

class State(MessagesState):
    context: List[Document]
    trace_id: str = None

@tool(response_format="content_and_artifact")
def retrieve(query: str):
    """Retrieve information related to a query."""
    retrieved_docs = vector_store.similarity_search(query, k=4) 
    serialized = "\n\n".join(
        f"Source: {doc.metadata}\nContent: {doc.page_content}"
        for doc in retrieved_docs
    )
    return serialized, retrieved_docs


def query_or_respond(state: State):
    llm_with_tools = llm.bind_tools([retrieve])
    system_message_content = (
        "You are an AI assistant for question-answering tasks. "
        "Use the provided tool for retrieval from knowledge base. "
        "Don't answer out of the knowledge base and if you don't know simply say that provided documents don't have the info. "
        "You must use the retrieve tool whenever user queries. You should never answer from general knowledge that isn't grounded in search results."
    )
    conversation_messages = [
        message
        for message in state["messages"]
        if message.type in ("human", "system")
        or (message.type == "ai" and not message.tool_calls)
    ]
    prompt = [SystemMessage(system_message_content)] + conversation_messages
    response = llm_with_tools.invoke(prompt)
    return {"messages": [response]}

tools = ToolNode([retrieve])

def generate(state: State):
    recent_tool_messages = []
    for message in reversed(state["messages"]):
        if message.type == "tool":
            recent_tool_messages.append(message)
        else:
            break
    tool_messages = recent_tool_messages[::-1]

    docs_content = "\n\n".join(doc.content for doc in tool_messages)
    system_message_content = (
        "You are an AI assistant for question-answering tasks. "
        "Use the provided tool for retrieval from knowledge base. "
        "Don't answer out of the knowledge base and if you don't know simply say that provided documents don't have the info. "
        "You must use the retrieve tool whenever user queries. You should never answer from general knowledge that isn't grounded in search results."
        f"{docs_content}"
    )
    conversation_messages = [
        message
        for message in state["messages"]
        if message.type in ("human", "system")
        or (message.type == "ai" and not message.tool_calls)
    ]
    prompt = [SystemMessage(system_message_content)] + conversation_messages
    response = llm.invoke(prompt)

    context = []
    for tool_message in tool_messages:
        if tool_message.artifact:
            context.extend(tool_message.artifact)
    return {"messages": [response], "context": context}

graph_builder = StateGraph(State)

graph_builder.add_node(query_or_respond)
graph_builder.add_node(tools)
graph_builder.add_node(generate)

graph_builder.set_entry_point("query_or_respond")
graph_builder.add_conditional_edges(
    "query_or_respond",
    tools_condition,
    {END: END, "tools": "tools"},
)
graph_builder.add_edge("tools", "generate")
graph_builder.add_edge("generate", END)

async_graph = graph_builder.compile(checkpointer=async_memory)