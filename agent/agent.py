from langgraph.graph import StateGraph, END

from agent.utils.configuration import Configuration
from agent.utils.nodes import *
from agent.utils.states import AgentState, InputState

workflow = StateGraph(
    state_schema=AgentState,
    config_schema=Configuration,
    input=InputState
)
workflow.add_node("state_init", state_init)
# 添加节点
workflow.add_node("analyze_image", analyze_image)
workflow.add_node("extract_nutrition", extract_nutrition_info)
workflow.add_node("generate_advice", generate_nutrition_advice)
workflow.add_node("format_response", format_final_response)
# 定义工作流
workflow.set_entry_point("state_init")
workflow.add_edge("state_init", "analyze_image")
workflow.add_edge("analyze_image", "extract_nutrition")
workflow.add_edge("extract_nutrition", "generate_advice")
workflow.add_edge("generate_advice", "format_response")
workflow.add_edge("format_response", END)
graph = workflow.compile()
