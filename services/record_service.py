from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import date, datetime
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from shared.models.database import get_db
from shared.models import schemas
from shared.config.redis_config import cache_service

app = FastAPI(title="记录服务", version="1.0.0")
security = HTTPBearer()

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "record-service"}

@app.post("/food-records", response_model=schemas.BaseResponse)
async def create_food_record(
    record_data: schemas.FoodRecordCreate,
    background_tasks: BackgroundTasks,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """创建食物记录"""
    try:
        # TODO: 实现创建食物记录逻辑
        # 1. 验证token获取用户ID
        # 2. 保存记录到数据库
        # 3. 异步触发营养分析
        # 4. 更新日汇总
        
        # 模拟保存记录
        saved_record = {
            "id": 1,
            "user_id": 1,  # TODO: 从token获取
            "record_date": record_data.record_date,
            "meal_type": record_data.meal_type,
            "food_name": record_data.food_name,
            "description": record_data.description,
            "recording_method": record_data.recording_method,
            "created_at": datetime.now()
        }
        
        # 异步任务：营养分析和日汇总更新
        background_tasks.add_task(analyze_nutrition_async, saved_record["id"])
        background_tasks.add_task(update_daily_summary_async, saved_record["user_id"], record_data.record_date)
        
        return schemas.BaseResponse(
            success=True,
            message="食物记录创建成功",
            data=saved_record
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"创建食物记录失败: {str(e)}"
        )

@app.get("/food-records", response_model=schemas.BaseResponse)
async def get_food_records(
    date_from: date = None,
    date_to: date = None,
    meal_type: int = None,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """获取食物记录"""
    try:
        # TODO: 实现获取食物记录逻辑
        # 1. 验证token获取用户ID
        # 2. 根据条件查询记录
        # 3. 返回记录列表
        
        # 模拟查询结果
        records = [
            {
                "id": 1,
                "user_id": 1,
                "record_date": "2024-01-01",
                "meal_type": 1,
                "food_name": "苹果",
                "description": "一个中等大小的苹果",
                "image_url": "/food-images/apple_123.jpg",
                "recording_method": 1,
                "created_at": "2024-01-01T08:30:00"
            }
        ]
        
        return schemas.BaseResponse(
            success=True,
            message="获取食物记录成功",
            data=records
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"获取食物记录失败: {str(e)}"
        )

@app.post("/weight-records", response_model=schemas.BaseResponse)
async def create_weight_record(
    weight_data: schemas.WeightRecordCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """记录体重"""
    try:
        # TODO: 实现体重记录逻辑
        # 1. 验证token获取用户ID
        # 2. 计算BMI
        # 3. 保存记录
        # 4. 更新用户资料中的当前体重
        
        # 模拟计算BMI（需要用户身高）
        height_m = 1.75  # TODO: 从用户资料获取身高
        bmi = float(weight_data.weight) / (height_m ** 2)
        
        saved_record = {
            "id": 1,
            "user_id": 1,
            "weight": weight_data.weight,
            "body_fat_percentage": weight_data.body_fat_percentage,
            "muscle_mass": weight_data.muscle_mass,
            "bmi": round(bmi, 2),
            "measured_at": datetime.now(),
            "notes": weight_data.notes,
            "device_type": weight_data.device_type
        }
        
        return schemas.BaseResponse(
            success=True,
            message="体重记录成功",
            data=saved_record
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"体重记录失败: {str(e)}"
        )

@app.get("/daily-summary/{summary_date}", response_model=schemas.BaseResponse)
async def get_daily_summary(
    summary_date: date,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """获取每日营养汇总"""
    try:
        # TODO: 实现获取每日汇总逻辑
        # 1. 验证token获取用户ID
        # 2. 先从缓存查询
        # 3. 缓存未命中则从数据库查询
        # 4. 更新缓存
        
        user_id = 1  # TODO: 从token获取
        
        # 尝试从缓存获取
        cached_summary = await cache_service.get_daily_nutrition(user_id, str(summary_date))
        if cached_summary:
            return schemas.BaseResponse(
                success=True,
                message="获取每日汇总成功（缓存）",
                data=cached_summary
            )
        
        # 模拟从数据库查询
        daily_summary = {
            "id": 1,
            "user_id": user_id,
            "summary_date": summary_date,
            "total_calories": 1800,
            "total_protein": 85.5,
            "total_fat": 65.2,
            "total_carbohydrates": 220.8,
            "total_fiber": 28.5,
            "total_sodium": 1200.0,
            "meal_count": 3,
            "water_intake": 2.5,
            "exercise_calories": 300,
            "health_score": 8.5
        }
        
        # 缓存结果
        await cache_service.cache_daily_nutrition(user_id, str(summary_date), daily_summary)
        
        return schemas.BaseResponse(
            success=True,
            message="获取每日汇总成功",
            data=daily_summary
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"获取每日汇总失败: {str(e)}"
        )

@app.get("/nutrition-trends", response_model=schemas.BaseResponse)
async def get_nutrition_trends(
    days: int = 7,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """获取营养趋势"""
    try:
        # TODO: 实现营养趋势查询逻辑
        user_id = 1  # TODO: 从token获取
        
        # 模拟趋势数据
        trends = {
            "period": f"最近{days}天",
            "daily_data": [
                {
                    "date": "2024-01-01",
                    "calories": 1800,
                    "protein": 85,
                    "health_score": 8.5
                },
                {
                    "date": "2024-01-02",
                    "calories": 1750,
                    "protein": 82,
                    "health_score": 8.2
                }
            ],
            "averages": {
                "calories": 1775,
                "protein": 83.5,
                "health_score": 8.35
            }
        }
        
        return schemas.BaseResponse(
            success=True,
            message="获取营养趋势成功",
            data=trends
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"获取营养趋势失败: {str(e)}"
        )

# 异步任务函数
async def analyze_nutrition_async(record_id: int):
    """异步营养分析"""
    # TODO: 调用AI服务进行营养分析
    print(f"异步分析食物记录 {record_id} 的营养成分")

async def update_daily_summary_async(user_id: int, record_date: date):
    """异步更新日汇总"""
    # TODO: 重新计算当日营养汇总
    print(f"异步更新用户 {user_id} 在 {record_date} 的营养汇总")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 