# 导入所有数据库模型
from .database import Base, get_db, create_tables, drop_tables
from .user_models import User, UserProfile, HealthGoal, Disease, Allergy, WeightRecord
from .food_models import FoodRecord, NutritionDetail, DailyNutritionSummary, FoodDatabase
from .conversation_models import ConversationSession, ConversationMessage, ConversationContext
from .saved_meal_models import SavedMeal, SavedMealNutrition, UserSavedMealFavorite

# 导入所有Pydantic模型
from . import schemas

__all__ = [
    # 数据库相关
    "Base",
    "get_db", 
    "create_tables",
    "drop_tables",
    
    # 用户模型
    "User",
    "UserProfile", 
    "HealthGoal",
    "Disease",
    "Allergy",
    "WeightRecord",
    
    # 食物模型
    "FoodRecord",
    "NutritionDetail",
    "DailyNutritionSummary", 
    "FoodDatabase",
    
    # 对话模型
    "ConversationSession",
    "ConversationMessage",
    "ConversationContext",
    
    # 保存菜品模型
    "SavedMeal",
    "SavedMealNutrition",
    "UserSavedMealFavorite",
    
    # Pydantic模型
    "schemas"
]
