from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from shared.models import schemas
from shared.config.minio_config import file_storage_service
from shared.config.redis_config import cache_service

app = FastAPI(title="AI分析服务", version="1.0.0")
security = HTTPBearer()

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "ai-service"}

@app.post("/analyze/image", response_model=schemas.BaseResponse)
async def analyze_food_image(
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """食物图片分析"""
    try:
        # TODO: 实现食物图片分析逻辑
        # 1. 验证token获取用户ID
        # 2. 上传图片到MinIO
        # 3. 调用LangGraph Agent进行分析
        # 4. 缓存分析结果
        # 5. 返回分析结果
        
        # 读取文件内容
        file_content = await file.read()
        
        # 模拟上传到MinIO
        upload_result = await file_storage_service.upload_food_image(
            file_data=file_content,
            filename=file.filename,
            user_id=1  # TODO: 从token获取真实用户ID
        )
        
        # 模拟AI分析结果
        analysis_result = {
            "detected_foods": [
                {
                    "name": "苹果",
                    "confidence": 0.95,
                    "portion": "1个中等大小",
                    "weight_grams": 150
                }
            ],
            "nutrition_facts": {
                "calories": 78,
                "protein": 0.4,
                "fat": 0.2,
                "carbohydrates": 20.6,
                "fiber": 2.4,
                "sugar": 15.6
            },
            "health_recommendations": [
                "苹果富含维生素C和纤维，是很好的健康零食",
                "建议在两餐之间食用，有助于控制血糖"
            ],
            "confidence_score": 0.95,
            "analysis_time": "2024-01-01T12:00:00"
        }
        
        return schemas.BaseResponse(
            success=True,
            message="食物分析完成",
            data=analysis_result
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"食物分析失败: {str(e)}"
        )

@app.post("/chat/nutrition", response_model=schemas.BaseResponse)
async def nutrition_chat(
    message: str,
    session_id: str = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """营养咨询对话"""
    try:
        # TODO: 实现营养咨询对话逻辑
        # 1. 验证token获取用户ID
        # 2. 获取或创建对话会话
        # 3. 调用LangGraph Agent进行对话
        # 4. 保存对话记录
        # 5. 返回AI回复
        
        # 模拟AI回复
        ai_response = {
            "session_id": session_id or "new_session_123",
            "message": f"我理解您的问题：{message}。作为您的营养师，我建议...",
            "suggestions": [
                "多吃蔬菜水果",
                "保持规律饮食",
                "适量运动"
            ],
            "follow_up_questions": [
                "您今天还吃了什么其他食物吗？",
                "您的运动习惯如何？"
            ]
        }
        
        return schemas.BaseResponse(
            success=True,
            message="对话成功",
            data=ai_response
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"营养咨询失败: {str(e)}"
        )

@app.post("/recommend/meals", response_model=schemas.BaseResponse)
async def recommend_meals(
    preferences: dict = None,
    health_goals: list = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """个性化膳食推荐"""
    try:
        # TODO: 实现个性化膳食推荐逻辑
        # 1. 验证token获取用户ID
        # 2. 获取用户健康状况和偏好
        # 3. 调用推荐算法
        # 4. 返回推荐结果
        
        # 模拟推荐结果
        recommendations = {
            "breakfast": {
                "name": "燕麦粥配水果",
                "calories": 350,
                "protein": 12,
                "reason": "富含纤维，有助于控制血糖"
            },
            "lunch": {
                "name": "鸡胸肉沙拉",
                "calories": 420,
                "protein": 35,
                "reason": "高蛋白低脂，适合减重目标"
            },
            "dinner": {
                "name": "蒸鱼配蔬菜",
                "calories": 380,
                "protein": 28,
                "reason": "清淡易消化，晚餐理想选择"
            }
        }
        
        return schemas.BaseResponse(
            success=True,
            message="膳食推荐生成成功",
            data=recommendations
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"膳食推荐失败: {str(e)}"
        )

@app.post("/analyze/health-trends", response_model=schemas.BaseResponse)
async def analyze_health_trends(
    user_id: int,
    days: int = 30,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """健康趋势分析"""
    try:
        # TODO: 实现健康趋势分析逻辑
        # 1. 验证权限
        # 2. 获取用户历史数据
        # 3. 进行趋势分析
        # 4. 生成报告
        
        # 模拟趋势分析结果
        trends = {
            "period": f"最近{days}天",
            "calorie_trend": "稳定",
            "weight_trend": "下降",
            "nutrition_balance": {
                "protein": "充足",
                "carbs": "适中",
                "fat": "偏低"
            },
            "recommendations": [
                "继续保持当前饮食习惯",
                "可以适当增加健康脂肪摄入",
                "建议增加运动频率"
            ]
        }
        
        return schemas.BaseResponse(
            success=True,
            message="健康趋势分析完成",
            data=trends
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"健康趋势分析失败: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 