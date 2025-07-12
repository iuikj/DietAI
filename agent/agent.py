from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition
from agent.utils.configuration import Configuration
from agent.utils.nodes import *
from agent.utils.states import AgentState, InputState, OutputState

workflow = StateGraph(
    state_schema=AgentState,
    config_schema=Configuration,
    input_schema=InputState,
    output_schema=OutputState
)

workflow.add_node("state_init", state_init)
# 添加节点
workflow.add_node("analyze_image", analyze_image)
workflow.add_node("extract_nutrition", extract_nutrition_info)
workflow.add_node("retrieve_nutrition_knowledge", retrieve_nutrition_knowledge)
workflow.add_node("generate_advice", generate_nutrition_advice)
workflow.add_node("format_response", format_final_response)
workflow.add_node("generate_dependencies", generate_dependencies)

# 定义工作流
workflow.set_entry_point("state_init")
workflow.add_edge("state_init", "analyze_image")
workflow.add_edge("analyze_image", "extract_nutrition")
workflow.add_edge("extract_nutrition", "retrieve_nutrition_knowledge")
workflow.add_edge("retrieve_nutrition_knowledge", "generate_dependencies")
workflow.add_edge("generate_dependencies", "generate_advice")
workflow.add_edge("generate_advice", "format_response")
workflow.add_edge("format_response", END)
graph = workflow.compile()
