import asyncio
import json

from typing import List, Annotated
from agent.common_utils.rag_utils import rag_loader
from langchain.schema import Document
from agent.utils.sturcts import Macronutrients, VitaminsMinerals, AdviceDependencies
from agent.utils.states import AgentState
from agent.common_utils.redis_util import get_redis_client
from langgraph.prebuilt import InjectedState
from langchain_core.tools import tool, InjectedToolCallId


# @tool
# async def retrieve_nutrition_knowledge(
#         food_items: List[str],
#         total_calories: float,
#         macronutrients: Macronutrients,
#         vitamins_minerals: VitaminsMinerals,
#         state: Annotated[AgentState, InjectedState]
# ):
#     """
#     根据用户提交的营养分析参数，自动检索相关营养知识并返回详细信息，用于辅助生成个性化营养建议。
#
#     并将返回的相关营养信息（nutrition_facts、health_guidelines、food_interactions）更新到 state 中的 advice_dependencies 字段。
#
#     参数:
#         food_items (List[str]): 用户输入的食物项目列表（如 ["鸡胸肉", "西兰花"]）。
#         total_calories (float): 总热量，单位为大卡（kcal）。
#         macronutrients (Macronutrients): 宏量营养素对象，包含蛋白质、脂肪、碳水化合物等信息。
#         vitamins_minerals (VitaminsMinerals): 维生素和矿物质对象，包含常见微量营养素的信息。
#         state (Annotated[AgentState, InjectedState]): 当前代理状态对象，模型框架会自动注入，用于在调用完成后写回依赖信息。
#
#     返回:
#         AgentState更新后的状态对象，包含 advice_dependencies 字段
#
#     注意事项:
#         - 本函数会先尝试从缓存（Redis）中读取查询结果，若未命中则进行向量检索（Vector Store）。
#         - 适用于需要基于营养数据和个性化健康信息生成专业建议的场景。
#
#     示例调用:
#         retrieve_nutrition_knowledge(
#             food_items=["三文鱼", "藜麦"],
#             total_calories=550,
#             macronutrients=Macronutrients(protein=40, fat=15, carbs=45),
#             vitamins_minerals=VitaminsMinerals(vitamin_c=50, iron=8),
#             state=state
#         )
#     """
#     vectorstore = rag_loader()
#
#     query_list = [
#         f"食物项目: {', '.join(food_items)}",
#         f"总热量: {total_calories} 大卡",
#         f"宏量营养素: {macronutrients}",
#         f"维生素和矿物质: {vitamins_minerals}"
#     ]
#
#     # 获取 Redis 客户端
#     redis_client = await get_redis_client()
#
#     # 使用 query_list 转换 JSON 字符串作为缓存 key
#     query_key = json.dumps(query_list, ensure_ascii=False)
#
#     # 检查缓存
#     cached_result = await redis_client.get(query_key)
#     if cached_result:
#         search_results = [Document(page_content=content) for content in json.loads(cached_result)]
#     else:
#         # 加载 vector store（异步包装）
#         vectorstore = await asyncio.to_thread(rag_loader)
#
#         search_results = []
#         for query in query_list:
#             # 同步方法转异步
#             docs = await asyncio.to_thread(vectorstore.similarity_search, query, 2)
#             search_results.extend(docs)
#
#         # 缓存结果
#         await redis_client.set(query_key, json.dumps([doc.page_content for doc in search_results]))
#
#     # 关闭 Redis 连接
#     await redis_client.aclose()
#
#     # 解析结果
#     nutrition_facts = []
#     health_guidelines = []
#     food_interactions = []
#
#     for doc in search_results:
#         try:
#             content = json.loads(doc.page_content)
#             nutrition_facts.append(content.get("nutrition_facts", ""))
#             health_guidelines.append(content.get("health_guidelines", ""))
#             food_interactions.append(content.get("food_interactions", ""))
#         except Exception as e:
#             print(f"文档查询错误: {e}")
#             continue
#
#     advice_dependencies = AdviceDependencies(
#         nutrition_facts=nutrition_facts,
#         health_guidelines=health_guidelines,
#         food_interactions=food_interactions)
#
#     state["advice_dependencies"] = advice_dependencies
#     return {
#         "nutrition_facts": nutrition_facts,
#         "health_guidelines": health_guidelines,
#         "food_interactions": food_interactions,
#     }
