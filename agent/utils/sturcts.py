from typing import Dict, List
from enum import IntEnum
from pydantic import BaseModel, Field


class Macronutrients(BaseModel):
    protein: float = Field(description="蛋白质 (克)")
    fat: float = Field(description="脂肪 (克)")
    carbohydrates: float = Field(description="碳水化合物 (克)")
    dietary_fiber: float = Field(description="膳食纤维(g)")
    sugar: float = Field(description="糖(g)")


class VitaminsMinerals(BaseModel):
    vitamin_a: float = Field(description="维生素A含量(mg)")
    vitamin_c: float = Field(description="维生素C含量(mg)")
    vitamin_d: float = Field(description="维生素D含量(mg)")
    calcium: float = Field(description="钙含量(mg)")
    iron: float = Field(description="铁含量(mg)")
    sodium: float = Field(description="钠(mg)")
    potassium: float = Field(description="钾(mg)")
    cholesterol: float = Field(description="胆固醇(mg)")
    # 可继续添加其它字段...


class HealthLevelEnum(IntEnum):
    E = 1
    D = 2
    C = 3
    B = 4
    A = 5


class NutritionAnalysis(BaseModel):
    """营养分析结果结构"""
    food_items: List[str] = Field(description="识别出的食物项目")
    total_calories: float = Field(description="总热量(大卡)")
    macronutrients: Macronutrients = Field(description="宏量营养素: 蛋白质、脂肪、碳水化合物")
    vitamins_minerals: VitaminsMinerals = Field(description="维生素和矿物质含量评估")
    # health_level: str = Field(description="健康等级(A、B、C、D、E)")
    health_level: HealthLevelEnum = Field(description="健康等级：A最优，B良好，C一般，D较差，E很差")


class NutritionAdvice(BaseModel):
    """营养建议结构"""
    recommendations: List[str] = Field(description="具体营养建议")
    dietary_tips: List[str] = Field(description="饮食建议")
    warnings: List[str] = Field(description="注意事项")
    alternative_foods: List[str] = Field(description="推荐替代食物")


class AdviceDependencies(BaseModel):
    """营养建议依据结构"""
    nutrition_facts: List[str] = Field(
        default_factory=list,
        description="相关营养知识要点"
    )
    health_guidelines: List[str] = Field(
        default_factory=list,
        description="健康指南建议"
    )
    food_interactions: List[str] = Field(
        default_factory=list,
        description="食物之间的相互作用"
    )




class ChatResponse(BaseModel):
    """聊天机器人响应结构"""
    success: bool = Field(description="是否成功")
    response_content: str = Field(description="回复内容")
    session_id: str = Field(description="会话ID")
    session_type: int = Field(description="会话类型")
    metadata: Dict = Field(description="元数据信息")
    suggestions: List[str] = Field(description="建议操作列表")
