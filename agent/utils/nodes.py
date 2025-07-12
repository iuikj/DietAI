import asyncio
from langchain.schema import Document

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

import json

from typing import List, Annotated
from agent.common_utils.rag_utils import rag_loader

from agent.common_utils.image_utils import encode_image_to_base64
from agent.common_utils.redis_util import get_redis_client
from agent.utils.configuration import Configuration
from agent.utils.states import AgentState, InputState, OutputState
from agent.utils.sturcts import NutritionAnalysis, NutritionAdvice, AdviceDependencies
from agent.common_utils.model_utils import get_model
from agent.utils.prompts import create_nutrition_prompt


def state_init(state: AgentState, config: RunnableConfig):
    configurable = Configuration.from_runnable_config(config)
    if state.get("image_dir") is None:
        initial_state = AgentState(
            image_data=state['image_data'],
            image_analysis=None,
            nutrition_analysis=None,
            nutrition_advice=None,
            advice_dependencies=None,
            retrieved_documents=[],
            user_preferences=state['user_preferences'],  # 后续要添加 已添加
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
        advice_dependencies=None,
        retrieved_documents=[],
        user_preferences=state['user_preferences'],  # 后续要添加 已添加
        conversation_history=[],
        current_step="starting",
        error_message=None,
        vision_model=get_model(model_provider=configurable.vision_model_provider, model_name=configurable.vision_model),
        analysis_model=get_model(model_provider=configurable.analysis_model_provider,
                                 model_name=configurable.analysis_model)
    )
    print(initial_state["current_step"])
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
        print(state["current_step"])

    except Exception as e:
        state["error_message"] = f"图片分析失败: {str(e)}"
    state['image_data'] = ""
    return state


def extract_nutrition_info(state: AgentState) -> AgentState:
    """第二步：提取营养信息"""
    # 后期可以对食物营养分析也配一个rag
    try:
        if not state.get("image_analysis"):
            state["error_message"] = "缺少图片分析结果"
            return state

        prompt = create_nutrition_prompt(
            image_analysis=state["image_analysis"]
        )
        # prompt = f"""
        #         基于以下食物描述，请提供详细的营养分析：
        #
        #         食物描述：{state["image_analysis"]}
        #
        #         请按照以下JSON格式返回营养分析：
        #         {{
        #             "food_items": ["食物1", "食物2", ...],
        #             "total_calories": 估计总热量(数字),
        #             "macronutrients": {{
        #                 "protein": 蛋白质含量(克),
        #                 "fat": 脂肪含量(克),
        #                 "carbohydrates": 碳水化合物含量(克)
        #             }},
        #             "vitamins_minerals": {{
        #                 "vitamin_c": "维生素C含量评估",
        #                 "calcium": "钙含量评估",
        #                 "iron": "铁含量评估"
        #             }},
        #             "health_level": 健康评分等级A-E
        #         }}
        #         """

        structured_model = state['analysis_model'].with_structured_output(
            NutritionAnalysis
        )

        nutrition_analysis = structured_model.invoke(prompt)
        state["nutrition_analysis"] = nutrition_analysis
        state["current_step"] = "nutrition_extracted"
        print(state["current_step"])

    except Exception as e:
        state["error_message"] = f"营养分析失败: {str(e)}"

    return state


async def retrieve_nutrition_knowledge(state: AgentState) -> AgentState:
    """第三步，检索营养知识"""
    try:
        if not state.get("nutrition_analysis"):
            state["error_message"] = "缺少营养分析结果"
            return state
        analysis = state["nutrition_analysis"]

        query_list = [
            f"食物项目: {', '.join(analysis.food_items)}",
            f"总热量: {analysis.total_calories} 大卡",
            f"宏量营养素: {analysis.macronutrients}",
            f"维生素和矿物质: {analysis.vitamins_minerals}"
        ]
        # 获取 Redis 客户端
        redis_client = await get_redis_client()

        # 使用 query_list 转换 JSON 字符串作为缓存 key
        query_key = json.dumps(query_list, ensure_ascii=False)

        # 检查缓存
        cached_result = await redis_client.get(query_key)
        if cached_result:
            search_results = [Document(page_content=content) for content in json.loads(cached_result)]
        else:
            # 加载 vector store（异步包装）
            vectorstore = await asyncio.to_thread(rag_loader)

            search_results = []
            for query in query_list:
                # 同步方法转异步
                docs = await asyncio.to_thread(vectorstore.similarity_search, query, 2)
                search_results.extend(docs)

            # 缓存结果
            await redis_client.set(query_key, json.dumps([doc.page_content for doc in search_results]))

        # 关闭 Redis 连接
        await redis_client.aclose()

        result=[]
        for doc in search_results:
            try:
                content = doc.page_content.strip()
                result.append(content)

            except Exception as e:
                print(f"文档查询错误: {e}")
                continue

        state["retrieved_documents"] = result
        state["current_step"] = "retrieve_nutrition_knowledge"
        print(state["current_step"])

    except Exception as e:
        state["error_message"] = f"营养知识检索失败: {str(e)}"

    return state


