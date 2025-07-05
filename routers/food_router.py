from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
from datetime import datetime, date, timedelta

from shared.models.database import get_db
from shared.models.schemas import (
    BaseResponse, FoodRecordCreate, FoodRecordResponse,
    NutritionDetailCreate, NutritionDetailResponse,
    DailyNutritionSummaryResponse, DateRangeParams,
    PaginationParams, FileUploadResponse
)
from shared.utils.auth import get_current_user
from shared.models.user_models import User
from shared.models.food_models import FoodRecord, NutritionDetail, DailyNutritionSummary, FoodDatabase
from shared.config.redis_config import cache_service
from shared.config.minio_config import minio_client

router = APIRouter(prefix="/foods", tags=["食物记录"])


@router.post("/records", response_model=BaseResponse)
async def create_food_record(
    food_data: FoodRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建食物记录"""
    try:
        food_record = FoodRecord(
            user_id=current_user.id,
            record_date=food_data.record_date,
            meal_type=food_data.meal_type,
            food_name=food_data.food_name,
            description=food_data.description,
            image_url=food_data.image_url,
            recording_method=food_data.recording_method or 1,
            analysis_status=1  # 待分析
        )
        
        db.add(food_record)
        db.commit()
        db.refresh(food_record)
        
        # 清除相关缓存
        cache_key = f"nutrition:daily:{current_user.id}:{food_data.record_date}"
        cache_service.redis.delete(cache_key)
        
        return BaseResponse(
            success=True,
            message="食物记录创建成功",
            data={
                "id": food_record.id,
                "user_id": food_record.user_id,
                "record_date": food_record.record_date.isoformat(),
                "meal_type": food_record.meal_type,
                "food_name": food_record.food_name,
                "description": food_record.description,
                "image_url": food_record.image_url,
                "recording_method": food_record.recording_method,
                "analysis_status": food_record.analysis_status,
                "created_at": food_record.created_at.isoformat()
            }
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建食物记录失败: {str(e)}"
        )


@router.get("/records", response_model=BaseResponse)
async def get_food_records(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    meal_type: Optional[int] = Query(None, description="餐次类型"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小")
):
    """获取食物记录列表"""
    try:
        query = db.query(FoodRecord).filter(FoodRecord.user_id == current_user.id)
        
        if start_date:
            query = query.filter(FoodRecord.record_date >= start_date)
        if end_date:
            query = query.filter(FoodRecord.record_date <= end_date)
        if meal_type:
            query = query.filter(FoodRecord.meal_type == meal_type)
        
        # 总数统计
        total = query.count()
        
        # 分页查询
        offset = (page - 1) * page_size
        records = query.order_by(FoodRecord.record_date.desc(), FoodRecord.created_at.desc()).offset(offset).limit(page_size).all()
        
        records_data = []
        for record in records:
            records_data.append({
                "id": record.id,
                "user_id": record.user_id,
                "record_date": record.record_date.isoformat(),
                "meal_type": record.meal_type,
                "food_name": record.food_name,
                "description": record.description,
                "image_url": record.image_url,
                "recording_method": record.recording_method,
                "analysis_status": record.analysis_status,
                "created_at": record.created_at.isoformat(),
                "updated_at": record.updated_at.isoformat()
            })
        
        pagination_info = {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
        
        return BaseResponse(
            success=True,
            message="获取食物记录列表成功",
            data={
                "records": records_data,
                "pagination": pagination_info
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取食物记录列表失败: {str(e)}"
        )


@router.get("/records/{record_id}", response_model=BaseResponse)
async def get_food_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取食物记录详情"""
    try:
        record = db.query(FoodRecord).filter(
            FoodRecord.id == record_id,
            FoodRecord.user_id == current_user.id
        ).first()
        
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="食物记录不存在"
            )
        
        # 获取营养详情
        nutrition_detail = db.query(NutritionDetail).filter(
            NutritionDetail.food_record_id == record_id
        ).first()
        
        record_data = {
            "id": record.id,
            "user_id": record.user_id,
            "record_date": record.record_date.isoformat(),
            "meal_type": record.meal_type,
            "food_name": record.food_name,
            "description": record.description,
            "image_url": record.image_url,
            "recording_method": record.recording_method,
            "analysis_status": record.analysis_status,
            "created_at": record.created_at.isoformat(),
            "updated_at": record.updated_at.isoformat(),
            "nutrition_detail": None
        }
        
        if nutrition_detail:
            record_data["nutrition_detail"] = {
                "id": nutrition_detail.id,
                "calories": float(nutrition_detail.calories),
                "protein": float(nutrition_detail.protein),
                "fat": float(nutrition_detail.fat),
                "carbohydrates": float(nutrition_detail.carbohydrates),
                "dietary_fiber": float(nutrition_detail.dietary_fiber),
                "sugar": float(nutrition_detail.sugar),
                "sodium": float(nutrition_detail.sodium),
                "cholesterol": float(nutrition_detail.cholesterol),
                "vitamin_a": float(nutrition_detail.vitamin_a),
                "vitamin_c": float(nutrition_detail.vitamin_c),
                "vitamin_d": float(nutrition_detail.vitamin_d),
                "calcium": float(nutrition_detail.calcium),
                "iron": float(nutrition_detail.iron),
                "potassium": float(nutrition_detail.potassium),
                "confidence_score": float(nutrition_detail.confidence_score) if nutrition_detail.confidence_score else None,
                "analysis_method": nutrition_detail.analysis_method
            }
        
        return BaseResponse(
            success=True,
            message="获取食物记录详情成功",
            data=record_data
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取食物记录详情失败: {str(e)}"
        )


