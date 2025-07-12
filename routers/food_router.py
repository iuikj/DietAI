from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
from datetime import datetime, date, timedelta
import base64
import json
from langgraph_sdk import get_client

from shared.models.database import get_db
from shared.models.schemas import (
    BaseResponse, FoodRecordCreate, FoodRecordResponse,
    NutritionDetailCreate, NutritionDetailResponse,
    DailyNutritionSummaryResponse, DateRangeParams,
    PaginationParams, FileUploadResponse, AgentAnalysisData, NutritionFacts, Recommendations
)
from shared.utils.auth import get_current_user
from shared.models.user_models import User
from shared.models.food_models import FoodRecord, NutritionDetail, DailyNutritionSummary, FoodDatabase
from shared.config.redis_config import cache_service
from shared.config.minio_config import minio_client
from shared.config.settings import get_settings

settings = get_settings()

router = APIRouter(prefix="/foods", tags=["食物记录"])


@router.post("/records")
async def create_food_record(
        food_data: FoodRecordCreate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """创建食物记录并使用Agent分析图片（流式输出）"""

    async def generate_sse_stream():
        try:
            # 1. 首先发送创建记录的状态
            yield f"data: {json.dumps({'type': 'record_created', 'data': {'status': 'creating', 'message': '正在创建食物记录...'}, 'success': True}, ensure_ascii=False)}\n\n"

            # 创建食物记录
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

            # 2. 发送记录创建完成的状态
            record_data = {
                "id": food_record.id,
                "user_id": food_record.user_id,
                "record_date": food_record.record_date.isoformat(),
                "meal_type": food_record.meal_type,
                "food_name": food_record.food_name,
                "description": food_record.description,
                "image_url": food_record.image_url,
                "recording_method": food_record.recording_method,
                "analysis_status": food_record.analysis_status,
                "created_at": food_record.created_at.isoformat(),
            }

            yield f"data: {json.dumps({'type': 'record_created', 'data': {'record': record_data, 'status': 'created', 'message': '食物记录创建成功'}, 'success': True}, ensure_ascii=False)}\n\n"

            # 3. 如果有图片URL，则使用Agent进行分析
            if food_data.image_url:
                try:
                    # 设置分析状态为处理中
                    food_record.analysis_status = 2  # 分析中
                    db.commit()

                    yield f"data: {json.dumps({'type': 'analysis_started', 'data': {'status': 'analyzing', 'message': '开始分析图片...'}, 'success': True}, ensure_ascii=False)}\n\n"

                # 使用Agent分析图片
                analysis_result: AgentAnalysisData = await analyze_food_image_with_agent(food_data.image_url,
                                                                                         current_user)

                    # 如果有营养分析结果，创建营养详情记录
                    if analysis_complete_data:
                        nutrition_facts = NutritionFacts(**analysis_complete_data["nutrition_facts"])
                        await create_nutrition_detail_from_analysis(
                            food_record.id,
                            nutrition_facts,
                            db
                        )

                        # 更新分析状态为完成
                        food_record.analysis_status = 3  # 已完成
                        db.commit()

                        # 触发每日营养汇总更新
                        await update_daily_nutrition_summary(current_user.id, food_data.record_date, db)

                        yield f"data: {json.dumps({'type': 'nutrition_saved', 'data': {'status': 'completed', 'message': '营养分析完成并已保存'}, 'success': True}, ensure_ascii=False)}\n\n"
                    else:
                        # 如果分析失败，设置为待分析
                        food_record.analysis_status = 1  # 待分析
                        db.commit()
                        yield f"data: {json.dumps({'type': 'analysis_failed', 'data': {'status': 'failed', 'message': '分析失败，请稍后重试'}, 'success': False}, ensure_ascii=False)}\n\n"

            except Exception as e:
                # 分析出错，设置为待分析状态
                food_record.analysis_status = 1  # 待分析
                db.commit()
                print(f"Agent分析失败: {str(e)}")
                yield f"data: {json.dumps({'type': 'analysis_failed', 'data': {'status': 'failed', 'message': f'分析失败: {str(e)}'}, 'success': False}, ensure_ascii=False)}\n\n"
            # 清除相关缓存
            cache_key = f"nutrition:daily:{current_user.id}:{food_data.record_date}"
            cache_service.redis.delete(cache_key)

            # 5. 发送完成信号
            yield f"data: {json.dumps({'type': 'stream_complete', 'data': {'status': 'completed', 'message': '流程完成'}, 'success': True}, ensure_ascii=False)}\n\n"

            except Exception as e:
                db.rollback()
                yield f"data: {json.dumps({'type': 'error', 'data': {'error': str(e), 'message': f'创建食物记录失败: {str(e)}'}, 'success': False}, ensure_ascii=False)}\n\n"

            return StreamingResponse(
                generate_sse_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "*",
                }
            )


