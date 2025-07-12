import asyncio
from langgraph.graph import StateGraph
from agent.disease_analysis_agent.utils.states import AgentState, InputState, OutputState
from agent.disease_analysis_agent.utils.configuration import Configuration
from agent.disease_analysis_agent.utils.nodes import state_init, analyze_disease_risk, format_final_response
from langchain_openai import ChatOpenAI

async def run_graph():
    # 构建 Graph
    builder = StateGraph(state_schema=AgentState)

    builder.add_node("state_init", state_init)
    builder.add_node("disease_analysis", analyze_disease_risk)
    builder.add_node("format_response", format_final_response)

    builder.set_entry_point("state_init")
    builder.add_edge("state_init", "disease_analysis")
    builder.add_edge("disease_analysis", "format_response")
    builder.set_finish_point("format_response")

    graph = builder.compile()

    # 示例输入
    input_state: InputState = {
        "foodrecord": {
            "record_date": "2025-07-06",
            "meals": [
                {"meal_type": "早餐", "foods": ["煎鸡蛋", "豆浆", "全麦吐司"]},
                {"meal_type": "午餐", "foods": ["米饭", "红烧牛肉", "西兰花", "胡萝卜"]}
            ]
        },
        "disease": {
            "disease_code": "I10",
            "disease_name": "高血压",
            "severity_level": 2,
            "diagnosed_date": "2023-01-15",
            "notes": "需控制钠摄入，避免血压波动"
        },
        "allergen": {
            "allergen_name": "花生",
            "severity_level": 2
        },
        "nutritiondetail": {
            "total_calories": 2000,
            "macronutrients": {
                "protein": 80,
                "fat": 70,
                "carbohydrates": 240
            },
            "micronutrients": {
                "vitamin_c": 100,
                "calcium": 500,
                "iron": 18
            }
        }
    }

    # 构造配置
    config = Configuration(
        vision_model_provider="openai",
        vision_model="gpt-4o",
        analysis_model_provider="openai",
        analysis_model="gpt-4o"
    )

    # 执行 graph
    result = await graph.ainvoke(input_state, config=config.__dict__)
    print("\n=== 最终结果 ===")
    print(result["formatted_output"])

# 运行
if __name__ == "__main__":
    asyncio.run(run_graph())
