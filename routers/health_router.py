from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime, date, timedelta
import math

from shared.models.database import get_db
from shared.models.schemas import (
    BaseResponse, HealthAnalysisRequest, HealthAnalysisResponse,
    DateRangeParams
)
from shared.utils.auth import get_current_user
from shared.models.user_models import User, UserProfile, HealthGoal, WeightRecord
from shared.models.food_models import DailyNutritionSummary
from shared.config.redis_config import cache_service

router = APIRouter(prefix="/health", tags=["健康分析"])


@router.post("/analysis", response_model=BaseResponse)
async def health_analysis(
    analysis_request: HealthAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """健康分析"""
    try:
        analysis_type = analysis_request.analysis_type
        
        if analysis_type == "bmr":
            result = await calculate_bmr(current_user.id, db)
        elif analysis_type == "tdee":
            result = await calculate_tdee(current_user.id, db)
        elif analysis_type == "nutrition_balance":
            result = await analyze_nutrition_balance(
                current_user.id, 
                analysis_request.date_range,
                db
            )
        elif analysis_type == "health_score":
            result = await calculate_health_score(
                current_user.id,
                analysis_request.date_range,
                db
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不支持的分析类型"
            )
        
        return BaseResponse(
            success=True,
            message="健康分析完成",
            data={
                "analysis_type": analysis_type,
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"健康分析失败: {str(e)}"
        )


@router.get("/bmr", response_model=BaseResponse)
async def get_bmr(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """计算基础代谢率(BMR)"""
    try:
        # 先尝试从缓存获取
        cached_bmr = cache_service.get_health_score(current_user.id)
        if cached_bmr and "bmr" in cached_bmr:
            return BaseResponse(
                success=True,
                message="获取BMR成功",
                data=cached_bmr["bmr"]
            )
        
        result = await calculate_bmr(current_user.id, db)
        
        return BaseResponse(
            success=True,
            message="BMR计算完成",
            data=result
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"BMR计算失败: {str(e)}"
        )


@router.get("/tdee", response_model=BaseResponse)
async def get_tdee(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """计算每日总能量消耗(TDEE)"""
    try:
        result = await calculate_tdee(current_user.id, db)
        
        return BaseResponse(
            success=True,
            message="TDEE计算完成",
            data=result
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"TDEE计算失败: {str(e)}"
        )


@router.get("/nutrition-balance", response_model=BaseResponse)
async def get_nutrition_balance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期")
):
    """营养平衡分析"""
    try:
        date_range = {}
        if start_date:
            date_range["start_date"] = start_date.isoformat()
        if end_date:
            date_range["end_date"] = end_date.isoformat()
        
        result = await analyze_nutrition_balance(current_user.id, date_range, db)
        
        return BaseResponse(
            success=True,
            message="营养平衡分析完成",
            data=result
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"营养平衡分析失败: {str(e)}"
        )


@router.get("/health-score", response_model=BaseResponse)
async def get_health_score(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期")
):
    """健康评分"""
    try:
        date_range = {}
        if start_date:
            date_range["start_date"] = start_date.isoformat()
        if end_date:
            date_range["end_date"] = end_date.isoformat()
        
        result = await calculate_health_score(current_user.id, date_range, db)
        
        return BaseResponse(
            success=True,
            message="健康评分完成",
            data=result
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"健康评分失败: {str(e)}"
        )


@router.get("/weight-trend", response_model=BaseResponse)
async def get_weight_trend(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = Query(30, description="天数", ge=7, le=365)
):
    """体重趋势分析"""
    try:
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # 获取体重记录
        weight_records = db.query(WeightRecord).filter(
            WeightRecord.user_id == current_user.id,
            WeightRecord.measured_at >= start_date,
            WeightRecord.measured_at <= end_date
        ).order_by(WeightRecord.measured_at).all()
        
        if not weight_records:
            return BaseResponse(
                success=True,
                message="暂无体重数据",
                data={
                    "trend": "stable",
                    "weight_change": 0,
                    "weight_change_percentage": 0,
                    "records": [],
                    "analysis": "暂无足够的体重数据进行趋势分析"
                }
            )
        
        # 计算趋势
        first_weight = weight_records[0].weight
        last_weight = weight_records[-1].weight
        weight_change = float(last_weight - first_weight)
        weight_change_percentage = (weight_change / float(first_weight)) * 100
        
        # 趋势判断
        if abs(weight_change_percentage) < 2:
            trend = "stable"
            trend_description = "体重保持稳定"
        elif weight_change_percentage > 0:
            trend = "increasing"
            trend_description = "体重呈上升趋势"
        else:
            trend = "decreasing"
            trend_description = "体重呈下降趋势"
        
        # 格式化记录数据
        records_data = []
        for record in weight_records:
            records_data.append({
                "date": record.measured_at.date().isoformat(),
                "weight": float(record.weight),
                "bmi": float(record.bmi) if record.bmi else None,
                "body_fat_percentage": float(record.body_fat_percentage) if record.body_fat_percentage else None
            })
        
        # 生成分析建议
        analysis = trend_description
        if trend == "increasing" and weight_change_percentage > 5:
            analysis += "，建议关注饮食控制和增加运动"
        elif trend == "decreasing" and weight_change_percentage < -10:
            analysis += "，注意营养均衡，避免过度减重"
        
        return BaseResponse(
            success=True,
            message="体重趋势分析完成",
            data={
                "trend": trend,
                "weight_change": round(weight_change, 2),
                "weight_change_percentage": round(weight_change_percentage, 2),
                "records": records_data,
                "analysis": analysis,
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": days
                }
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"体重趋势分析失败: {str(e)}"
        )


# 辅助函数
async def calculate_bmr(user_id: int, db: Session) -> Dict[str, Any]:
    """计算基础代谢率"""
    # 获取用户资料
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile or not profile.weight or not profile.height or not profile.gender or not profile.birth_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="缺少必要的用户资料信息（体重、身高、性别、出生日期）"
        )
    
    # 计算年龄
    today = date.today()
    age = today.year - profile.birth_date.year - ((today.month, today.day) < (profile.birth_date.month, profile.birth_date.day))
    
    weight = float(profile.weight)
    height = float(profile.height)
    
    # 使用Mifflin-St Jeor方程计算BMR
    if profile.gender == 1:  # 男性
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:  # 女性
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    
    return {
        "bmr": round(bmr, 1),
        "unit": "kcal/day",
        "method": "Mifflin-St Jeor方程",
        "user_data": {
            "weight": weight,
            "height": height,
            "age": age,
            "gender": "男" if profile.gender == 1 else "女"
        },
        "description": "基础代谢率是维持基本生理功能所需的最少能量"
    }


async def calculate_tdee(user_id: int, db: Session) -> Dict[str, Any]:
    """计算每日总能量消耗"""
    # 先计算BMR
    bmr_result = await calculate_bmr(user_id, db)
    bmr = bmr_result["bmr"]
    
    # 获取活动水平
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    activity_level = profile.activity_level if profile else 2
    
    # 活动系数
    activity_factors = {
        1: 1.2,   # 久坐
        2: 1.375, # 轻度活动
        3: 1.55,  # 中度活动
        4: 1.725, # 重度活动
        5: 1.9    # 超重度活动
    }
    
    activity_descriptions = {
        1: "久坐（很少或无运动）",
        2: "轻度活动（轻松运动/每周1-3天）",
        3: "中度活动（中等运动/每周3-5天）",
        4: "重度活动（剧烈运动/每周6-7天）",
        5: "超重度活动（极剧烈运动/体力劳动）"
    }
    
    factor = activity_factors.get(activity_level, 1.375)
    tdee = bmr * factor
    
    return {
        "tdee": round(tdee, 1),
        "bmr": bmr,
        "activity_level": activity_level,
        "activity_factor": factor,
        "activity_description": activity_descriptions.get(activity_level, "轻度活动"),
        "unit": "kcal/day",
        "description": "每日总能量消耗包括基础代谢和活动消耗"
    }


async def analyze_nutrition_balance(user_id: int, date_range: Dict[str, str], db: Session) -> Dict[str, Any]:
    """营养平衡分析"""
    # 设置日期范围
    if date_range.get("end_date"):
        end_date = datetime.fromisoformat(date_range["end_date"]).date()
    else:
        end_date = date.today()
    
    if date_range.get("start_date"):
        start_date = datetime.fromisoformat(date_range["start_date"]).date()
    else:
        start_date = end_date - timedelta(days=7)
    
    # 获取营养汇总数据
    summaries = db.query(DailyNutritionSummary).filter(
        DailyNutritionSummary.user_id == user_id,
        DailyNutritionSummary.summary_date >= start_date,
        DailyNutritionSummary.summary_date <= end_date
    ).all()
    
    if not summaries:
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "analysis": "暂无营养数据",
            "recommendations": ["请记录饮食以获得营养分析"]
        }
    
    # 计算平均值
    total_days = len(summaries)
    avg_calories = sum(float(s.total_calories) for s in summaries) / total_days
    avg_protein = sum(float(s.total_protein) for s in summaries) / total_days
    avg_fat = sum(float(s.total_fat) for s in summaries) / total_days
    avg_carbs = sum(float(s.total_carbohydrates) for s in summaries) / total_days
    avg_fiber = sum(float(s.total_fiber) for s in summaries) / total_days
    avg_sodium = sum(float(s.total_sodium) for s in summaries) / total_days
    
    # 计算TDEE作为参考
    tdee_result = await calculate_tdee(user_id, db)
    recommended_calories = tdee_result["tdee"]
    
    # 营养素比例分析
    protein_calories = avg_protein * 4
    fat_calories = avg_fat * 9
    carb_calories = avg_carbs * 4
    total_macro_calories = protein_calories + fat_calories + carb_calories
    
    if total_macro_calories > 0:
        protein_percentage = (protein_calories / total_macro_calories) * 100
        fat_percentage = (fat_calories / total_macro_calories) * 100
        carb_percentage = (carb_calories / total_macro_calories) * 100
    else:
        protein_percentage = fat_percentage = carb_percentage = 0
    
    # 生成建议
    recommendations = []
    
    # 热量分析
    calorie_ratio = avg_calories / recommended_calories
    if calorie_ratio < 0.8:
        recommendations.append("热量摄入偏低，建议适量增加")
    elif calorie_ratio > 1.2:
        recommendations.append("热量摄入偏高，建议适量减少")
    
    # 蛋白质分析
    if protein_percentage < 10:
        recommendations.append("蛋白质摄入不足，建议增加优质蛋白质")
    elif protein_percentage > 35:
        recommendations.append("蛋白质摄入过多，建议适量减少")
    
    # 脂肪分析
    if fat_percentage < 20:
        recommendations.append("脂肪摄入偏低，建议适量增加健康脂肪")
    elif fat_percentage > 35:
        recommendations.append("脂肪摄入过多，建议减少饱和脂肪")
    
    # 碳水化合物分析
    if carb_percentage < 45:
        recommendations.append("碳水化合物摄入偏低，建议增加复合碳水")
    elif carb_percentage > 65:
        recommendations.append("碳水化合物摄入过多，建议适量减少")
    
    # 膳食纤维分析
    if avg_fiber < 25:
        recommendations.append("膳食纤维摄入不足，建议多吃蔬菜水果")
    
    # 钠摄入分析
    if avg_sodium > 2300:
        recommendations.append("钠摄入过多，建议减少盐分摄入")
    
    if not recommendations:
        recommendations.append("营养平衡良好，请继续保持")
    
    return {
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "days": total_days
        },
        "averages": {
            "calories": round(avg_calories, 1),
            "protein": round(avg_protein, 1),
            "fat": round(avg_fat, 1),
            "carbohydrates": round(avg_carbs, 1),
            "fiber": round(avg_fiber, 1),
            "sodium": round(avg_sodium, 1)
        },
        "percentages": {
            "protein": round(protein_percentage, 1),
            "fat": round(fat_percentage, 1),
            "carbohydrates": round(carb_percentage, 1)
        },
        "reference": {
            "recommended_calories": round(recommended_calories, 1),
            "calorie_ratio": round(calorie_ratio, 2)
        },
        "recommendations": recommendations
    }


