from fastapi import FastAPI, Depends, HTTPException, status
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

app = FastAPI(title="健康评估服务", version="1.0.0")
security = HTTPBearer()

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "health-service"}

@app.post("/calculate/bmr", response_model=schemas.BaseResponse)
async def calculate_bmr(
    user_data: dict,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """计算基础代谢率"""
    try:
        # TODO: 实现BMR计算逻辑
        # Harris-Benedict公式
        age = user_data.get("age", 25)
        gender = user_data.get("gender", 1)  # 1:男 2:女
        height = user_data.get("height", 175)  # cm
        weight = user_data.get("weight", 70)  # kg
        
        if gender == 1:  # 男性
            bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
        else:  # 女性
            bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
        
        result = {
            "bmr": round(bmr, 2),
            "unit": "大卡/天",
            "formula": "Harris-Benedict公式",
            "note": "基础代谢率是维持基本生理功能所需的最低能量"
        }
        
        return schemas.BaseResponse(
            success=True,
            message="基础代谢率计算成功",
            data=result
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"BMR计算失败: {str(e)}"
        )

@app.post("/calculate/tdee", response_model=schemas.BaseResponse)
async def calculate_tdee(
    user_data: dict,
    activity_level: int,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """计算每日总能量消耗"""
    try:
        # TODO: 实现TDEE计算逻辑
        # 先计算BMR
        bmr_response = await calculate_bmr(user_data, credentials)
        bmr = bmr_response.data["bmr"]
        
        # 活动系数
        activity_multipliers = {
            1: 1.2,    # 久坐
            2: 1.375,  # 轻度活动
            3: 1.55,   # 中度活动
            4: 1.725,  # 重度活动
            5: 1.9     # 超重度活动
        }
        
        multiplier = activity_multipliers.get(activity_level, 1.375)
        tdee = bmr * multiplier
        
        result = {
            "bmr": bmr,
            "activity_level": activity_level,
            "activity_multiplier": multiplier,
            "tdee": round(tdee, 2),
            "unit": "大卡/天",
            "note": "总日能量消耗包括基础代谢和活动消耗"
        }
        
        return schemas.BaseResponse(
            success=True,
            message="TDEE计算成功",
            data=result
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"TDEE计算失败: {str(e)}"
        )

@app.post("/assess/health-score", response_model=schemas.BaseResponse)
async def assess_health_score(
    user_id: int,
    analysis_period: int = 7,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """计算健康评分"""
    try:
        # TODO: 实现健康评分计算逻辑
        # 1. 获取用户最近N天的数据
        # 2. 计算各项指标得分
        # 3. 加权计算总分
        
        # 先检查缓存
        cached_score = await cache_service.get_health_score(user_id)
        if cached_score:
            return schemas.BaseResponse(
                success=True,
                message="获取健康评分成功（缓存）",
                data=cached_score
            )
        
        # 模拟健康评分计算
        scores = {
            "nutrition_balance": 8.5,  # 营养平衡
            "calorie_balance": 7.8,    # 热量平衡
            "food_variety": 8.2,       # 食物多样性
            "meal_regularity": 9.0,    # 用餐规律性
            "hydration": 7.5,          # 水分摄入
            "exercise_correlation": 8.0 # 运动相关性
        }
        
        # 权重
        weights = {
            "nutrition_balance": 0.3,
            "calorie_balance": 0.2,
            "food_variety": 0.15,
            "meal_regularity": 0.15,
            "hydration": 0.1,
            "exercise_correlation": 0.1
        }
        
        # 计算总分
        total_score = sum(scores[key] * weights[key] for key in scores)
        
        result = {
            "user_id": user_id,
            "analysis_period": analysis_period,
            "total_score": round(total_score, 2),
            "max_score": 10.0,
            "component_scores": scores,
            "weights": weights,
            "level": "良好" if total_score >= 8 else "一般" if total_score >= 6 else "需要改善",
            "recommendations": [
                "继续保持良好的饮食习惯",
                "可以增加一些新的食物品种",
                "建议增加饮水量"
            ]
        }
        
        # 缓存结果
        await cache_service.cache_health_score(user_id, result)
        
        return schemas.BaseResponse(
            success=True,
            message="健康评分计算成功",
            data=result
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"健康评分计算失败: {str(e)}"
        )

@app.post("/analyze/nutrition-balance", response_model=schemas.BaseResponse)
async def analyze_nutrition_balance(
    user_id: int,
    analysis_date: date,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """分析营养平衡度"""
    try:
        # TODO: 实现营养平衡分析逻辑
        # 1. 获取当日营养摄入
        # 2. 对比推荐摄入量
        # 3. 计算平衡度
        
        # 模拟营养平衡分析
        analysis = {
            "date": analysis_date,
            "macronutrients": {
                "protein": {
                    "actual": 85.5,
                    "recommended": 80.0,
                    "percentage": 106.9,
                    "status": "充足"
                },
                "fat": {
                    "actual": 65.2,
                    "recommended": 70.0,
                    "percentage": 93.1,
                    "status": "适中"
                },
                "carbohydrates": {
                    "actual": 220.8,
                    "recommended": 250.0,
                    "percentage": 88.3,
                    "status": "稍低"
                }
            },
            "micronutrients": {
                "vitamin_c": {
                    "actual": 85.0,
                    "recommended": 90.0,
                    "percentage": 94.4,
                    "status": "接近推荐量"
                },
                "calcium": {
                    "actual": 650.0,
                    "recommended": 800.0,
                    "percentage": 81.3,
                    "status": "稍低"
                }
            },
            "balance_score": 8.2,
            "recommendations": [
                "可以适当增加碳水化合物摄入",
                "建议多吃富含钙质的食物",
                "整体营养搭配良好"
            ]
        }
        
        return schemas.BaseResponse(
            success=True,
            message="营养平衡分析完成",
            data=analysis
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"营养平衡分析失败: {str(e)}"
        )

@app.get("/recommendations/daily-targets", response_model=schemas.BaseResponse)
async def get_daily_targets(
    user_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """获取每日营养目标"""
    try:
        # TODO: 实现个性化营养目标计算
        # 1. 获取用户基本信息
        # 2. 获取健康目标
        # 3. 考虑疾病和过敏
        # 4. 计算个性化目标
        
        # 模拟个性化目标
        targets = {
            "user_id": user_id,
            "calories": {
                "target": 1800,
                "min": 1600,
                "max": 2000,
                "unit": "大卡"
            },
            "protein": {
                "target": 80,
                "min": 70,
                "max": 90,
                "unit": "克"
            },
            "fat": {
                "target": 70,
                "min": 60,
                "max": 80,
                "unit": "克"
            },
            "carbohydrates": {
                "target": 250,
                "min": 200,
                "max": 300,
                "unit": "克"
            },
            "fiber": {
                "target": 25,
                "min": 20,
                "max": 35,
                "unit": "克"
            },
            "water": {
                "target": 2.5,
                "min": 2.0,
                "max": 3.0,
                "unit": "升"
            },
            "notes": [
                "目标基于您的减重计划制定",
                "建议分3-4餐摄入",
                "如有不适请及时调整"
            ]
        }
        
        return schemas.BaseResponse(
            success=True,
            message="获取每日营养目标成功",
            data=targets
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"获取每日营养目标失败: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 