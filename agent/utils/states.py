
from typing import Dict, List, Optional, TypedDict

from langchain_openai.chat_models.base import BaseChatOpenAI

from agent.utils.sturcts import NutritionAnalysis, NutritionAdvice, AdviceDependencies


class AgentState(TypedDict):
    """Agent状态管理"""
    image_dir: Optional[str]
    image_data: Optional[str]
    image_analysis: Optional[str]
    nutrition_analysis: Optional[NutritionAnalysis]
    nutrition_advice: Optional[NutritionAdvice]
    advice_dependencies: Optional[AdviceDependencies]
    user_preferences: Optional[Dict]
    retrieved_documents: List[str]
    conversation_history: List[Dict]
    current_step: str
    error_message: Optional[str]
    vision_model: BaseChatOpenAI
    analysis_model: BaseChatOpenAI


class InputState(TypedDict):
    image_data: Optional[str]
    user_preferences: Optional[Dict]


class OutputState(TypedDict):
    nutrition_analysis: Optional[NutritionAnalysis]
    nutrition_advice: Optional[NutritionAdvice]
    advice_dependencies: Optional[AdviceDependencies]
