from typing import Optional

from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage, HumanMessage

from agent.common_utils.model_utils import get_model
from agent.disease_analysis_agent.utils.configuration import Configuration
from agent.disease_analysis_agent.utils.states import AgentState
from agent.disease_analysis_agent.utils.sturcts import AllergyCreate, DiseaseCreate, FoodRecordCreate, \
    DiseaseRiskAnalysis


def state_init(state: AgentState, config: RunnableConfig):
    # 初始化状态
    configurable = Configuration.from_runnable_config(config)
    initial_state = AgentState(
        allergen=state.get("allergen"),
        disease=state.get("disease"),
        foodrecord=state.get("foodrecord"),
        nutritiondetail=state.get("nutritiondetail"),

        disease_analysis=None,
        conversation_history=[],
        current_step="starting",
        error_message=None,

        vision_model=get_model(
            model_provider=configurable.vision_model_provider,
            model_name=configurable.vision_model
        ),

        analysis_model=get_model(
            model_provider=configurable.analysis_model_provider,
            model_name=configurable.analysis_model
        )
    )

    return initial_state


def analyze_disease_risk(state: AgentState) -> AgentState:
    """第二步：疾病相关成分预警分析"""
    try:
        # 必要字段校验
        if not state.get("disease") or not state.get("nutritiondetail"):
            state["error_message"] = "缺少疾病信息或营养数据"
            return state

        disease = state["disease"]
        nutrition = state["nutritiondetail"]
        allergen = state.get("allergen", None)

        # 构造提示词
        prompt = f"""
你是一位医学营养专家，请根据以下疾病、过敏原和摄入的营养信息，进行健康风险分析：

【疾病信息】
- 疾病名称: {disease.get("disease_name")}
- 严重程度: {disease.get("severity_level")}

【营养摄入】
- 总热量: {nutrition.get("total_calories")} 大卡
- 碳水化合物: {nutrition.get("carbohydrates")} 克
- 脂肪: {nutrition.get("fat")} 克
- 蛋白质: {nutrition.get("protein")} 克
- 胆固醇: {nutrition.get("cholesterol")} 毫克
- 钠: {nutrition.get("sodium")} 毫克
- 糖: {nutrition.get("sugar")} 克

{f"【过敏原】\n- {allergen.get('allergen_name')}" if allergen else ""}

请你详细分析该饮食对疾病的影响，包括：
1. 哪些营养成分不利于该疾病或过敏原；
2. 每种成分的危害解释；
3. 应避免的食物；
4. 健康饮食建议。

请使用以下JSON结构返回：
```json
{{
  "disease": "...",
  "risky_nutrients": ["..."],
  "risk_explanations": ["..."],
  "avoid_foods": ["..."],
  "health_tips": ["..."],
  "allergen": ["..."]
}}
"""
        # 调用分析模型并结构化输出
        model = state["analysis_model"].with_structured_output(DiseaseRiskAnalysis)
        result = model.invoke(prompt)

        # 保存分析结果
        state["disease_analysis"] = result
        state["current_step"] = "disease_risk_analyzed"

    except Exception as e:
        state["error_message"] = f"疾病风险分析失败: {str(e)}"

    return state


def format_final_response(state: AgentState) -> AgentState:
    """第三步：格式化疾病风险分析的最终响应文本"""
    try:
        if state.get("error_message"):
            return state  # 如果之前节点出错，直接跳过

        result = state.get("disease_analysis")
        if not result:
            state["error_message"] = "缺少疾病分析结果"
            return state

        # 格式化结构化结果
        formatted = (
            f"【疾病名称】\n{result.disease}\n"
            f"【需要注意的营养成分】\n{', '.join(result.risky_nutrients)}\n"
            f"【风险说明】\n- " + "\n- ".join(result.risk_explanations) + "\n"
            f"【建议避免食物】\n- " + "\n- ".join(result.avoid_foods) + "\n"
            f"【健康饮食建议】\n- " + "\n- ".join(result.health_tips)
        )

        state["formatted_output"] = formatted
        state["current_step"] = "completed"

    except Exception as e:
        state["error_message"] = f"格式化响应失败: {str(e)}"

    return state
