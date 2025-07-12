from typing import Dict, List

from pydantic import BaseModel, Field


class Macronutrients(BaseModel):
    protein: float = Field(description="蛋白质 (克)")
    fat: float = Field(description="脂肪 (克)")
    carbohydrates: float = Field(description="碳水化合物 (克)")


class VitaminsMinerals(BaseModel):
    vitamin_a: str = Field(description="维生素A含量")
    vitamin_c: str = Field(description="维生素C含量")
    calcium: str = Field(description="钙含量")
    iron: str = Field(description="铁含量")
    # 可继续添加其它字段...


class NutritionAnalysis(BaseModel):
    """营养分析结果结构"""
    food_items: List[str] = Field(description="识别出的食物项目")
    total_calories: float = Field(description="总热量(大卡)")
    macronutrients: Macronutrients = Field(description="宏量营养素: 蛋白质、脂肪、碳水化合物")
    vitamins_minerals: VitaminsMinerals = Field(description="维生素和矿物质含量评估")
    health_score: int = Field(description="健康评分(1-10分)")


class NutritionAdvice(BaseModel):
    """营养建议结构"""
    recommendations: List[str] = Field(description="具体营养建议")
    dietary_tips: List[str] = Field(description="饮食建议")
    warnings: List[str] = Field(description="注意事项")
    alternative_foods: List[str] = Field(description="推荐替代食物")

