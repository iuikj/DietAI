from agent.utils.sturcts import NutritionAnalysis, AdviceDependencies


def create_nutrition_prompt(image_analysis: str) -> str:
    return f"""
    作为一名专业的注册营养师，请你基于以下食物图片分析描述，严格按照以下要求，生成详细、准确的营养分析数据。
    
    ###  图片描述
    {image_analysis}
    
    ###  返回格式要求
    请你务必只返回符合以下 JSON 格式的分析数据（不要包含文字解释或额外描述），并确保所有字段完整，数据类型和含义如下：
    
    ```json
    {{
        "food_items": ["食物名称1", "食物名称2", ...],  // 识别出的食物项目列表
        "total_calories": 浮点数,  // 总热量 (大卡)
        "macronutrients": {{
            "protein": 浮点数,         // 蛋白质 (g)
            "fat": 浮点数,             // 脂肪 (g)
            "carbohydrates": 浮点数,  // 碳水化合物 (g)
            "dietary_fiber": 浮点数,  // 膳食纤维 (g)
            "sugar": 浮点数           // 糖 (g)
        }},
        "vitamins_minerals": {{
            "vitamin_a": 浮点数,      // 维生素A (μg)
            "vitamin_c": 浮点数,      // 维生素C (mg)
            "vitamin_d": 浮点数,      // 维生素D (μg)
            "calcium": 浮点数,        // 钙 (mg)
            "iron": 浮点数,           // 铁 (mg)
            "sodium": 浮点数,         // 钠 (mg)
            "potassium": 浮点数       // 钾 (mg)
            "cholesterol": 浮点数      // 胆固醇(mg)
        }},
        "health_level": 整数         // 健康等级 (1~5, 其中 1=E(很差), 2=D(较差), 3=C(一般), 4=B(良好), 5=A(最优))
    }}
     注意
    所有数值必须基于标准食品数据库进行估算，务必准确、完整。
    
    不允许返回字符串描述（例如 "低含量" 或 "not calculated"），无数据可估计请填写 0。
    
    所有字段必须存在，禁止缺省，严格符合数据类型要求。
    
    严格遵守以上规范生成 JSON 返回。
    """


# def create_advice_prompt(analysis: NutritionAnalysis, advice_dependencies: AdviceDependencies = None, user_prefs: dict = None) -> str:
#     """
#     生成营养建议提示词
#
#     Args:
#         analysis: 包含食物分析结果的字典
#         advice_dependencies: 包含营养知识参考的字典
#         user_prefs: 用户偏好信息
#
#     Returns:
#         str: 格式化的提示词
#     """
#     if advice_dependencies is None:
#         advice_dependencies = {}
#
#     return f"""
#         基于以下营养分析结果和专业知识，请提供专业的营养建议：
#
#         营养分析：
#         - 食物项目：{analysis.get('food_items')}
#         - 总热量：{analysis.get('total_calories')}大卡
#         - 宏量营养素：{analysis.get('macronutrients')}
#         - 健康等级：{analysis.get('health_level')}
#
#         营养知识参考：
#         - 营养要点：{advice_dependencies.get('nutrition_facts', [])}
#         - 健康指南：{advice_dependencies.get('health_guidelines', [])}
#         - 食物相互作用：{advice_dependencies.get('food_interactions', [])}
#
#         用户偏好：{user_prefs or {}}
#
#         请按照以下JSON格式返回建议：
#         {{
#             "recommendations": ["具体建议1", "具体建议2", ...],
#             "dietary_tips": ["饮食技巧1", "饮食技巧2", ...],
#             "warnings": ["注意事项1", "注意事项2", ...],
#             "alternative_foods": ["替代食物1", "替代食物2", ...]
#         }}
#         """