@router.post("/records/{record_id}/nutrition", response_model=BaseResponse)
async def add_nutrition_detail(
    record_id: int,
    nutrition_data: NutritionDetailCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """添加营养详情"""
    try:
        # 验证记录是否存在且属于当前用户
        record = db.query(FoodRecord).filter(
            FoodRecord.id == record_id,
            FoodRecord.user_id == current_user.id
        ).first()
        
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="食物记录不存在"
            )
        
        # 检查是否已有营养详情
        existing_detail = db.query(NutritionDetail).filter(
            NutritionDetail.food_record_id == record_id
        ).first()
        
        if existing_detail:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该食物记录已有营养详情"
            )
        
        # 创建营养详情
        nutrition_detail = NutritionDetail(
            food_record_id=record_id,
            calories=nutrition_data.calories or 0,
            protein=nutrition_data.protein or 0,
            fat=nutrition_data.fat or 0,
            carbohydrates=nutrition_data.carbohydrates or 0,
            dietary_fiber=nutrition_data.dietary_fiber or 0,
            sugar=nutrition_data.sugar or 0,
            sodium=nutrition_data.sodium or 0,
            cholesterol=nutrition_data.cholesterol or 0,
            vitamin_a=nutrition_data.vitamin_a or 0,
            vitamin_c=nutrition_data.vitamin_c or 0,
            vitamin_d=nutrition_data.vitamin_d or 0,
            calcium=nutrition_data.calcium or 0,
            iron=nutrition_data.iron or 0,
            potassium=nutrition_data.potassium or 0,
            confidence_score=nutrition_data.confidence_score,
            analysis_method=nutrition_data.analysis_method
        )
        
        db.add(nutrition_detail)
        
        # 更新食物记录的分析状态
        record.analysis_status = 3  # 已完成
        record.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(nutrition_detail)
        
        # 触发每日营养汇总更新
        await update_daily_nutrition_summary(current_user.id, record.record_date, db)
        
        # 清除相关缓存
        cache_key = f"nutrition:daily:{current_user.id}:{record.record_date}"
        cache_service.redis.delete(cache_key)
        
        return BaseResponse(
            success=True,
            message="营养详情添加成功",
            data={
                "id": nutrition_detail.id,
                "food_record_id": nutrition_detail.food_record_id,
                "calories": float(nutrition_detail.calories),
                "protein": float(nutrition_detail.protein),
                "fat": float(nutrition_detail.fat),
                "carbohydrates": float(nutrition_detail.carbohydrates),
                "dietary_fiber": float(nutrition_detail.dietary_fiber),
                "sugar": float(nutrition_detail.sugar),
                "sodium": float(nutrition_detail.sodium),
                "cholesterol": float(nutrition_detail.cholesterol),
                "confidence_score": float(nutrition_detail.confidence_score) if nutrition_detail.confidence_score else None,
                "analysis_method": nutrition_detail.analysis_method,
                "created_at": nutrition_detail.created_at.isoformat()
            }
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"添加营养详情失败: {str(e)}"
        )


