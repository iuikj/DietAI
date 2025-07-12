from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableLambda

from agent.disease_analysis_agent.utils.configuration import Configuration
from agent.disease_analysis_agent.utils.nodes import state_init, extract_disease_allergy_info, analyze_disease_risk, format_final_response
from agent.disease_analysis_agent.utils.states import AgentState, InputState, OutputState

workflow = StateGraph(
        state_schema=AgentState,
        input_schema=InputState,
        output_schema=OutputState,
        config_schema=Configuration
    )
workflow.add_node("init", RunnableLambda(state_init))
workflow.add_node("extract_disease_allergy_info", RunnableLambda(extract_disease_allergy_info))
workflow.add_node("analyze_disease_risk", RunnableLambda(analyze_disease_risk))
workflow.add_node("format_final_response", RunnableLambda(format_final_response))

workflow.set_entry_point("init")
workflow.add_edge("init", "extract_disease_allergy_info")
# 判断user_input是否存在，决定流程走向
workflow.add_conditional_edges(
    "extract_disease_allergy_info",
    lambda state: END if state.get("user_input") else "analyze_disease_risk"
)
workflow.add_edge("analyze_disease_risk", "format_final_response")
workflow.add_edge("format_final_response", END)

graph=workflow.compile()