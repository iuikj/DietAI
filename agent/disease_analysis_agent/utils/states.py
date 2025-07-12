from datetime import date
from typing import Optional, List, Dict, TypedDict

from langchain_openai.chat_models.base import BaseChatOpenAI

from agent.disease_analysis_agent.utils.sturcts import FoodRecordCreate, AllergyCreate, DiseaseRiskAnalysis

from typing import Optional, List, Dict, TypedDict

from langchain_openai.chat_models.base import BaseChatOpenAI

from agent.disease_analysis_agent.utils.sturcts import FoodRecordCreate, AllergyCreate, \
    DiseaseCreate, NutritionDetailCreate


class AgentState(TypedDict):
    #过敏原
    allergen: Optional[AllergyCreate]
    #疾病
    disease:Optional[DiseaseCreate]
    #食物记录
    foodrecord: Optional[FoodRecordCreate]
    #营养信息
    nutritiondetail:Optional[NutritionDetailCreate]
    #分析结果
    disease_analysis: Optional[DiseaseRiskAnalysis]
    formatted_output: Optional[str]
    # 用户输入
    user_input: Optional[str]
    conversation_history: List[Dict]
    current_step: str
    error_message: Optional[str]
    vision_model: BaseChatOpenAI
    analysis_model: BaseChatOpenAI

class InputState(TypedDict):
    # 过敏原
    allergen: Optional[AllergyCreate]
    # 疾病
    disease: Optional[DiseaseCreate]
    # 食物记录
    foodrecord: Optional[FoodRecordCreate]
    # 营养信息
    nutritiondetail: Optional[NutritionDetailCreate]
    # 用户输入
    user_input: Optional[str]

class OutputState(TypedDict):
    disease_analysis: Optional[DiseaseRiskAnalysis]
    formatted_output: Optional[str]
    allergen: Optional[AllergyCreate]
    disease: Optional[DiseaseCreate]

