from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableLambda
from agent.disease_analysis_agent.utils.states import (
    AgentState, InputState, OutputState
)
from agent.disease_analysis_agent.utils.configuration import Configuration
from agent.disease_analysis_agent.utils.nodes import (
    state_init,
    analyze_disease_risk,
    format_final_response
)
workflow = StateGraph(
    state_schema=AgentState,
    input=InputState,
    output=OutputState,
    config_schema=Configuration
)

# 注册节点
workflow.add_node("init", RunnableLambda(state_init))
workflow.add_node("analyze_disease_risk", RunnableLambda(analyze_disease_risk))
workflow.add_node("format_final_response", RunnableLambda(format_final_response))

# 设置执行顺序
workflow.set_entry_point("init")
workflow.add_edge("init", "analyze_disease_risk")
workflow.add_edge("analyze_disease_risk", "format_final_response")
workflow.add_edge("format_final_response", END)
graph = workflow.compile()
