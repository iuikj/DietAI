"""
拍照分析页面专用聊天接口
在食物分析结果页面集成聊天功能，以分析结果为上下文
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from shared.models.database import get_db
from shared.models import schemas, user_models, conversation_models
from shared.utils.auth import get_current_user
from routers.chat_router import send_chat_message, start_chat_session

router = APIRouter(prefix="/analysis-chat", tags=["分析页面聊天"])


class AnalysisChatRequest(BaseModel):
    """分析页面聊天请求"""
    message: str = Field(..., description="用户消息")
    food_analysis: Dict[str, Any] = Field(..., description="食物分析结果")
    session_id: Optional[int] = Field(None, description="会话ID，如果为空则创建新会话")


class NutritionAnalysisContext(BaseModel):
    """营养分析上下文"""
    food_items: list = Field(default=[], description="识别的食物")
    total_calories: float = Field(default=0.0, description="总热量")
    protein: float = Field(default=0.0, description="蛋白质")
    fat: float = Field(default=0.0, description="脂肪") 
    carbohydrates: float = Field(default=0.0, description="碳水化合物")
    health_score: int = Field(default=5, description="健康评分")


@router.post("/chat-with-analysis", response_model=schemas.BaseResponse)
async def chat_with_food_analysis(
    request: AnalysisChatRequest,
    current_user: user_models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    基于食物分析结果的聊天
    
    功能：
    - 将分析结果作为上下文信息
    - 自动创建或使用现有的营养咨询会话
    - 提供针对当前分析食物的专业建议
    """
    try:
        session_id = request.session_id
        
        # 如果没有会话ID，创建新的营养咨询会话
        if not session_id:
            session_data = schemas.ConversationSessionCreate(
                session_type=1,  # 营养咨询
                title=f"食物分析咨询"
            )
            
            session_response = await start_chat_session(session_data, current_user, db)
            if not session_response.success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="创建会话失败"
                )
            
            session_id = session_response.data["session_id"]
        
        # 构建带有分析结果的消息
        analysis_context = format_analysis_context(request.food_analysis)
        
        enhanced_message = f"""基于刚才的食物分析结果：
{analysis_context}

用户问题：{request.message}

请结合这份分析报告给出专业的营养建议。"""
        
        # 发送消息
        chat_response = await send_chat_message(
            session_id=session_id,
            message=enhanced_message,
            session_type=1,  # 营养咨询
            current_user=current_user,
            db=db
        )
        
        if not chat_response.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=chat_response.message
            )
        
        # 提取并格式化响应
        ai_response = chat_response.data["ai_response"]["content"]
        suggestions = chat_response.data.get("suggestions", [])
        
        # 添加针对分析结果的专门建议
        analysis_suggestions = generate_analysis_suggestions(request.food_analysis)
        all_suggestions = suggestions + analysis_suggestions
        
        return schemas.BaseResponse(
            success=True,
            message="分析咨询成功",
            data={
                "session_id": session_id,
                "ai_response": ai_response,
                "suggestions": all_suggestions[:6],  # 限制建议数量
                "analysis_summary": extract_analysis_summary(request.food_analysis),
                "user_message": request.message,
                "original_message": enhanced_message
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分析咨询失败: {str(e)}"
        )


@router.post("/quick-analysis-chat", response_model=schemas.BaseResponse)
async def quick_analysis_chat(
    analysis_result: Dict[str, Any],
    question: str = "这份分析结果怎么样？",
    current_user: user_models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    快速分析咨询 - 不需要会话管理
    
    适用于分析页面的快速咨询功能
    """
    try:
        # 格式化分析结果
        analysis_context = format_analysis_context(analysis_result)
        
        # 构建完整消息
        full_message = f"""请基于以下食物分析结果回答问题：

{analysis_context}

问题：{question}

请给出简洁专业的建议，重点关注营养价值和健康影响。"""
        
        # 创建临时会话进行咨询
        session_data = schemas.ConversationSessionCreate(
            session_type=1,  # 营养咨询
            title=f"快速分析咨询"
        )
        
        session_response = await start_chat_session(session_data, current_user, db)
        if not session_response.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="创建会话失败"
            )
        
        session_id = session_response.data["session_id"]
        
        # 发送消息获取回复
        chat_response = await send_chat_message(
            session_id=session_id,
            message=full_message,
            session_type=1,
            current_user=current_user,
            db=db
        )
        
        if not chat_response.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=chat_response.message
            )
        
        ai_response = chat_response.data["ai_response"]["content"]
        
        return schemas.BaseResponse(
            success=True,
            message="快速咨询成功",
            data={
                "ai_response": ai_response,
                "analysis_summary": extract_analysis_summary(analysis_result),
                "recommendations": generate_quick_recommendations(analysis_result),
                "session_id": session_id  # 可供后续继续对话
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"快速咨询失败: {str(e)}"
        )


def format_analysis_context(analysis_data: Dict[str, Any]) -> str:
    """格式化分析结果为上下文字符串"""
    try:
        context_parts = []
        
        # 食物识别结果
        if "food_items" in analysis_data:
            food_list = analysis_data["food_items"]
            if isinstance(food_list, list) and food_list:
                context_parts.append(f"识别食物：{', '.join(food_list)}")
        
        # 营养成分
        nutrition_info = []
        if "total_calories" in analysis_data:
            nutrition_info.append(f"总热量：{analysis_data['total_calories']}大卡")
        
        if "macronutrients" in analysis_data:
            macro = analysis_data["macronutrients"]
            if isinstance(macro, dict):
                if "protein" in macro:
                    nutrition_info.append(f"蛋白质：{macro['protein']}g")
                if "fat" in macro:
                    nutrition_info.append(f"脂肪：{macro['fat']}g")
                if "carbohydrates" in macro:
                    nutrition_info.append(f"碳水化合物：{macro['carbohydrates']}g")
        
        if nutrition_info:
            context_parts.append("营养成分：" + "，".join(nutrition_info))
        
        # 健康评分
        if "health_score" in analysis_data:
            context_parts.append(f"健康评分：{analysis_data['health_score']}/10分")
        
        # 维生素矿物质
        if "vitamins_minerals" in analysis_data:
            vm = analysis_data["vitamins_minerals"]
            if isinstance(vm, dict):
                vm_info = []
                for key, value in vm.items():
                    if value:
                        vm_info.append(f"{key}：{value}")
                if vm_info:
                    context_parts.append("维生素矿物质：" + "，".join(vm_info))
        
        return "\n".join(context_parts) if context_parts else "分析结果数据格式异常"
        
    except Exception as e:
        return f"分析结果解析失败：{str(e)}"


def extract_analysis_summary(analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    """提取分析结果摘要"""
    try:
        summary = {}
        
        if "food_items" in analysis_data and analysis_data["food_items"]:
            summary["food_count"] = len(analysis_data["food_items"])
            summary["main_foods"] = analysis_data["food_items"][:3]  # 主要食物
        
        if "total_calories" in analysis_data:
            summary["calories"] = analysis_data["total_calories"]
        
        if "health_score" in analysis_data:
            summary["health_score"] = analysis_data["health_score"]
            summary["health_level"] = get_health_level(analysis_data["health_score"])
        
        return summary
        
    except Exception:
        return {"error": "摘要提取失败"}


def generate_analysis_suggestions(analysis_data: Dict[str, Any]) -> list:
    """基于分析结果生成建议"""
    suggestions = []
    
    try:
        # 基于热量的建议
        if "total_calories" in analysis_data:
            calories = analysis_data["total_calories"]
            if calories > 800:
                suggestions.append("这餐热量较高，建议搭配运动")
            elif calories < 200:
                suggestions.append("热量较低，可以适当增加营养")
        
        # 基于健康评分的建议
        if "health_score" in analysis_data:
            score = analysis_data["health_score"]
            if score >= 8:
                suggestions.append("营养搭配很好，继续保持")
            elif score <= 5:
                suggestions.append("建议优化营养搭配")
        
        # 基于营养成分的建议
        if "macronutrients" in analysis_data:
            macro = analysis_data["macronutrients"]
            if isinstance(macro, dict):
                protein = macro.get("protein", 0)
                if protein < 10:
                    suggestions.append("蛋白质偏低，建议增加")
        
        # 通用建议
        suggestions.extend([
            "查看类似食物的营养对比",
            "获取个性化饮食建议",
            "记录到饮食日记"
        ])
        
        return suggestions[:4]  # 返回前4个建议
        
    except Exception:
        return ["获取营养建议", "查看食物详情"]


def generate_quick_recommendations(analysis_data: Dict[str, Any]) -> list:
    """生成快速推荐"""
    recommendations = []
    
    try:
        if "health_score" in analysis_data:
            score = analysis_data["health_score"]
            if score >= 8:
                recommendations.append("营养均衡，可以适量享用")
            elif score >= 6:
                recommendations.append("整体不错，注意控制分量")
            else:
                recommendations.append("建议搭配更多蔬菜水果")
        
        if "total_calories" in analysis_data:
            calories = analysis_data["total_calories"]
            if calories > 600:
                recommendations.append("热量较高，建议配合运动消耗")
            elif calories < 300:
                recommendations.append("热量适中，可作为加餐选择")
        
        return recommendations
        
    except Exception:
        return ["建议咨询营养师获取专业建议"]


def get_health_level(score: int) -> str:
    """根据健康评分获取等级"""
    if score >= 8:
        return "优秀"
    elif score >= 6:
        return "良好" 
    elif score >= 4:
        return "一般"
    else:
        return "需改善"