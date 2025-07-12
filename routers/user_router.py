from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from datetime import datetime, date
import json
import logging
import traceback
from decimal import Decimal

from shared.models.database import get_db
from shared.models.schemas import (
    BaseResponse, UserProfileUpdate, UserProfileResponse,
    HealthGoalCreate, HealthGoalResponse, DiseaseCreate, DiseaseResponse,
    AllergyCreate, AllergyResponse, WeightRecordCreate, WeightRecordResponse,
    OnboardingStepUpdate, OnboardingDataRequest
)
from shared.utils.auth import get_current_user
from shared.models.user_models import User, UserProfile, HealthGoal, Disease, Allergy, WeightRecord
from shared.config.redis_config import cache_service

router = APIRouter(prefix="/users", tags=["用户", "用户管理"])
logger = logging.getLogger(__name__)

# 错误消息常量
class ErrorMessages:
    """错误消息常量"""
    PROFILE_NOT_FOUND = "用户资料不存在"
    PROFILE_LOAD_FAILED = "获取用户资料失败"
    PROFILE_UPDATE_FAILED = "更新用户资料失败"
    HEALTH_GOAL_NOT_FOUND = "健康目标不存在"
    HEALTH_GOAL_CREATE_FAILED = "创建健康目标失败"
    HEALTH_GOAL_UPDATE_FAILED = "更新健康目标失败"
    DISEASE_CREATE_FAILED = "添加疾病信息失败"
    ALLERGY_CREATE_FAILED = "添加过敏信息失败"
    WEIGHT_RECORD_CREATE_FAILED = "添加体重记录失败"
    ONBOARDING_UPDATE_FAILED = "更新引导步骤失败"
    ONBOARDING_COMPLETE_FAILED = "完成用户引导失败"
    DATABASE_ERROR = "数据库操作失败"
    UNKNOWN_ERROR = "未知错误"

def handle_database_error(e: Exception, operation: str = "数据库操作") -> HTTPException:
    """统一处理数据库错误"""
    logger.error(f"{operation}失败: {str(e)}")
    logger.error(f"错误类型: {type(e).__name__}")
    logger.error(f"详细堆栈: {traceback.format_exc()}")
    
    if isinstance(e, SQLAlchemyError):
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{operation}失败，请稍后重试"
        )
    else:
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{operation}失败: {str(e)}"
        )

def calculate_bmi(height: Optional[float], weight: Optional[float]) -> Optional[float]:
    """计算BMI"""
    if height and weight and height > 0:
        height_m = height / 100
        return round(weight / (height_m ** 2), 2)
    return None

def format_profile_data(profile: UserProfile) -> dict:
    """格式化用户资料数据 - 只使用数据库中存在的字段"""
    return {
        # 数据库中存在的字段
        "id": profile.id,
        "user_id": profile.user_id,
        "real_name": profile.real_name,
        "gender": profile.gender,
        "birth_date": profile.birth_date.isoformat() if profile.birth_date else None,
        "height": float(profile.height) if profile.height else None,
        "weight": float(profile.weight) if profile.weight else None,
        "bmi": float(profile.bmi) if profile.bmi else None,
        "activity_level": profile.activity_level,
        "occupation": profile.occupation,
        "region": profile.region,
        "created_at": profile.created_at.isoformat(),
        "updated_at": profile.updated_at.isoformat(),
        
        # 以下字段在当前数据库中不存在，返回默认值以保持API兼容性
        "dietary_preferences": None,
        "food_dislikes": None,
        "wake_up_time": None,
        "sleep_time": None,
        "meal_times": None,
        "health_status": 1,  # 默认健康状态
        "onboarding_completed": False,  # 默认未完成引导
        "onboarding_step": 0,  # 默认引导步骤
    }


