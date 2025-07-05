from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date

from shared.models.database import get_db
from shared.models.schemas import (
    BaseResponse, UserProfileUpdate, UserProfileResponse,
    HealthGoalCreate, HealthGoalResponse, DiseaseCreate, DiseaseResponse,
    AllergyCreate, AllergyResponse, WeightRecordCreate, WeightRecordResponse,
    PaginationParams, DateRangeParams
)
from shared.utils.auth import get_current_user
from shared.models.user_models import User, UserProfile, HealthGoal, Disease, Allergy, WeightRecord
from shared.config.redis_config import cache_service

router = APIRouter(prefix="/users", tags=["用户管理"])


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
        bmi = None
        if profile.height and profile.weight:
            height_m = profile.height / 100
            bmi = round(profile.weight / (height_m ** 2), 2)
            if profile.bmi != bmi:
                profile.bmi = bmi
                db.commit()
        
        profile_data = {
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
            "updated_at": profile.updated_at.isoformat()
        }
        
        # 缓存用户资料
        cache_service.cache_user_profile(current_user.id, profile_data)
        
        return BaseResponse(
            success=True,
            message="获取用户资料成功",
            data=profile_data
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户资料失败: {str(e)}"
        )


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
        if profile.height and profile.weight:
            height_m = profile.height / 100
            profile.bmi = round(profile.weight / (height_m ** 2), 2)
        
        profile.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(profile)
        
        # 清除缓存
        cache_service.clear_user_cache(current_user.id)
        
        return BaseResponse(
            success=True,
            message="用户资料更新成功",
            data={
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
                "updated_at": profile.updated_at.isoformat()
            }
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新用户资料失败: {str(e)}"
        )


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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建健康目标失败: {str(e)}"
        )


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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取健康目标列表失败: {str(e)}"
        )


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
                detail="健康目标不存在"
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
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新健康目标失败: {str(e)}"
        )


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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"添加疾病信息失败: {str(e)}"
        )


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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取疾病信息列表失败: {str(e)}"
        )


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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"添加过敏信息失败: {str(e)}"
        )


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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取过敏信息列表失败: {str(e)}"
        )


@router.post("/weight-records", response_model=BaseResponse)
async def add_weight_record(
    weight_data: WeightRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """添加体重记录"""
    try:
        # 计算BMI
        bmi = None
        user_profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        if user_profile and user_profile.height:
            height_m = user_profile.height / 100
            bmi = round(weight_data.weight / (height_m ** 2), 2)
        
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"添加体重记录失败: {str(e)}"
        )


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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取体重记录列表失败: {str(e)}"
        ) 