def generate_dependencies(state: AgentState) -> AgentState:
    try:
        if not state.get("retrieved_documents"):
            advice_dependencies = AdviceDependencies(
                     nutrition_facts=[],
                     health_guidelines=[],
                     food_interactions=[])
            state["advice_dependencies"] = advice_dependencies
            print("缺少相关营养知识文档")
            return state

        documents = state["retrieved_documents"]
        user_prefs = state.get("user_preferences", {})
        prompt = f"""
                基于以下专业知识和用户信息，请提供相关营养知识参考：
                专业知识：{documents}
                用户偏好：{user_prefs}
                请按照以下json格式返回： 
                {{
                    "nutrition_facts": ["知识要点1", "知识要点2", ...],
                    "health_guidelines": ["健康指南1", "健康指南2", ...],
                    "food_interactions": ["相互作用1", "相互作用2", ...]（如果没有内容则填“无”）
                }}
                """

        model = state['analysis_model']

        structured_model = model.with_structured_output(
            AdviceDependencies
        )

        try:
            advice_dependencies = structured_model.invoke(prompt)
            # print("调用成功，结果:", advice_dependencies)
            state["advice_dependencies"] = advice_dependencies
            state["current_step"] = "generate_dependencies"
            print(state["current_step"])
        except Exception as e:
            print("invoke 调用异常:", e)
    except Exception as e:
        print("依赖项生成失败:", e)

    return state


def generate_nutrition_advice(state: AgentState) -> AgentState:
    """第四步：生成营养建议"""
    try:
        if not state.get("advice_dependencies"):
            print("缺少相关营养知识")
            # state["error_message"] = "缺少相关营养知识"

        analysis = state["nutrition_analysis"]
        advice_dependencies = state["advice_dependencies"]
        user_prefs = state.get("user_preferences", {})

        # prompt = f"""
        # 基于以下营养分析结果，请提供专业的营养建议：
        #
        # 营养分析：
        # - 食物项目：{analysis.food_items}
        # - 总热量：{analysis.total_calories}大卡
        # - 宏量营养素：{analysis.macronutrients}
        # - 维生素和矿物质：{analysis.vitamins_minerals}
        # - 健康等级：{analysis.health_level}
        #
        # 营养知识参考：使用retrieve_nutrition_knowledge工具获得相关知识参考
        # 用户偏好：{user_prefs}
        #
        # 请按照以下 JSON 格式返回建议和依据：
        # {{
        #     "nutrition_advice": {{
        #         "recommendations": ["具体建议1", "具体建议2", ...],
        #         "dietary_tips": ["饮食技巧1", "饮食技巧2", ...],
        #         "warnings": ["注意事项1", "注意事项2", ...],
        #         "alternative_foods": ["替代食物1", "替代食物2", ...]
        #     }},
        #     "advice_dependencies": {{
        #         "nutrition_facts": ["知识要点1", "知识要点2", ...],
        #         "health_guidelines": ["健康指南1", "健康指南2", ...],
        #         "food_interactions": ["相互作用1", "相互作用2", ...]（如果没有内容则填“无”）
        #     }}
        # }}
        # """

        prompt = f"""
             基于以下营养分析结果和专业知识，请提供专业的营养建议：

             营养分析：
             - 食物项目：{analysis.food_items}
             - 总热量：{analysis.total_calories}大卡
             - 宏量营养素：{analysis.macronutrients}
             - 健康等级：{analysis.health_level}

             营养知识参考：
             - 营养要点：{advice_dependencies.nutrition_facts}
             - 健康指南：{advice_dependencies.health_guidelines}
             - 食物相互作用：{advice_dependencies.food_interactions}

             用户偏好：{user_prefs}
             请基于以上信息，结合科学营养学原理，给出具体、可执行的营养建议。
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
        print(state["current_step"])

    except Exception as e:
        # state["error_message"] = f"建议生成失败: {str(e)}"
        print(f"建议生成失败: {str(e)}")

    return state


def format_final_response(state: AgentState) -> AgentState:
    """第四步：格式化最终响应"""
    try:
        if state.get("error_message"):
            return state

        # 这里可以添加响应格式化逻辑
        state["current_step"] = "completed"
        print(state["current_step"])

    except Exception as e:
        state["error_message"] = f"响应格式化失败: {str(e)}"

    return state