@router.get("/daily-summary/{summary_date}", response_model=BaseResponse)
async def get_daily_nutrition_summary(
    summary_date: date,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取每日营养汇总"""
    try:
        # 先尝试从缓存获取
        cached_summary = cache_service.get_daily_nutrition(current_user.id, summary_date.isoformat())
        if cached_summary:
            return BaseResponse(
                success=True,
                message="获取每日营养汇总成功",
                data=cached_summary
            )
        
        # 从数据库获取
        summary = db.query(DailyNutritionSummary).filter(
            DailyNutritionSummary.user_id == current_user.id,
            DailyNutritionSummary.summary_date == summary_date
        ).first()
        
        if not summary:
            # 如果没有汇总，生成一个
            summary = await create_daily_nutrition_summary(current_user.id, summary_date, db)
        
        summary_data = {
            "id": summary.id,
            "user_id": summary.user_id,
            "summary_date": summary.summary_date.isoformat(),
            "total_calories": float(summary.total_calories),
            "total_protein": float(summary.total_protein),
            "total_fat": float(summary.total_fat),
            "total_carbohydrates": float(summary.total_carbohydrates),
            "total_fiber": float(summary.total_fiber),
            "total_sodium": float(summary.total_sodium),
            "meal_count": summary.meal_count,
            "water_intake": float(summary.water_intake),
            "exercise_calories": float(summary.exercise_calories),
            "health_score": float(summary.health_score) if summary.health_score else None,
            "created_at": summary.created_at.isoformat(),
            "updated_at": summary.updated_at.isoformat()
        }
        
        # 缓存汇总数据
        cache_service.cache_daily_nutrition(current_user.id, summary_date.isoformat(), summary_data)
        
        return BaseResponse(
            success=True,
            message="获取每日营养汇总成功",
            data=summary_data
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取每日营养汇总失败: {str(e)}"
        )


@router.get("/nutrition-trends", response_model=BaseResponse)
async def get_nutrition_trends(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    metrics: Optional[str] = Query("calories,protein,fat,carbohydrates", description="指标列表，逗号分隔")
):
    """获取营养趋势"""
    try:
        # 设置默认日期范围（最近30天）
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # 获取营养汇总数据
        summaries = db.query(DailyNutritionSummary).filter(
            DailyNutritionSummary.user_id == current_user.id,
            DailyNutritionSummary.summary_date >= start_date,
            DailyNutritionSummary.summary_date <= end_date
        ).order_by(DailyNutritionSummary.summary_date).all()
        
        # 解析指标列表
        metric_list = [metric.strip() for metric in metrics.split(',')]
        
        trends_data = {
            "date_range": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "metrics": metric_list,
            "data": []
        }
        
        for summary in summaries:
            data_point = {
                "date": summary.summary_date.isoformat(),
                "values": {}
            }
            
            for metric in metric_list:
                if metric == "calories":
                    data_point["values"]["calories"] = float(summary.total_calories)
                elif metric == "protein":
                    data_point["values"]["protein"] = float(summary.total_protein)
                elif metric == "fat":
                    data_point["values"]["fat"] = float(summary.total_fat)
                elif metric == "carbohydrates":
                    data_point["values"]["carbohydrates"] = float(summary.total_carbohydrates)
                elif metric == "fiber":
                    data_point["values"]["fiber"] = float(summary.total_fiber)
                elif metric == "sodium":
                    data_point["values"]["sodium"] = float(summary.total_sodium)
                elif metric == "health_score":
                    data_point["values"]["health_score"] = float(summary.health_score) if summary.health_score else None
            
            trends_data["data"].append(data_point)
        
        return BaseResponse(
            success=True,
            message="获取营养趋势成功",
            data=trends_data
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取营养趋势失败: {str(e)}"
        )


@router.post("/upload-image", response_model=BaseResponse)
async def upload_food_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """上传食物图片"""
    try:
        print("上传图片开始")
        # 验证文件类型
        if file.content_type not in ["image/jpeg", "image/png", "image/gif"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不支持的文件类型，请上传JPEG、PNG或GIF格式的图片"
            )
        
        # 验证文件大小（10MB限制）
        file_content = await file.read()
        if len(file_content) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件大小不能超过10MB"
            )
        
        # 生成文件名
        timestamp = int(datetime.utcnow().timestamp())
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        object_name = f"food_images/{current_user.id}/{timestamp}.{file_extension}"

        print("上传图片开始-minio")
        # 上传到MinIO
        success = minio_client.upload_file(object_name, file_content, file.content_type)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="文件上传失败"
            )
        print("上传图片结束-minio")
        # 获取文件URL
        file_url = minio_client.get_file_url(object_name)  # 使用默认有效期，7天
        print("获取文件URL结束")
        return BaseResponse(
            success=True,
            message="图片上传成功",
            data={
                "file_id": object_name,
                "file_name": file.filename,
                "file_url": file_url,
                "file_size": len(file_content),
                "content_type": file.content_type,
                "upload_time": datetime.utcnow().isoformat()
            }
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"图片上传失败: {str(e)}"
        )


# 辅助函数
async def create_daily_nutrition_summary(user_id: int, summary_date: date, db: Session) -> DailyNutritionSummary:
    """创建每日营养汇总"""
    # 统计当天的所有食物记录的营养信息
    nutrition_stats = db.query(
        func.sum(NutritionDetail.calories).label('total_calories'),
        func.sum(NutritionDetail.protein).label('total_protein'),
        func.sum(NutritionDetail.fat).label('total_fat'),
        func.sum(NutritionDetail.carbohydrates).label('total_carbohydrates'),
        func.sum(NutritionDetail.dietary_fiber).label('total_fiber'),
        func.sum(NutritionDetail.sodium).label('total_sodium'),
        func.count(FoodRecord.id).label('meal_count')
    ).select_from(FoodRecord).join(
        NutritionDetail, FoodRecord.id == NutritionDetail.food_record_id
    ).filter(
        FoodRecord.user_id == user_id,
        FoodRecord.record_date == summary_date
    ).first()
    
    summary = DailyNutritionSummary(
        user_id=user_id,
        summary_date=summary_date,
        total_calories=nutrition_stats.total_calories or 0,
        total_protein=nutrition_stats.total_protein or 0,
        total_fat=nutrition_stats.total_fat or 0,
        total_carbohydrates=nutrition_stats.total_carbohydrates or 0,
        total_fiber=nutrition_stats.total_fiber or 0,
        total_sodium=nutrition_stats.total_sodium or 0,
        meal_count=nutrition_stats.meal_count or 0,
        water_intake=0,  # 默认值，后续可以从其他地方获取
        exercise_calories=0,  # 默认值，后续可以从运动记录获取
        health_score=None  # 后续计算健康评分
    )
    
    db.add(summary)
    db.commit()
    db.refresh(summary)
    
    return summary


async def update_daily_nutrition_summary(user_id: int, summary_date: date, db: Session):
    """更新每日营养汇总"""
    # 重新计算当天的营养统计
    nutrition_stats = db.query(
        func.sum(NutritionDetail.calories).label('total_calories'),
        func.sum(NutritionDetail.protein).label('total_protein'),
        func.sum(NutritionDetail.fat).label('total_fat'),
        func.sum(NutritionDetail.carbohydrates).label('total_carbohydrates'),
        func.sum(NutritionDetail.dietary_fiber).label('total_fiber'),
        func.sum(NutritionDetail.sodium).label('total_sodium'),
        func.count(FoodRecord.id).label('meal_count')
    ).select_from(FoodRecord).join(
        NutritionDetail, FoodRecord.id == NutritionDetail.food_record_id
    ).filter(
        FoodRecord.user_id == user_id,
        FoodRecord.record_date == summary_date
    ).first()
    
    # 获取或创建汇总记录
    summary = db.query(DailyNutritionSummary).filter(
        DailyNutritionSummary.user_id == user_id,
        DailyNutritionSummary.summary_date == summary_date
    ).first()
    
    if not summary:
        summary = DailyNutritionSummary(
            user_id=user_id,
            summary_date=summary_date
        )
        db.add(summary)
    
    # 更新统计数据
    summary.total_calories = nutrition_stats.total_calories or 0
    summary.total_protein = nutrition_stats.total_protein or 0
    summary.total_fat = nutrition_stats.total_fat or 0
    summary.total_carbohydrates = nutrition_stats.total_carbohydrates or 0
    summary.total_fiber = nutrition_stats.total_fiber or 0
    summary.total_sodium = nutrition_stats.total_sodium or 0
    summary.meal_count = nutrition_stats.meal_count or 0
    summary.updated_at = datetime.utcnow()
    
    db.commit()
    
    # 清除相关缓存
    cache_key = f"nutrition:daily:{user_id}:{summary_date}"
    cache_service.redis.delete(cache_key) 