@router.get("/profile", response_model=BaseResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户资料"""
    try:
        # 先尝试从缓存获取
        cached_profile = cache_service.get_user_profile(current_user.id)
        if cached_profile:
            return BaseResponse(
                success=True,
                message="获取用户资料成功",
                data=cached_profile
            )
        
        # 从数据库获取
        profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        
        if not profile:
            # 如果没有资料，创建默认资料
            profile = UserProfile(
                user_id=current_user.id,
                activity_level=2  # 默认轻度活动
            )
            db.add(profile)
            db.commit()
            db.refresh(profile)
        
        # 计算BMI
        bmi = calculate_bmi(profile.height, profile.weight)
        if bmi and profile.bmi != bmi:
            profile.bmi = bmi
            db.commit()
        
        profile_data = format_profile_data(profile)
        
        # 缓存用户资料
        cache_service.cache_user_profile(current_user.id, profile_data)
        
        return BaseResponse(
            success=True,
            message="获取用户资料成功",
            data=profile_data
        )
    except Exception as e:
        raise handle_database_error(e, "获取用户资料")


@router.put("/profile", response_model=BaseResponse)
async def update_user_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户资料"""
    try:
        # 获取现有资料
        profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        
        if not profile:
            # 如果没有资料，创建新的
            profile = UserProfile(user_id=current_user.id)
            db.add(profile)
        
        # 更新字段
        update_data = profile_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(profile, field):
                setattr(profile, field, value)
        
        # 重新计算BMI
        bmi = calculate_bmi(profile.height, profile.weight)
        if bmi:
            profile.bmi = bmi
        
        profile.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(profile)
        
        # 清除缓存
        cache_service.clear_user_cache(current_user.id)
        
        return BaseResponse(
            success=True,
            message="用户资料更新成功",
            data=format_profile_data(profile)
        )
    except Exception as e:
        db.rollback()
        raise handle_database_error(e, "更新用户资料")


@router.post("/health-goals", response_model=BaseResponse)
async def create_health_goal(
    goal_data: HealthGoalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建健康目标"""
    try:
        # 暂停其他进行中的目标
        db.query(HealthGoal).filter(
            HealthGoal.user_id == current_user.id,
            HealthGoal.current_status == 1
        ).update({"current_status": 3})  # 暂停
        
        # 创建新目标
        health_goal = HealthGoal(
            user_id=current_user.id,
            goal_type=goal_data.goal_type,
            target_weight=goal_data.target_weight,
            target_date=goal_data.target_date,
            current_status=1  # 进行中
        )
        
        db.add(health_goal)
        db.commit()
        db.refresh(health_goal)
        
        return BaseResponse(
            success=True,
            message="健康目标创建成功",
            data={
                "id": health_goal.id,
                "user_id": health_goal.user_id,
                "goal_type": health_goal.goal_type,
                "target_weight": float(health_goal.target_weight) if health_goal.target_weight else None,
                "target_date": health_goal.target_date.isoformat() if health_goal.target_date else None,
                "current_status": health_goal.current_status,
                "created_at": health_goal.created_at.isoformat()
            }
        )
    except Exception as e:
        db.rollback()
        raise handle_database_error(e, "创建健康目标")


@router.get("/health-goals", response_model=BaseResponse)
async def get_health_goals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    status_filter: Optional[int] = Query(None, description="状态筛选")
):
    """获取健康目标列表"""
    try:
        query = db.query(HealthGoal).filter(HealthGoal.user_id == current_user.id)
        
        if status_filter is not None:
            query = query.filter(HealthGoal.current_status == status_filter)
        
        goals = query.order_by(HealthGoal.created_at.desc()).all()
        
        goals_data = []
        for goal in goals:
            goals_data.append({
                "id": goal.id,
                "user_id": goal.user_id,
                "goal_type": goal.goal_type,
                "target_weight": float(goal.target_weight) if goal.target_weight else None,
                "target_date": goal.target_date.isoformat() if goal.target_date else None,
                "current_status": goal.current_status,
                "created_at": goal.created_at.isoformat(),
                "updated_at": goal.updated_at.isoformat()
            })
        
        return BaseResponse(
            success=True,
            message="获取健康目标列表成功",
            data=goals_data
        )
    except Exception as e:
        raise handle_database_error(e, "获取健康目标列表")


@router.put("/health-goals/{goal_id}", response_model=BaseResponse)
async def update_health_goal(
    goal_id: int,
    goal_data: HealthGoalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新健康目标"""
    try:
        goal = db.query(HealthGoal).filter(
            HealthGoal.id == goal_id,
            HealthGoal.user_id == current_user.id
        ).first()
        
        if not goal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorMessages.HEALTH_GOAL_NOT_FOUND
            )
        
        # 更新字段
        goal.goal_type = goal_data.goal_type
        goal.target_weight = goal_data.target_weight
        goal.target_date = goal_data.target_date
        goal.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(goal)
        
        return BaseResponse(
            success=True,
            message="健康目标更新成功",
            data={
                "id": goal.id,
                "user_id": goal.user_id,
                "goal_type": goal.goal_type,
                "target_weight": float(goal.target_weight) if goal.target_weight else None,
                "target_date": goal.target_date.isoformat() if goal.target_date else None,
                "current_status": goal.current_status,
                "updated_at": goal.updated_at.isoformat()
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise handle_database_error(e, "更新健康目标")


@router.post("/diseases", response_model=BaseResponse)
async def add_disease(
    disease_data: DiseaseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """添加疾病信息"""
    try:
        disease = Disease(
            user_id=current_user.id,
            disease_code=disease_data.disease_code,
            disease_name=disease_data.disease_name,
            severity_level=disease_data.severity_level,
            diagnosed_date=disease_data.diagnosed_date,
            notes=disease_data.notes
        )
        
        db.add(disease)
        db.commit()
        db.refresh(disease)
        
        return BaseResponse(
            success=True,
            message="疾病信息添加成功",
            data={
                "id": disease.id,
                "user_id": disease.user_id,
                "disease_code": disease.disease_code,
                "disease_name": disease.disease_name,
                "severity_level": disease.severity_level,
                "diagnosed_date": disease.diagnosed_date.isoformat() if disease.diagnosed_date else None,
                "is_current": disease.is_current,
                "notes": disease.notes,
                "created_at": disease.created_at.isoformat()
            }
        )
    except Exception as e:
        db.rollback()
        raise handle_database_error(e, "添加疾病信息")


@router.get("/diseases", response_model=BaseResponse)
async def get_diseases(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    is_current: Optional[bool] = Query(None, description="是否当前病症")
):
    """获取疾病信息列表"""
    try:
        query = db.query(Disease).filter(Disease.user_id == current_user.id)
        
        if is_current is not None:
            query = query.filter(Disease.is_current == is_current)
        
        diseases = query.order_by(Disease.created_at.desc()).all()
        
        diseases_data = []
        for disease in diseases:
            diseases_data.append({
                "id": disease.id,
                "user_id": disease.user_id,
                "disease_code": disease.disease_code,
                "disease_name": disease.disease_name,
                "severity_level": disease.severity_level,
                "diagnosed_date": disease.diagnosed_date.isoformat() if disease.diagnosed_date else None,
                "is_current": disease.is_current,
                "notes": disease.notes,
                "created_at": disease.created_at.isoformat()
            })
        
        return BaseResponse(
            success=True,
            message="获取疾病信息列表成功",
            data=diseases_data
        )
    except Exception as e:
        raise handle_database_error(e, "获取疾病信息列表")


@router.post("/allergies", response_model=BaseResponse)
async def add_allergy(
    allergy_data: AllergyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """添加过敏信息"""
    try:
        allergy = Allergy(
            user_id=current_user.id,
            allergen_type=allergy_data.allergen_type,
            allergen_name=allergy_data.allergen_name,
            severity_level=allergy_data.severity_level,
            reaction_description=allergy_data.reaction_description
        )
        
        db.add(allergy)
        db.commit()
        db.refresh(allergy)
        
        return BaseResponse(
            success=True,
            message="过敏信息添加成功",
            data={
                "id": allergy.id,
                "user_id": allergy.user_id,
                "allergen_type": allergy.allergen_type,
                "allergen_name": allergy.allergen_name,
                "severity_level": allergy.severity_level,
                "reaction_description": allergy.reaction_description,
                "created_at": allergy.created_at.isoformat()
            }
        )
    except Exception as e:
        db.rollback()
        raise handle_database_error(e, "添加过敏信息")


@router.get("/allergies", response_model=BaseResponse)
async def get_allergies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    allergen_type: Optional[int] = Query(None, description="过敏原类型")
):
    """获取过敏信息列表"""
    try:
        query = db.query(Allergy).filter(Allergy.user_id == current_user.id)
        
        if allergen_type is not None:
            query = query.filter(Allergy.allergen_type == allergen_type)
        
        allergies = query.order_by(Allergy.created_at.desc()).all()
        
        allergies_data = []
        for allergy in allergies:
            allergies_data.append({
                "id": allergy.id,
                "user_id": allergy.user_id,
                "allergen_type": allergy.allergen_type,
                "allergen_name": allergy.allergen_name,
                "severity_level": allergy.severity_level,
                "reaction_description": allergy.reaction_description,
                "created_at": allergy.created_at.isoformat()
            })
        
        return BaseResponse(
            success=True,
            message="获取过敏信息列表成功",
            data=allergies_data
        )
    except Exception as e:
        raise handle_database_error(e, "获取过敏信息列表")


@router.post("/weight-records", response_model=BaseResponse)
async def add_weight_record(
    weight_data: WeightRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """添加体重记录"""
    try:
        # 获取用户资料并计算BMI
        user_profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        bmi = calculate_bmi(user_profile.height if user_profile else None, weight_data.weight)
        
        weight_record = WeightRecord(
            user_id=current_user.id,
            weight=weight_data.weight,
            body_fat_percentage=weight_data.body_fat_percentage,
            muscle_mass=weight_data.muscle_mass,
            bmi=bmi,
            measured_at=weight_data.measured_at or datetime.utcnow(),
            notes=weight_data.notes,
            device_type=weight_data.device_type
        )
        
        db.add(weight_record)
        db.commit()
        db.refresh(weight_record)
        
        # 更新用户资料中的体重
        if user_profile:
            user_profile.weight = weight_data.weight
            user_profile.bmi = bmi
            user_profile.updated_at = datetime.utcnow()
            db.commit()
            
            # 清除缓存
            cache_service.clear_user_cache(current_user.id)
        
        return BaseResponse(
            success=True,
            message="体重记录添加成功",
            data={
                "id": weight_record.id,
                "user_id": weight_record.user_id,
                "weight": float(weight_record.weight),
                "body_fat_percentage": float(weight_record.body_fat_percentage) if weight_record.body_fat_percentage else None,
                "muscle_mass": float(weight_record.muscle_mass) if weight_record.muscle_mass else None,
                "bmi": float(weight_record.bmi) if weight_record.bmi else None,
                "measured_at": weight_record.measured_at.isoformat(),
                "notes": weight_record.notes,
                "device_type": weight_record.device_type,
                "created_at": weight_record.created_at.isoformat()
            }
        )
    except Exception as e:
        db.rollback()
        raise handle_database_error(e, "添加体重记录")


@router.get("/weight-records", response_model=BaseResponse)
async def get_weight_records(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    limit: int = Query(50, description="记录数量限制")
):
    """获取体重记录列表"""
    try:
        query = db.query(WeightRecord).filter(WeightRecord.user_id == current_user.id)
        
        if start_date:
            query = query.filter(WeightRecord.measured_at >= start_date)
        if end_date:
            query = query.filter(WeightRecord.measured_at <= end_date)
        
        records = query.order_by(WeightRecord.measured_at.desc()).limit(limit).all()
        
        records_data = []
        for record in records:
            records_data.append({
                "id": record.id,
                "user_id": record.user_id,
                "weight": float(record.weight),
                "body_fat_percentage": float(record.body_fat_percentage) if record.body_fat_percentage else None,
                "muscle_mass": float(record.muscle_mass) if record.muscle_mass else None,
                "bmi": float(record.bmi) if record.bmi else None,
                "measured_at": record.measured_at.isoformat(),
                "notes": record.notes,
                "device_type": record.device_type,
                "created_at": record.created_at.isoformat()
            })
        
        return BaseResponse(
            success=True,
            message="获取体重记录列表成功",
            data=records_data
        )
    except Exception as e:
        raise handle_database_error(e, "获取体重记录列表")


# 用户引导相关端点
@router.get("/onboarding/status", response_model=BaseResponse)
async def get_onboarding_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户引导状态 - 简化版本，因为引导字段不存在"""
    try:
        logger.info(f"开始获取用户 {current_user.id} 的引导状态")
        
        profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        
        if not profile:
            logger.info(f"用户 {current_user.id} 没有资料，创建新的资料")
            profile = UserProfile(
                user_id=current_user.id,
                activity_level=2
            )
            db.add(profile)
            db.commit()
            db.refresh(profile)
            logger.info(f"用户 {current_user.id} 的资料创建成功")
        
        # 由于引导字段不存在，返回默认值
        data = {
            "onboarding_completed": False,  # 默认未完成
            "current_step": 0,  # 默认步骤
            "total_steps": 6,
            "next_step": 1  # 默认下一步
        }
        
        logger.info(f"用户 {current_user.id} 的引导状态: {data}")
        
        return BaseResponse(
            success=True,
            message="获取引导状态成功",
            data=data
        )
    except Exception as e:
        raise handle_database_error(e, "获取引导状态")


@router.post("/onboarding/step", response_model=BaseResponse)
async def update_onboarding_step(
    step_data: OnboardingStepUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户引导步骤 - 简化版本"""
    try:
        profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        
        if not profile:
            profile = UserProfile(
                user_id=current_user.id,
                activity_level=2
            )
            db.add(profile)
        
        # 处理步骤数据，只更新存在的字段
        if step_data.data:
            for key, value in step_data.data.items():
                if hasattr(profile, key):
                    # 跳过数据库中不存在的字段
                    if key in ['dietary_preferences', 'food_dislikes', 'meal_times', 'wake_up_time', 'sleep_time', 'health_status', 'onboarding_step', 'onboarding_completed']:
                        logger.warning(f"跳过不存在的字段: {key}")
                        continue
                    else:
                        setattr(profile, key, value)
        
        profile.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(profile)
        
        # 清除缓存
        cache_service.clear_user_cache(current_user.id)
        
        return BaseResponse(
            success=True,
            message="引导步骤更新成功",
            data={
                "current_step": step_data.step,
                "completed": step_data.completed,
                "next_step": step_data.step + 1 if not step_data.completed else None
            }
        )
    except Exception as e:
        db.rollback()
        raise handle_database_error(e, "更新引导步骤")


@router.post("/onboarding/complete", response_model=BaseResponse)
async def complete_onboarding(
    onboarding_data: OnboardingDataRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """完成用户引导并批量保存数据 - 简化版本"""
    try:
        profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        
        if not profile:
            profile = UserProfile(
                user_id=current_user.id,
                activity_level=2
            )
            db.add(profile)
        
        # 更新基本信息
        if onboarding_data.basic_info:
            for key, value in onboarding_data.basic_info.items():
                if hasattr(profile, key):
                    if key == 'birth_date' and isinstance(value, str):
                        profile.birth_date = datetime.strptime(value, "%Y-%m-%d").date()
                    else:
                        setattr(profile, key, value)
        
        # 更新身体数据
        if onboarding_data.physical_data:
            for key, value in onboarding_data.physical_data.items():
                if hasattr(profile, key):
                    setattr(profile, key, value)
        
        # 跳过不存在的字段
        if onboarding_data.dietary_preferences:
            logger.warning("跳过dietary_preferences字段，数据库中不存在")
        
        if onboarding_data.lifestyle_habits:
            for key, value in onboarding_data.lifestyle_habits.items():
                if hasattr(profile, key):
                    if key in ['meal_times', 'wake_up_time', 'sleep_time']:
                        logger.warning(f"跳过不存在的字段: {key}")
                        continue
                    else:
                        setattr(profile, key, value)
        
        # 计算BMI
        bmi = calculate_bmi(profile.height, profile.weight)
        if bmi:
            profile.bmi = bmi
        
        profile.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(profile)
        
        # 创建健康目标
        health_goals_created = 0
        if onboarding_data.health_goals:
            for goal_data in onboarding_data.health_goals:
                health_goal = HealthGoal(
                    user_id=current_user.id,
                    goal_type=goal_data.get('goal_type', 1),
                    target_weight=goal_data.get('target_weight'),
                    target_date=datetime.strptime(goal_data['target_date'], "%Y-%m-%d").date() if goal_data.get('target_date') else None,
                    current_status=1
                )
                db.add(health_goal)
                health_goals_created += 1
        
        # 添加疾病信息
        diseases_added = 0
        if onboarding_data.medical_conditions:
            for condition in onboarding_data.medical_conditions:
                disease = Disease(
                    user_id=current_user.id,
                    disease_name=condition['disease_name'],
                    disease_code=condition.get('disease_code'),
                    severity_level=condition.get('severity_level', 1),
                    diagnosed_date=datetime.strptime(condition['diagnosed_date'], "%Y-%m-%d").date() if condition.get('diagnosed_date') else None,
                    notes=condition.get('notes')
                )
                db.add(disease)
                diseases_added += 1
        
        # 添加过敏信息
        allergies_added = 0
        if onboarding_data.allergies:
            for allergy_data in onboarding_data.allergies:
                allergy = Allergy(
                    user_id=current_user.id,
                    allergen_type=allergy_data.get('allergen_type', 1),
                    allergen_name=allergy_data['allergen_name'],
                    severity_level=allergy_data.get('severity_level', 1),
                    reaction_description=allergy_data.get('reaction_description')
                )
                db.add(allergy)
                allergies_added += 1
        
        db.commit()
        
        # 清除缓存
        cache_service.clear_user_cache(current_user.id)
        
        return BaseResponse(
            success=True,
            message="用户引导完成成功",
            data={
                "profile_id": profile.id,
                "onboarding_completed": True,  # 返回默认值
                "bmi": float(profile.bmi) if profile.bmi else None,
                "health_goals_created": health_goals_created,
                "medical_conditions_added": diseases_added,
                "allergies_added": allergies_added
            }
        )
    except Exception as e:
        db.rollback()
        raise handle_database_error(e, "完成用户引导")


@router.post("/onboarding/reset", response_model=BaseResponse)
async def reset_onboarding(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """重置用户引导状态 - 简化版本"""
    try:
        profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        
        if profile:
            profile.updated_at = datetime.utcnow()
            db.commit()
            
            # 清除缓存
            cache_service.clear_user_cache(current_user.id)
        
        return BaseResponse(
            success=True,
            message="引导状态重置成功",
            data={
                "onboarding_completed": False,
                "current_step": 0
            }
        )
    except Exception as e:
        db.rollback()
        raise handle_database_error(e, "重置引导状态") 