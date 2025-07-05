
from typing import Dict, List, Optional, TypedDict

from langchain_openai.chat_models.base import BaseChatOpenAI

from agent.utils.sturcts import NutritionAnalysis, NutritionAdvice


class AgentState(TypedDict):
    """Agent状态管理"""
    image_dir: Optional[str]
    image_data: Optional[str]
    image_analysis: Optional[str]
    nutrition_analysis: Optional[NutritionAnalysis]
    nutrition_advice: Optional[NutritionAdvice]
    user_preferences: Optional[Dict]
    conversation_history: List[Dict]
    current_step: str
    error_message: Optional[str]
    vision_model: BaseChatOpenAI
    analysis_model: BaseChatOpenAI


class InputState(TypedDict):
    image_data: Optional[str]
