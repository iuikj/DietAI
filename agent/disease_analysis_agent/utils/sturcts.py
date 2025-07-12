from datetime import date
from typing import Optional, TypedDict, List

from pydantic import BaseModel, Field


class FoodRecordCreate(BaseModel):
    """食物记录创建模型"""
    record_date: date = Field(..., description="记录日期")
    meal_type: int = Field(..., ge=1, le=5, description="餐次类型：1早餐2午餐3晚餐4加餐5夜宵")
    food_name: Optional[str] = Field(None, max_length=200, description="食物名称")
    description: Optional[str] = Field(None, description="描述")
    image_url: Optional[str] = Field(None, max_length=500, description="图片URL")
    recording_method: Optional[int] = Field(1, ge=1, le=3, description="记录方式：1手动2拍照3语音")

class AllergyCreate(BaseModel):
    """过敏信息创建模型"""
    allergen_type: int = Field(..., ge=1, le=4, description="过敏原类型：1食物2药物3环境4其他")
    allergen_name: str = Field(..., max_length=100, description="过敏原名称")
    severity_level: Optional[int] = Field(None, ge=1, le=3, description="严重程度1-3")
    reaction_description: Optional[str] = Field(None, description="反应描述")

class DiseaseCreate(BaseModel):
    """疾病信息创建模型"""
    disease_code: Optional[str] = Field(None, max_length=20, description="疾病编码")
    disease_name: str = Field(..., max_length=200, description="疾病名称")
    severity_level: Optional[int] = Field(None, ge=1, le=3, description="严重程度1-3")
    diagnosed_date: Optional[date] = Field(None, description="诊断日期")
    notes: Optional[str] = Field(None, description="备注")

class NutritionDetailCreate(BaseModel):
    """营养详情创建模型"""
    food_record_id: int = Field(..., description="食物记录ID")
    calories: Optional[float] = Field(0, ge=0, description="热量(kcal)")
    protein: Optional[float] = Field(0, ge=0, description="蛋白质(g)")
    fat: Optional[float] = Field(0, ge=0, description="脂肪(g)")
    carbohydrates: Optional[float] = Field(0, ge=0, description="碳水化合物(g)")
    dietary_fiber: Optional[float] = Field(0, ge=0, description="膳食纤维(g)")
    sugar: Optional[float] = Field(0, ge=0, description="糖类(g)")
    sodium: Optional[float] = Field(0, ge=0, description="钠(mg)")
    cholesterol: Optional[float] = Field(0, ge=0, description="胆固醇(mg)")
    vitamin_a: Optional[float] = Field(0, ge=0, description="维生素A(μg)")
    vitamin_c: Optional[float] = Field(0, ge=0, description="维生素C(mg)")
    vitamin_d: Optional[float] = Field(0, ge=0, description="维生素D(μg)")
    calcium: Optional[float] = Field(0, ge=0, description="钙(mg)")
    iron: Optional[float] = Field(0, ge=0, description="铁(mg)")
    potassium: Optional[float] = Field(0, ge=0, description="钾(mg)")
    confidence_score: Optional[float] = Field(None, ge=0, le=1, description="置信度")
    analysis_method: Optional[str] = Field(None, max_length=50, description="分析方法")


from typing import List, Optional
from pydantic import BaseModel, Field

class DiseaseRiskAnalysis(BaseModel):
    # 疾病分析结构
    disease: str = Field(..., description="疾病名称，例如高血压、糖尿病")
    allergen: Optional[str] = Field(
        ..., description="相关过敏原名称（如有），例如花生、牛奶"
    )
    risky_nutrients: List[str] = Field(
        ..., description="该疾病患者需要注意的营养成分，例如钠、胆固醇"
    )
    risk_explanations: List[str] = Field(
        ..., description="每个营养成分对应的健康风险说明"
    )
    avoid_foods: List[str] = Field(
        ..., description="根据疾病与营养信息推断，应避免摄入的典型食物"
    )
    health_tips: List[str] = Field(
        ..., description="个性化营养建议，例如推荐多吃哪些或注意哪些饮食习惯"
    )