@router.post("/records/traditional", response_model=BaseResponse)
async def create_food_record_traditional(
        food_data: FoodRecordCreate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """创建食物记录（传统接口，不使用流式输出）"""
    try:
        # 创建食物记录
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

        # 如果有图片URL，异步启动分析（不等待完成）
        if food_data.image_url:
            try:
                # 设置分析状态为处理中
                food_record.analysis_status = 2  # 分析中
                db.commit()

                # 异步分析（在后台进行）
                import asyncio
                from concurrent.futures import ThreadPoolExecutor

                def background_analysis():
                    asyncio.run(_run_background_analysis(food_data.image_url, current_user, food_record.id))

                executor = ThreadPoolExecutor(max_workers=1)
                executor.submit(background_analysis)

            except Exception as e:
                print(f"启动后台分析失败: {str(e)}")
                # 分析启动失败，但记录已创建成功

        # 清除相关缓存
        cache_key = f"nutrition:daily:{current_user.id}:{food_data.record_date}"
        cache_service.redis.delete(cache_key)

        # 构建响应数据
        response_data = {
            "id": food_record.id,
            "user_id": food_record.user_id,
            "record_date": food_record.record_date.isoformat(),
            "meal_type": food_record.meal_type,
            "food_name": food_record.food_name,
            "description": food_record.description,
            "image_url": food_record.image_url,
            "recording_method": food_record.recording_method,
            "analysis_status": food_record.analysis_status,
            "created_at": food_record.created_at.isoformat(),
            "analysis_result": analysis_result  # 包含Agent分析结果
        }

        return BaseResponse(
            success=True,
            message="食物记录创建成功，图片正在后台分析",
            data=response_data
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建食物记录失败: {str(e)}"
        )


async def _run_background_analysis(image_url: str, current_user: User, food_record_id: int):
    """后台运行图片分析"""
    try:
        from shared.models.database import get_db

        # 获取数据库会话
        db_gen = get_db()
        db = next(db_gen)

        try:
            # 获取食物记录
            food_record = db.query(FoodRecord).filter(FoodRecord.id == food_record_id).first()
            if not food_record:
                print(f"食物记录不存在: {food_record_id}")
                return

            # 运行分析
            analysis_complete_data = None
            async for chunk in analyze_food_image_with_agent(image_url, current_user):
                if chunk["type"] == "analysis_complete":
                    analysis_complete_data = chunk["data"]
                    break
                elif chunk["type"] == "error":
                    print(f"Agent分析失败: {chunk['data']}")
                    break

            # 如果有营养分析结果，创建营养详情记录
            if analysis_complete_data:
                nutrition_facts = NutritionFacts(**analysis_complete_data["nutrition_facts"])
                await create_nutrition_detail_from_analysis(
                    food_record.id,
                    nutrition_facts,
                    db
                )

                # 更新分析状态为完成
                food_record.analysis_status = 3  # 已完成
                db.commit()

                # 触发每日营养汇总更新
                await update_daily_nutrition_summary(current_user.id, food_record.record_date, db)
            else:
                # 分析失败
                food_record.analysis_status = 1  # 待分析
                db.commit()

        finally:
            db.close()

    except Exception as e:
        print(f"后台分析失败: {str(e)}")


@router.post("/records/confirm/{record_id}", response_model=BaseResponse)
async def confirm_food_record(
        record_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """确认食物记录创建完成"""
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
                "analysis_method": nutrition_detail.analysis_method
            }

        return BaseResponse(
            success=True,
            message="食物记录确认完成",
            data=record_data
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"确认食物记录失败: {str(e)}"
        )


async def analyze_food_image_with_agent(image_url: str, current_user: User,db: Session):
    """使用Langgraph Agent分析食物图片（流式输出）"""

    try:
        # 初始化Langgraph客户端
        # client = get_client(url="http://127.0.0.1:2024")
        client = get_client(url=settings.ai_service_url)
        # 从MinIO获取图片数据并转换为base64
        image_base64 = await get_image_base64_from_url(image_url)


        user_prefs = await get_user_preferences(db, current_user.id)

        # 创建营养师Agent
        assistant = await client.assistants.create(
            graph_id="nutrition_agent",
            config={
                "configurable": {
                    "vision_model_provider": "openai",
                    "vision_model": "gpt-4.1-nano-2025-04-14",
                    "analysis_model_provider": "openai",
                    "analysis_model": "o3-mini-2025-01-31"
                }
            }
        )

        # 创建线程
        thread = await client.threads.create()
        async for chunk in client.runs.stream(
                assistant_id=assistant["assistant_id"],
                thread_id=thread['thread_id'],
                input={
                    "image_data": image_base64,
                    "user_preferences": user_prefs
                }
        ):
            if chunk.data is not None:
                if chunk.data.get("current_step") == "completed":
                    print("Agent分析完成")
                    yield {
                        "type": "analysis_complete",
                        "data": {
                            "image_description": chunk.data.get("image_analysis"),
                            "nutrition_facts": chunk.data.get("nutrition_analysis"),
                            "recommendations": chunk.data.get("nutrition_advice")
                        }
                    }
                else:
                    yield {
                        "type": "analysis_progress",
                        "data": {
                            "current_step": chunk.data.get("current_step")
                        }
                    }
    except Exception as e:
        print(f"Agent分析失败: {str(e)}")
        yield {
            "type": "error",
            "data": {
                "error": str(e)
            }
        }
        raise e


async def get_user_preferences(db: Session, user_id: int):
    try:
        user = db.query(User).filter(user_id == User.id).first()
        if not user:
            return {
                "dietary_restrictions": [],
                "health_goals": [],
                "language": "zh-CN"
            }
        # 饮食限制
        dietary_restrictions = []
        if user.allergies:
            dietary_restrictions.extend([
                {
                    "allergen_name": allergy.allergen_name,
                    "severity_level": allergy.severity_level,
                    "reaction_description": allergy.reaction_description,
                    "created_at": allergy.created_at.isoformat() if allergy.created_at else None,
                    "updated_at": allergy.updated_at.isoformat() if allergy.updated_at else None
                }
                for allergy in user.allergies
            ])
        # 处理疾病信息
        if user.diseases:
            dietary_restrictions.extend([
                {
                    "disease_name": disease.disease_name,
                    "severity_level": disease.severity_level,
                    "diagnosed_date": disease.diagnosed_date.isoformat() if disease.diagnosed_date else None,
                    "is_current": disease.is_current,
                    "notes": disease.notes,
                    "created_at": disease.created_at.isoformat() if disease.created_at else None,
                    "updated_at": disease.updated_at.isoformat() if disease.updated_at else None
                }
                for disease in user.diseases
            ])
        # 健康目标
        health_goals = []
        if user.health_goals:
            health_goals.extend([
                {
                    "goal_type": goal.goal_type,  # 1:减重 2:增重 3:维持 4:增肌 5:减脂
                    "target_weight": float(goal.target_weight) if goal.target_weight is not None else None,
                    "target_date": goal.target_date.isoformat() if goal.target_date else None,
                    "current_status": goal.current_status,  # 1:进行中 2:已完成 3:已暂停 4:已取消
                    "created_at": goal.created_at.isoformat() if goal.created_at else None,
                    "updated_at": goal.updated_at.isoformat() if goal.updated_at else None,
                }
                for goal in user.health_goals])
            health_goals.extend([{"goal_type_mean:": "1:减重 2:增重 3:维持 4:增肌 5:减脂",
                                  "current_status_mean": "1:进行中 2:已完成 3:已暂停 4:已取消"}])

        language = "zh-CN"

        return {
            "dietary_restrictions": dietary_restrictions,
            "health_goals": health_goals,
            "language": language
        }

    except Exception as e:
        print(f"获取用户偏好失败: {e}")

        # 返回一个默认偏好，防止后续逻辑出错
        return {
            "dietary_restrictions": [],
            "health_goals": [],
            "language": "zh-CN"
        }


async def get_image_base64_from_url(image_identifier: str) -> str:
    """从图片标识符获取base64编码的图片数据"""
    try:
        # 判断是URL还是对象名
        if image_identifier.startswith('http'):
            # 如果是完整的URL，需要正确提取对象名
            from urllib.parse import urlparse, unquote

            parsed_url = urlparse(image_identifier)
            # 获取路径部分并移除bucket名称
            path_parts = parsed_url.path.strip('/').split('/')
            if len(path_parts) >= 2:
                # 移除bucket名称，保留对象路径
                object_name = '/'.join(path_parts[1:])
            else:
                # 如果路径格式不正确，尝试从最后一部分提取
                object_name = path_parts[-1] if path_parts else parsed_url.path.split('/')[-1]

            # URL解码
            object_name = unquote(object_name)
        else:
            # 如果是对象名或路径，直接使用
            object_name = image_identifier

        print(f"尝试获取对象: {object_name}")

        # 获取图片数据
        image_data = minio_client.download_file(object_name)

        if image_data is None:
            raise Exception(f"无法从MinIO获取图片数据: {object_name}")

        # 转换为base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')

        return image_base64

    except Exception as e:
        print(f"获取图片数据失败: {str(e)}")
        raise e


async def create_nutrition_detail_from_analysis(food_record_id: int, nutrition_facts: NutritionFacts, db: Session):
    """根据Agent分析结果创建营养详情记录"""
    try:
        # 检查是否已有营养详情
        existing_detail = db.query(NutritionDetail).filter(
            NutritionDetail.food_record_id == food_record_id
        ).first()

        if existing_detail:
            return  # 如果已存在，则不创建

        # 从分析结果中提取营养信息
        nutrition_detail = NutritionDetail(
            food_record_id=food_record_id,
            calories=nutrition_facts.total_calories or 0,
            protein=nutrition_facts.macronutrients.protein or 0,
            fat=nutrition_facts.macronutrients.fat or 0,
            carbohydrates=nutrition_facts.macronutrients.carbohydrates or 0,
            # dietary_fiber=0,  #TODO:Agent忘写膳食纤维了(下面同理) 已完成
            # sugar=0,
            # sodium=0,
            # cholesterol=0,
            dietary_fiber=nutrition_facts.macronutrients.dietary_fiber or 0,
            sugar=nutrition_facts.macronutrients.sugar or 0,
            # 微量营养素
            sodium=nutrition_facts.vitamins_minerals.sodium or 0,
            cholesterol=nutrition_facts.vitamins_minerals.cholesterol or 0,

            # 维生素
            vitamin_a=nutrition_facts.vitamins_minerals.vitamin_a or 0,
            vitamin_c=nutrition_facts.vitamins_minerals.vitamin_c or 0,
            vitamin_d=nutrition_facts.vitamins_minerals.vitamin_d or 0,

            # 矿物质
            calcium=nutrition_facts.vitamins_minerals.calcium or 0,
            iron=nutrition_facts.vitamins_minerals.iron or 0,
            potassium=nutrition_facts.vitamins_minerals.potassium or 0,
            # vitamin_a=nutrition_facts.vitamins_minerals.vitamin_a or 0,
            # vitamin_c=nutrition_facts.vitamins_minerals.vitamin_c or 0,
            # vitamin_d=0,
            # calcium=nutrition_facts.vitamins_minerals.calcium or 0,
            # iron=0,
            # potassium=0,
            # confidence_score=0,#TODO:confidence_score还未实现
            analysis_method="agent_analysis"
        )

        try:
            db.add(nutrition_detail)
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"添加数据库失败: {str(e)}")
            raise e

    except Exception as e:
        print(f"创建营养详情失败: {str(e)}")
        raise e


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
        query = db.query(FoodRecord).filter(current_user.id == FoodRecord.user_id)

        if start_date:
            query = query.filter(FoodRecord.record_date >= start_date)
        if end_date:
            query = query.filter(FoodRecord.record_date <= end_date)
        if meal_type:
            query = query.filter(meal_type == FoodRecord.meal_type)

        # 总数统计
        total = query.count()

        # 分页查询
        offset = (page - 1) * page_size
        records = query.order_by(FoodRecord.record_date.desc(), FoodRecord.created_at.desc()).offset(offset).limit(
            page_size).all()

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
                "confidence_score": float(
                    nutrition_detail.confidence_score) if nutrition_detail.confidence_score else None,
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
                "confidence_score": float(
                    nutrition_detail.confidence_score) if nutrition_detail.confidence_score else None,
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
                "object_name": object_name,  # 用于存储到数据库
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


@router.get("/images/url", response_model=BaseResponse)
async def get_image_url(
        object_name: str = Query(..., description="对象名称"),
        current_user: User = Depends(get_current_user),
        expires_minutes: int = Query(60, ge=1, le=10080, description="URL有效期(分钟)")
):
    """获取图片的访问URL"""
    try:
        # 验证对象名格式（确保是该用户的图片）
        if not object_name.startswith(f"food_images/{current_user.id}/"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问该图片"
            )

        # 检查文件是否存在
        if not minio_client.file_exists(object_name):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="图片不存在"
            )

        # 生成预签名URL
        from datetime import timedelta
        expires = timedelta(minutes=expires_minutes)
        file_url = minio_client.get_file_url(object_name, expires)

        if not file_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="生成图片URL失败"
            )

        return BaseResponse(
            success=True,
            message="获取图片URL成功",
            data={
                "object_name": object_name,
                "file_url": file_url,
                "expires_in": expires_minutes * 60,  # 转换为秒
                "expires_at": (datetime.utcnow() + expires).isoformat()
            }
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取图片URL失败: {str(e)}"
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
