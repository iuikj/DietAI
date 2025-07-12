from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Date, Numeric, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from .database import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    phone = Column(String(20), unique=True, index=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    avatar_url = Column(String(500), nullable=True)
    status = Column(Integer, default=1)  # 1:正常 2:禁用 3:删除
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_login_at = Column(DateTime, nullable=True)
    
    # 关系
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    health_goals = relationship("HealthGoal", back_populates="user")
    diseases = relationship("Disease", back_populates="user")
    allergies = relationship("Allergy", back_populates="user")
    food_records = relationship("FoodRecord", back_populates="user")
    weight_records = relationship("WeightRecord", back_populates="user")
    daily_summaries = relationship("DailyNutritionSummary", back_populates="user")
    conversations = relationship("ConversationSession", back_populates="user")


class UserProfile(Base):
    """用户资料表 - 最小化版本，只包含数据库中确实存在的字段"""
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    real_name = Column(String(100), nullable=True)
    gender = Column(Integer, nullable=True)  # 1:男 2:女 3:其他
    birth_date = Column(Date, nullable=True)
    height = Column(Numeric(5, 2), nullable=True)  # 身高(cm)
    weight = Column(Numeric(5, 2), nullable=True)  # 体重(kg)
    bmi = Column(Numeric(4, 2), nullable=True)  # BMI
    activity_level = Column(Integer, default=2)  # 1:久坐 2:轻度 3:中度 4:重度 5:超重度
    occupation = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关系
    user = relationship("User", back_populates="profile")
    
    # 以下字段在当前数据库中不存在，如果需要需要通过数据库迁移添加：
    # - dietary_preferences (Text, JSON格式存储饮食偏好)
    # - food_dislikes (Text, JSON格式存储不喜欢的食物)  
    # - wake_up_time (String(10), 起床时间 HH:MM)
    # - sleep_time (String(10), 睡觉时间 HH:MM)
    # - meal_times (Text, JSON格式存储用餐时间)
    # - health_status (Integer, 健康状态)
    # - onboarding_completed (Boolean, 引导完成状态)
    # - onboarding_step (Integer, 当前引导步骤)


class HealthGoal(Base):
    """健康目标表"""
    __tablename__ = "health_goals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    goal_type = Column(Integer, nullable=False)  # 1:减重 2:增重 3:维持 4:增肌 5:减脂
    target_weight = Column(Numeric(5, 2), nullable=True)
    target_date = Column(Date, nullable=True)
    current_status = Column(Integer, default=1)  # 1:进行中 2:已完成 3:已暂停 4:已取消
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关系
    user = relationship("User", back_populates="health_goals")


class Disease(Base):
    """疾病信息表"""
    __tablename__ = "diseases"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    disease_code = Column(String(20), nullable=True)  # ICD-10编码
    disease_name = Column(String(200), nullable=False)
    severity_level = Column(Integer, nullable=True)  # 1:轻度 2:中度 3:重度
    diagnosed_date = Column(Date, nullable=True)
    is_current = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关系
    user = relationship("User", back_populates="diseases")


class Allergy(Base):
    """过敏信息表"""
    __tablename__ = "allergies"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    allergen_type = Column(Integer, nullable=False)  # 1:食物 2:药物 3:环境 4:其他
    allergen_name = Column(String(100), nullable=False)
    severity_level = Column(Integer, nullable=True)  # 1:轻度 2:中度 3:重度
    reaction_description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关系
    user = relationship("User", back_populates="allergies")


class WeightRecord(Base):
    """体重记录表"""
    __tablename__ = "weight_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    weight = Column(Numeric(5, 2), nullable=False)
    body_fat_percentage = Column(Numeric(4, 2), nullable=True)  # 体脂率
    muscle_mass = Column(Numeric(5, 2), nullable=True)  # 肌肉量
    bmi = Column(Numeric(4, 2), nullable=True)
    measured_at = Column(DateTime, default=func.now())
    notes = Column(Text, nullable=True)
    device_type = Column(String(50), nullable=True)  # 测量设备类型
    created_at = Column(DateTime, default=func.now())
    
    # 关系
    user = relationship("User", back_populates="weight_records")
    
    # 索引
    __table_args__ = (
        Index('idx_weight_records_user_measured', 'user_id', 'measured_at'),
    ) 