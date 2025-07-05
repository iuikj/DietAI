from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_qwq import ChatQwen

from agent.common_utils.image_utils import encode_image_to_base64
from agent.utils.configuration import Configuration
from agent.utils.states import AgentState
from agent.utils.sturcts import NutritionAnalysis, NutritionAdvice
from agent.common_utils.model_utils import get_model


def state_init(state: AgentState, config: RunnableConfig):
    configurable = Configuration.from_runnable_config(config)
    if state.get("image_dir") is None:
        initial_state = AgentState(
            image_data=state['image_data'],
            image_analysis=None,
            nutrition_analysis=None,
            nutrition_advice=None,
            user_preferences={},  # 后续要添加
            conversation_history=[],
            current_step="starting",
            error_message=None,
            vision_model=get_model(model_provider=configurable.vision_model_provider,
                                   model_name=configurable.vision_model),
            analysis_model=get_model(model_provider=configurable.analysis_model_provider,
                                     model_name=configurable.analysis_model)
        )
        return initial_state
    image_data = encode_image_to_base64(str(state['image_dir']))
    print(configurable.analysis_model)
    print(configurable.vision_model)
    initial_state = AgentState(
        image_data=image_data,
        image_analysis=None,
        nutrition_analysis=None,
        nutrition_advice=None,
        user_preferences={},  #后续要添加
        conversation_history=[],
        current_step="starting",
        error_message=None,
        vision_model=get_model(model_provider=configurable.vision_model_provider, model_name=configurable.vision_model),
        analysis_model=get_model(model_provider=configurable.analysis_model_provider,
                                 model_name=configurable.analysis_model)
    )
    return initial_state


def analyze_image(state: AgentState) -> AgentState:
    """第一步：分析图片中的食物"""
    try:
        if not state.get("image_data"):
            state["error_message"] = "未提供图片数据"
            return state

        # if not state.get("image_dir"):
        #     state["error_message"] = "未提供图片数据"
        #     return state

        messages = [
            SystemMessage(content="""你是一位专业的营养师，擅长识别和分析食物图片。
            请详细描述图片中的所有食物，包括：
            1. 具体的食物名称和种类
            2. 估计的分量和重量
            3. 烹饪方式（煎、炒、蒸、煮等）
            4. 食物的新鲜程度和外观
            5. 可能的调料和配菜
            请用中文回答，尽可能详细和准确。"""),

            HumanMessage(content=[
                {
                    "type": "text",
                    "text": "请分析这张食物图片，详细描述其中的所有食物项目："
                },
                {
                    "type": "image",
                    "source_type": "base64",
                    "data": state["image_data"],
                    "mime_type": "image/jpeg"
                }
            ])
        ]

        response = state['vision_model'].invoke(messages)
        state["image_analysis"] = response.content
        state["current_step"] = "image_analyzed"

    except Exception as e:
        state["error_message"] = f"图片分析失败: {str(e)}"
    state['image_data'] = ""
    return state


def extract_nutrition_info(state: AgentState) -> AgentState:
    """第二步：提取营养信息"""
    try:
        if not state.get("image_analysis"):
            state["error_message"] = "缺少图片分析结果"
            return state

        prompt = f"""
        基于以下食物描述，请提供详细的营养分析：

        食物描述：{state["image_analysis"]}

        请按照以下JSON格式返回营养分析：
        {{
            "food_items": ["食物1", "食物2", ...],
            "total_calories": 估计总热量(数字),
            "macronutrients": {{
                "protein": 蛋白质含量(克),
                "fat": 脂肪含量(克),
                "carbohydrates": 碳水化合物含量(克)
            }},
            "vitamins_minerals": {{
                "vitamin_c": "维生素C含量评估",
                "calcium": "钙含量评估",
                "iron": "铁含量评估"
            }},
            "health_score": 健康评分(1-10)
        }}
        """

        structured_model = state['analysis_model'].with_structured_output(
            NutritionAnalysis
        )

        nutrition_analysis = structured_model.invoke(prompt)
        state["nutrition_analysis"] = nutrition_analysis
        state["current_step"] = "nutrition_extracted"

    except Exception as e:
        state["error_message"] = f"营养分析失败: {str(e)}"

    return state


def generate_nutrition_advice(state: AgentState) -> AgentState:
    """第三步：生成营养建议"""
    try:
        if not state.get("nutrition_analysis"):
            state["error_message"] = "缺少营养分析结果"
            return state

        analysis = state["nutrition_analysis"]
        user_prefs = state.get("user_preferences", {})

        prompt = f"""
        基于以下营养分析结果，请提供专业的营养建议：

        营养分析：
        - 食物项目：{analysis.food_items}
        - 总热量：{analysis.total_calories}大卡
        - 宏量营养素：{analysis.macronutrients}
        - 健康评分：{analysis.health_score}/10

        用户偏好：{user_prefs}

        请按照以下JSON格式返回建议：
        {{
            "recommendations": ["具体建议1", "具体建议2", ...],
            "dietary_tips": ["饮食技巧1", "饮食技巧2", ...],
            "warnings": ["注意事项1", "注意事项2", ...],
            "alternative_foods": ["替代食物1", "替代食物2", ...]
        }}
        """
        model = state['analysis_model']
        structured_model = model.with_structured_output(
            NutritionAdvice
        )

        nutrition_advice = structured_model.invoke(prompt)
        state["nutrition_advice"] = nutrition_advice
        state["current_step"] = "advice_generated"

    except Exception as e:
        state["error_message"] = f"建议生成失败: {str(e)}"

    return state


def format_final_response(state: AgentState) -> AgentState:
    """第四步：格式化最终响应"""
    try:
        if state.get("error_message"):
            return state

        # 这里可以添加响应格式化逻辑
        state["current_step"] = "completed"

    except Exception as e:
        state["error_message"] = f"响应格式化失败: {str(e)}"

    return state
