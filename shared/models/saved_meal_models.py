from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Date, Numeric, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from .database import Base


class SavedMeal(Base):
    """用户保存的菜品模板表"""
    __tablename__ = "saved_meals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    meal_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)
    category = Column(String(100), nullable=True)  # 分类：主食、蔬菜、肉类、汤类等
    tags = Column(JSON, nullable=True)  # 标签数组，如["健康", "减脂", "高蛋白"]
    
    # 是否为公共菜品（可供其他用户使用）
    is_public = Column(Boolean, default=False)
    
    # 使用统计
    usage_count = Column(Integer, default=0)  # 使用次数
    favorite_count = Column(Integer, default=0)  # 收藏次数（如果是公共菜品）
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关系
    user = relationship("User", back_populates="saved_meals")
    nutrition_template = relationship("SavedMealNutrition", back_populates="saved_meal", uselist=False)
    
    # 索引
    __table_args__ = (
        Index('idx_saved_meals_user_id', 'user_id'),
        Index('idx_saved_meals_category', 'category'),
        Index('idx_saved_meals_public', 'is_public'),
    )


class SavedMealNutrition(Base):
    """保存菜品的营养模板表"""
    __tablename__ = "saved_meal_nutrition"
    
    id = Column(Integer, primary_key=True, index=True)
    saved_meal_id = Column(Integer, ForeignKey("saved_meals.id"), unique=True, nullable=False)
    
    # 基础营养信息（每100g或每份）
    serving_size = Column(Numeric(6, 2), default=100)  # 份量大小(g)
    serving_unit = Column(String(20), default="g")  # 单位
    
    # 宏量营养素
    calories = Column(Numeric(8, 2), default=0)  # 热量(kcal)
    protein = Column(Numeric(6, 2), default=0)  # 蛋白质(g)
    fat = Column(Numeric(6, 2), default=0)  # 脂肪(g)
    carbohydrates = Column(Numeric(6, 2), default=0)  # 碳水化合物(g)
    dietary_fiber = Column(Numeric(6, 2), default=0)  # 膳食纤维(g)
    sugar = Column(Numeric(6, 2), default=0)  # 糖类(g)
    
    # 微量营养素
    sodium = Column(Numeric(8, 2), default=0)  # 钠(mg)
    cholesterol = Column(Numeric(6, 2), default=0)  # 胆固醇(mg)
    
    # 维生素
    vitamin_a = Column(Numeric(8, 2), default=0)  # 维生素A(μg)
    vitamin_c = Column(Numeric(8, 2), default=0)  # 维生素C(mg)
    vitamin_d = Column(Numeric(8, 2), default=0)  # 维生素D(μg)
    
    # 矿物质
    calcium = Column(Numeric(8, 2), default=0)  # 钙(mg)
    iron = Column(Numeric(8, 2), default=0)  # 铁(mg)
    potassium = Column(Numeric(8, 2), default=0)  # 钾(mg)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关系
    saved_meal = relationship("SavedMeal", back_populates="nutrition_template")


class UserSavedMealFavorite(Base):
    """用户收藏的菜品表（用于公共菜品收藏）"""
    __tablename__ = "user_saved_meal_favorites"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    saved_meal_id = Column(Integer, ForeignKey("saved_meals.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # 关系
    user = relationship("User")
    saved_meal = relationship("SavedMeal")
    
    # 索引和约束
    __table_args__ = (
        Index('idx_user_favorites_user_meal', 'user_id', 'saved_meal_id', unique=True),
        Index('idx_user_favorites_user_id', 'user_id'),
    )