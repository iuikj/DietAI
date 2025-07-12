from langgraph.graph import StateGraph, END

from agent.utils.configuration import Configuration
from agent.utils.chat_nodes import *
from agent.utils.chat_states import ChatState, ChatInputState

# 创建聊天机器人工作流
chat_workflow = StateGraph(
    state_schema=ChatState,
    config_schema=Configuration,
    input=ChatInputState
)

# 添加节点
chat_workflow.add_node("initialize_chat", initialize_chat_session)
chat_workflow.add_node("analyze_context", analyze_conversation_context)
chat_workflow.add_node("generate_response", generate_chat_response)
chat_workflow.add_node("format_chat_response", format_chat_response)

# 定义工作流
chat_workflow.set_entry_point("initialize_chat")
chat_workflow.add_edge("initialize_chat", "analyze_context")
chat_workflow.add_edge("analyze_context", "generate_response")
chat_workflow.add_edge("generate_response", "format_chat_response")
chat_workflow.add_edge("format_chat_response", END)

# 编译图
chat_graph = chat_workflow.compile()