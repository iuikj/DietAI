from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Date, Numeric, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from .database import Base


class FoodRecord(Base):
    """食物记录表"""
    __tablename__ = "food_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    record_date = Column(Date, nullable=False)
    meal_type = Column(Integer, nullable=False)  # 1:早餐 2:午餐 3:晚餐 4:加餐 5:夜宵
    food_name = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)
    recording_method = Column(Integer, default=1)  # 1:手动输入 2:拍照识别 3:语音录入
    analysis_status = Column(Integer, default=1)  # 1:待分析 2:分析中 3:已完成 4:分析失败
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关系
    user = relationship("User", back_populates="food_records")
    nutrition_detail = relationship("NutritionDetail", back_populates="food_record", uselist=False)
    
    # 索引
    __table_args__ = (
        Index('idx_food_records_user_date', 'user_id', 'record_date'),
        Index('idx_food_records_user_meal', 'user_id', 'meal_type'),
    )


class NutritionDetail(Base):
    """营养成分详情表"""
    __tablename__ = "nutrition_details"
    
    id = Column(Integer, primary_key=True, index=True)
    food_record_id = Column(Integer, ForeignKey("food_records.id"), unique=True, nullable=False)
    
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
    
    # 其他
    confidence_score = Column(Numeric(3, 2), nullable=True)  # 识别置信度
    analysis_method = Column(String(50), nullable=True)  # 分析方法
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关系
    food_record = relationship("FoodRecord", back_populates="nutrition_detail")


class DailyNutritionSummary(Base):
    """每日营养汇总表"""
    __tablename__ = "daily_nutrition_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    summary_date = Column(Date, nullable=False)
    
    # 营养汇总
    total_calories = Column(Numeric(8, 2), default=0)
    total_protein = Column(Numeric(6, 2), default=0)
    total_fat = Column(Numeric(6, 2), default=0)
    total_carbohydrates = Column(Numeric(6, 2), default=0)
    total_fiber = Column(Numeric(6, 2), default=0)
    total_sodium = Column(Numeric(8, 2), default=0)
    
    # 统计信息
    meal_count = Column(Integer, default=0)
    water_intake = Column(Numeric(4, 2), default=0)  # 饮水量(L)
    exercise_calories = Column(Numeric(6, 2), default=0)  # 运动消耗(kcal)
    
    # 健康评分
    health_level = Column(Numeric(3, 2), nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关系
    user = relationship("User", back_populates="daily_summaries")
    
    # 索引
    __table_args__ = (
        Index('idx_daily_summaries_user_date', 'user_id', 'summary_date'),
    )


class FoodDatabase(Base):
    """食物数据库表"""
    __tablename__ = "food_database"
    
    id = Column(Integer, primary_key=True, index=True)
    food_code = Column(String(20), unique=True, nullable=True)  # 食物编码
    food_name = Column(String(200), nullable=False)
    food_name_en = Column(String(200), nullable=True)
    category = Column(String(100), nullable=True)  # 食物分类
    brand = Column(String(100), nullable=True)  # 品牌
    
    # 营养信息(每100g)
    calories_per_100g = Column(Numeric(6, 2), default=0)
    protein_per_100g = Column(Numeric(6, 2), default=0)
    fat_per_100g = Column(Numeric(6, 2), default=0)
    carbohydrates_per_100g = Column(Numeric(6, 2), default=0)
    fiber_per_100g = Column(Numeric(6, 2), default=0)
    sodium_per_100g = Column(Numeric(8, 2), default=0)
    
    # 元数据
    data_source = Column(String(100), nullable=True)  # 数据来源
    verified = Column(Boolean, default=False)  # 是否已验证
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 索引
    __table_args__ = (
        Index('idx_food_database_name', 'food_name'),
        Index('idx_food_database_category', 'category'),
    )