async def calculate_health_score(user_id: int, date_range: Dict[str, str], db: Session) -> Dict[str, Any]:
    """计算健康评分"""
    # 设置日期范围
    if date_range.get("end_date"):
        end_date = datetime.fromisoformat(date_range["end_date"]).date()
    else:
        end_date = date.today()
    
    if date_range.get("start_date"):
        start_date = datetime.fromisoformat(date_range["start_date"]).date()
    else:
        start_date = end_date - timedelta(days=7)
    
    score_components = {}
    total_score = 0
    max_score = 0
    
    # 营养平衡评分 (40分)
    nutrition_analysis = await analyze_nutrition_balance(user_id, date_range, db)
    if "averages" in nutrition_analysis:
        nutrition_score = calculate_nutrition_score(nutrition_analysis)
        score_components["nutrition"] = {
            "score": nutrition_score,
            "max_score": 40,
            "description": "营养平衡"
        }
        total_score += nutrition_score
    max_score += 40
    
    # BMI评分 (20分)
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if profile and profile.bmi:
        bmi_score = calculate_bmi_score(float(profile.bmi))
        score_components["bmi"] = {
            "score": bmi_score,
            "max_score": 20,
            "description": "体重指数"
        }
        total_score += bmi_score
    max_score += 20
    
    # 饮食规律性评分 (20分)
    summaries = db.query(DailyNutritionSummary).filter(
        DailyNutritionSummary.user_id == user_id,
        DailyNutritionSummary.summary_date >= start_date,
        DailyNutritionSummary.summary_date <= end_date
    ).all()
    
    if summaries:
        regularity_score = calculate_diet_regularity_score(summaries)
        score_components["regularity"] = {
            "score": regularity_score,
            "max_score": 20,
            "description": "饮食规律性"
        }
        total_score += regularity_score
    max_score += 20
    
    # 水分摄入评分 (10分)
    if summaries:
        avg_water = sum(float(s.water_intake) for s in summaries) / len(summaries)
        water_score = calculate_water_score(avg_water)
        score_components["water"] = {
            "score": water_score,
            "max_score": 10,
            "description": "水分摄入"
        }
        total_score += water_score
    max_score += 10
    
    # 运动评分 (10分)
    if summaries:
        avg_exercise = sum(float(s.exercise_calories) for s in summaries) / len(summaries)
        exercise_score = calculate_exercise_score(avg_exercise)
        score_components["exercise"] = {
            "score": exercise_score,
            "max_score": 10,
            "description": "运动消耗"
        }
        total_score += exercise_score
    max_score += 10
    
    # 计算总分百分比
    final_score = (total_score / max_score * 100) if max_score > 0 else 0
    
    # 生成等级和建议
    if final_score >= 90:
        grade = "优秀"
        suggestions = ["继续保持良好的饮食习惯"]
    elif final_score >= 80:
        grade = "良好"
        suggestions = ["整体表现不错，可以在薄弱环节进一步改善"]
    elif final_score >= 70:
        grade = "一般"
        suggestions = ["需要关注营养平衡和饮食规律"]
    elif final_score >= 60:
        grade = "较差"
        suggestions = ["建议调整饮食结构，增加运动"]
    else:
        grade = "很差"
        suggestions = ["强烈建议咨询营养师，制定健康饮食计划"]
    
    return {
        "total_score": round(final_score, 1),
        "grade": grade,
        "components": score_components,
        "suggestions": suggestions,
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
    }


