from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
from enum import IntEnum


# 基础响应模型
class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    data: Optional[Any] = Field(None, description="数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class PaginatedResponse(BaseResponse):
    """分页响应模型"""
    pagination: Optional[Dict[str, Any]] = Field(None, description="分页信息")


# 用户相关模型
class UserCreate(BaseModel):
    """用户创建模型"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., min_length=8, description="密码")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('密码长度至少8位')
        return v


class UserLogin(BaseModel):
    """用户登录模型"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


class UserResponse(BaseModel):
    """用户响应模型"""
    id: int
    username: str
    email: Optional[str]
    phone: Optional[str]
    avatar_url: Optional[str]
    status: int
    created_at: datetime
    last_login_at: Optional[datetime]

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """令牌响应模型"""
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求模型"""
    refresh_token: str = Field(..., description="刷新令牌")


class PasswordChangeRequest(BaseModel):
    """修改密码请求模型"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=8, description="新密码")


# 用户资料模型
class UserProfileUpdate(BaseModel):
    """用户资料更新模型"""
    real_name: Optional[str] = Field(None, max_length=100, description="真实姓名")
    gender: Optional[int] = Field(None, ge=1, le=3, description="性别：1男2女3其他")
    birth_date: Optional[date] = Field(None, description="出生日期")
    height: Optional[float] = Field(None, gt=0, le=300, description="身高(cm)")
    weight: Optional[float] = Field(None, gt=0, le=1000, description="体重(kg)")
    activity_level: Optional[int] = Field(None, ge=1, le=5, description="活动级别1-5")
    occupation: Optional[str] = Field(None, max_length=100, description="职业")
    region: Optional[str] = Field(None, max_length=100, description="地区")


class UserProfileResponse(BaseModel):
    """用户资料响应模型"""
    id: int
    user_id: int
    real_name: Optional[str]
    gender: Optional[int]
    birth_date: Optional[date]
    height: Optional[float]
    weight: Optional[float]
    bmi: Optional[float]
    activity_level: int
    occupation: Optional[str]
    region: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# 健康目标模型
class HealthGoalCreate(BaseModel):
    """健康目标创建模型"""
    goal_type: int = Field(..., ge=1, le=5, description="目标类型：1减重2增重3维持4增肌5减脂")
    target_weight: Optional[float] = Field(None, gt=0, description="目标体重")
    target_date: Optional[date] = Field(None, description="目标日期")


class HealthGoalResponse(BaseModel):
    """健康目标响应模型"""
    id: int
    user_id: int
    goal_type: int
    target_weight: Optional[float]
    target_date: Optional[date]
    current_status: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# 疾病信息模型
class DiseaseCreate(BaseModel):
    """疾病信息创建模型"""
    disease_code: Optional[str] = Field(None, max_length=20, description="疾病编码")
    disease_name: str = Field(..., max_length=200, description="疾病名称")
    severity_level: Optional[int] = Field(None, ge=1, le=3, description="严重程度1-3")
    diagnosed_date: Optional[date] = Field(None, description="诊断日期")
    notes: Optional[str] = Field(None, description="备注")


class DiseaseResponse(BaseModel):
    """疾病信息响应模型"""
    id: int
    user_id: int
    disease_code: Optional[str]
    disease_name: str
    severity_level: Optional[int]
    diagnosed_date: Optional[date]
    is_current: bool
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# 过敏信息模型
class AllergyCreate(BaseModel):
    """过敏信息创建模型"""
    allergen_type: int = Field(..., ge=1, le=4, description="过敏原类型：1食物2药物3环境4其他")
    allergen_name: str = Field(..., max_length=100, description="过敏原名称")
    severity_level: Optional[int] = Field(None, ge=1, le=3, description="严重程度1-3")
    reaction_description: Optional[str] = Field(None, description="反应描述")


class AllergyResponse(BaseModel):
    """过敏信息响应模型"""
    id: int
    user_id: int
    allergen_type: int
    allergen_name: str
    severity_level: Optional[int]
    reaction_description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# 体重记录模型
class WeightRecordCreate(BaseModel):
    """体重记录创建模型"""
    weight: float = Field(..., gt=0, description="体重(kg)")
    body_fat_percentage: Optional[float] = Field(None, ge=0, le=100, description="体脂率")
    muscle_mass: Optional[float] = Field(None, gt=0, description="肌肉量")
    measured_at: Optional[datetime] = Field(None, description="测量时间")
    notes: Optional[str] = Field(None, description="备注")
    device_type: Optional[str] = Field(None, max_length=50, description="设备类型")


class WeightRecordResponse(BaseModel):
    """体重记录响应模型"""
    id: int
    user_id: int
    weight: float
    body_fat_percentage: Optional[float]
    muscle_mass: Optional[float]
    bmi: Optional[float]
    measured_at: datetime
    notes: Optional[str]
    device_type: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# 食物记录模型
class FoodRecordCreate(BaseModel):
    """食物记录创建模型"""
    record_date: date = Field(..., description="记录日期")
    meal_type: int = Field(..., ge=1, le=5, description="餐次类型：1早餐2午餐3晚餐4加餐5夜宵")
    food_name: Optional[str] = Field(None, max_length=200, description="食物名称")
    description: Optional[str] = Field(None, description="描述")
    image_url: Optional[str] = Field(None, max_length=500, description="图片URL")
    recording_method: Optional[int] = Field(1, ge=1, le=3, description="记录方式：1手动2拍照3语音")


class FoodRecordResponse(BaseModel):
    """食物记录响应模型"""
    id: int
    user_id: int
    record_date: date
    meal_type: int
    food_name: Optional[str]
    description: Optional[str]
    image_url: Optional[str]
    recording_method: int
    analysis_status: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# 营养详情模型
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


class NutritionDetailResponse(BaseModel):
    """营养详情响应模型"""
    id: int
    food_record_id: int
    calories: float
    protein: float
    fat: float
    carbohydrates: float
    dietary_fiber: float
    sugar: float
    sodium: float
    cholesterol: float
    vitamin_a: float
    vitamin_c: float
    vitamin_d: float
    calcium: float
    iron: float
    potassium: float
    confidence_score: Optional[float]
    analysis_method: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# 每日营养汇总模型
class DailyNutritionSummaryResponse(BaseModel):
    """每日营养汇总响应模型"""
    id: int
    user_id: int
    summary_date: date
    total_calories: float
    total_protein: float
    total_fat: float
    total_carbohydrates: float
    total_fiber: float
    total_sodium: float
    meal_count: int
    water_intake: float
    exercise_calories: float
    health_score: Optional[float]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# 对话相关模型
class ConversationSessionCreate(BaseModel):
    """对话会话创建模型"""
    session_type: int = Field(1, ge=1, le=4, description="会话类型：1营养咨询2健康评估3食物识别4运动建议")
    title: Optional[str] = Field(None, max_length=200, description="会话标题")


class ConversationCreate(BaseModel):
    """对话创建模型"""
    title: Optional[str] = Field(None, max_length=200, description="会话标题")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")


class ConversationResponse(BaseModel):
    """对话响应模型"""
    id: int
    user_id: int
    session_id: str
    title: Optional[str]
    status: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationMessageCreate(BaseModel):
    """对话消息创建模型"""
    content: str = Field(..., description="消息内容")
    message_type: int = Field(..., ge=1, le=3, description="消息类型：1用户消息2助手消息3系统消息")
    message_metadata: Optional[Dict[str, Any]] = Field(None, description="消息元数据")


class MessageCreate(BaseModel):
    """消息创建模型"""
    content: str = Field(..., description="消息内容")
    message_type: int = Field(..., ge=1, le=3, description="消息类型：1文本2图片3语音")
    message_metadata: Optional[Dict[str, Any]] = Field(None, description="消息元数据")


class MessageResponse(BaseModel):
    """消息响应模型"""
    id: int
    session_id: str
    content: str
    message_type: int
    sender_type: int
    message_metadata: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


# 健康分析模型
class HealthAnalysisRequest(BaseModel):
    """健康分析请求模型"""
    analysis_type: str = Field(..., description="分析类型：bmr,tdee,nutrition_balance,health_score")
    date_range: Optional[Dict[str, str]] = Field(None, description="日期范围")
    parameters: Optional[Dict[str, Any]] = Field(None, description="额外参数")


class HealthAnalysisResponse(BaseModel):
    """健康分析响应模型"""
    analysis_type: str
    result: Dict[str, Any]
    recommendations: Optional[List[str]]
    timestamp: datetime


# 文件上传模型
class FileUploadResponse(BaseModel):
    """文件上传响应模型"""
    file_id: str
    file_name: str
    file_url: str
    file_size: int
    content_type: str
    upload_time: datetime


# 分页参数模型
class PaginationParams(BaseModel):
    """分页参数模型"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页大小")
    sort_by: Optional[str] = Field(None, description="排序字段")
    sort_order: Optional[str] = Field("desc", description="排序顺序：asc,desc")


# 查询参数模型
class DateRangeParams(BaseModel):
    """日期范围参数模型"""
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")


class NutritionTrendParams(DateRangeParams):
    """营养趋势参数模型"""
    metrics: Optional[List[str]] = Field(None, description="指标列表")


# 枚举类型
class GenderEnum(IntEnum):
    """性别枚举"""
    MALE = 1
    FEMALE = 2
    OTHER = 3


class ActivityLevelEnum(IntEnum):
    """活动级别枚举"""
    SEDENTARY = 1
    LIGHTLY_ACTIVE = 2
    MODERATELY_ACTIVE = 3
    VERY_ACTIVE = 4
    EXTREMELY_ACTIVE = 5


class MealTypeEnum(IntEnum):
    """餐次类型枚举"""
    BREAKFAST = 1
    LUNCH = 2
    DINNER = 3
    SNACK = 4
    LATE_NIGHT = 5


class GoalTypeEnum(IntEnum):
    """目标类型枚举"""
    LOSE_WEIGHT = 1
    GAIN_WEIGHT = 2
    MAINTAIN_WEIGHT = 3
    GAIN_MUSCLE = 4
    LOSE_FAT = 5

# =============与Agent进行通信的数据模型=============

# ----------和营养成分分析Agent通信的数据模型----------
class Macronutrients(BaseModel):
    protein: float
    fat: float
    carbohydrates: float


class VitaminsMinerals(BaseModel):
    vitamin_a: str
    vitamin_c: str
    calcium: str
    iron: str


class NutritionFacts(BaseModel):
    food_items: List[str]
    total_calories: float
    macronutrients: Macronutrients
    vitamins_minerals: VitaminsMinerals
    health_score: int


class Recommendations(BaseModel):
    recommendations: List[str]
    dietary_tips: List[str]
    warnings: List[str]
    alternative_foods: List[str]


class AgentAnalysisData(BaseModel):
    image_description: str
    nutrition_facts: NutritionFacts
    recommendations: Recommendations