def calculate_nutrition_score(nutrition_analysis: Dict[str, Any]) -> float:
    """计算营养评分"""
    score = 0
    
    # 热量平衡 (15分)
    calorie_ratio = nutrition_analysis["reference"]["calorie_ratio"]
    if 0.9 <= calorie_ratio <= 1.1:
        score += 15
    elif 0.8 <= calorie_ratio <= 1.2:
        score += 10
    elif 0.7 <= calorie_ratio <= 1.3:
        score += 5
    
    # 蛋白质比例 (10分)
    protein_pct = nutrition_analysis["percentages"]["protein"]
    if 15 <= protein_pct <= 25:
        score += 10
    elif 10 <= protein_pct <= 30:
        score += 7
    elif 8 <= protein_pct <= 35:
        score += 4
    
    # 脂肪比例 (10分)
    fat_pct = nutrition_analysis["percentages"]["fat"]
    if 25 <= fat_pct <= 30:
        score += 10
    elif 20 <= fat_pct <= 35:
        score += 7
    elif 15 <= fat_pct <= 40:
        score += 4
    
    # 膳食纤维 (5分)
    fiber = nutrition_analysis["averages"]["fiber"]
    if fiber >= 25:
        score += 5
    elif fiber >= 20:
        score += 3
    elif fiber >= 15:
        score += 1
    
    return score


def calculate_bmi_score(bmi: float) -> float:
    """计算BMI评分"""
    if 18.5 <= bmi <= 24.9:
        return 20
    elif 17.0 <= bmi <= 27.9:
        return 15
    elif 16.0 <= bmi <= 29.9:
        return 10
    elif 15.0 <= bmi <= 34.9:
        return 5
    else:
        return 0


def calculate_diet_regularity_score(summaries) -> float:
    """计算饮食规律性评分"""
    if not summaries:
        return 0
    
    # 计算每日餐次的标准差
    meal_counts = [s.meal_count for s in summaries]
    avg_meals = sum(meal_counts) / len(meal_counts)
    
    if avg_meals >= 3:
        base_score = 15
    elif avg_meals >= 2:
        base_score = 10
    else:
        base_score = 5
    
    # 规律性加分
    if len(set(meal_counts)) <= 2:  # 餐次变化不大
        base_score += 5
    
    return min(base_score, 20)


def calculate_water_score(water_intake: float) -> float:
    """计算水分摄入评分"""
    if water_intake >= 2.0:
        return 10
    elif water_intake >= 1.5:
        return 7
    elif water_intake >= 1.0:
        return 4
    elif water_intake >= 0.5:
        return 2
    else:
        return 0


def calculate_exercise_score(exercise_calories: float) -> float:
    """计算运动评分"""
    if exercise_calories >= 300:
        return 10
    elif exercise_calories >= 200:
        return 7
    elif exercise_calories >= 100:
        return 4
    elif exercise_calories >= 50:
        return 2
    else:
        return 0 