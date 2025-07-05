from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional

from shared.models.database import get_db
from shared.models import schemas, user_models, conversation_models
from shared.utils.auth import get_current_user
from shared.config.redis_config import cache_service

router = APIRouter(prefix="/conversations", tags=["对话管理"])


@router.post("/sessions", response_model=schemas.BaseResponse)
def create_conversation_session(
    session_data: schemas.ConversationSessionCreate,
    current_user: user_models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建对话会话"""
    session = conversation_models.ConversationSession(
        user_id=current_user.id,
        session_type=session_data.session_type,
        title=session_data.title,
        status=1  # 进行中
    )
    
    try:
        db.add(session)
        db.commit()
        db.refresh(session)
        
        return schemas.BaseResponse(
            success=True,
            message="对话会话创建成功",
            data={
                "id": session.id,
                "session_type": session.session_type,
                "title": session.title,
                "status": session.status,
                "created_at": session.created_at.isoformat()
            }
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建对话会话失败: {str(e)}"
        )


@router.get("/sessions", response_model=schemas.BaseResponse)
def get_conversation_sessions(
    session_type: Optional[int] = None,
    limit: int = 20,
    current_user: user_models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取对话会话列表"""
    query = db.query(conversation_models.ConversationSession).filter(
        conversation_models.ConversationSession.user_id == current_user.id
    )
    
    if session_type:
        query = query.filter(conversation_models.ConversationSession.session_type == session_type)
    
    sessions = query.order_by(
        conversation_models.ConversationSession.last_message_at.desc().nullslast(),
        conversation_models.ConversationSession.created_at.desc()
    ).limit(limit).all()
    
    sessions_data = []
    for session in sessions:
        # 获取最后一条消息
        last_message = db.query(conversation_models.ConversationMessage).filter(
            conversation_models.ConversationMessage.session_id == session.id
        ).order_by(conversation_models.ConversationMessage.created_at.desc()).first()
        
        session_data = {
            "id": session.id,
            "session_type": session.session_type,
            "session_type_name": get_session_type_name(session.session_type),
            "langgraph_thread_id": session.langgraph_thread_id,
            "title": session.title,
            "status": session.status,
            "status_name": get_session_status_name(session.status),
            "created_at": session.created_at.isoformat(),
            "last_message_at": session.last_message_at.isoformat() if session.last_message_at else None,
            "last_message": {
                "content": last_message.content[:100] + "..." if last_message and len(last_message.content) > 100 else last_message.content if last_message else None,
                "message_type": last_message.message_type if last_message else None,
                "created_at": last_message.created_at.isoformat() if last_message else None
            } if last_message else None
        }
        sessions_data.append(session_data)
    
    return schemas.BaseResponse(
        success=True,
        message="获取对话会话列表成功",
        data=sessions_data
    )


@router.get("/sessions/{session_id}", response_model=schemas.BaseResponse)
def get_conversation_session(
    session_id: int,
    current_user: user_models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取对话会话详情"""
    session = db.query(conversation_models.ConversationSession).filter(
        conversation_models.ConversationSession.id == session_id,
        conversation_models.ConversationSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话会话不存在"
        )
    
    # 获取会话消息
    messages = db.query(conversation_models.ConversationMessage).filter(
        conversation_models.ConversationMessage.session_id == session_id
    ).order_by(conversation_models.ConversationMessage.created_at).all()
    
    messages_data = []
    for message in messages:
        messages_data.append({
            "id": message.id,
            "message_type": message.message_type,
            "message_type_name": get_message_type_name(message.message_type),
            "content": message.content,
            "metadata": message.metadata,
            "created_at": message.created_at.isoformat()
        })
    
    session_data = {
        "id": session.id,
        "session_type": session.session_type,
        "session_type_name": get_session_type_name(session.session_type),
        "langgraph_thread_id": session.langgraph_thread_id,
        "title": session.title,
        "status": session.status,
        "status_name": get_session_status_name(session.status),
        "created_at": session.created_at.isoformat(),
        "last_message_at": session.last_message_at.isoformat() if session.last_message_at else None,
        "messages": messages_data,
        "message_count": len(messages_data)
    }
    
    return schemas.BaseResponse(
        success=True,
        message="获取对话会话详情成功",
        data=session_data
    )


@router.put("/sessions/{session_id}", response_model=schemas.BaseResponse)
def update_conversation_session(
    session_id: int,
    update_data: dict,
    current_user: user_models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新对话会话"""
    session = db.query(conversation_models.ConversationSession).filter(
        conversation_models.ConversationSession.id == session_id,
        conversation_models.ConversationSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话会话不存在"
        )
    
    # 更新字段
    if "title" in update_data:
        session.title = update_data["title"]
    if "status" in update_data:
        session.status = update_data["status"]
    if "langgraph_thread_id" in update_data:
        session.langgraph_thread_id = update_data["langgraph_thread_id"]
    
    session.updated_at = datetime.now()
    
    try:
        db.commit()
        
        return schemas.BaseResponse(
            success=True,
            message="对话会话更新成功"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新对话会话失败: {str(e)}"
        )


@router.post("/sessions/{session_id}/messages", response_model=schemas.BaseResponse)
def create_conversation_message(
    session_id: int,
    message_data: schemas.ConversationMessageCreate,
    current_user: user_models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建对话消息"""
    # 验证会话是否存在且属于当前用户
    session = db.query(conversation_models.ConversationSession).filter(
        conversation_models.ConversationSession.id == session_id,
        conversation_models.ConversationSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话会话不存在"
        )
    
    # 创建消息
    message = conversation_models.ConversationMessage(
        session_id=session_id,
        message_type=message_data.message_type,
        content=message_data.content,
        metadata=message_data.metadata
    )
    
    try:
        db.add(message)
        
        # 更新会话的最后消息时间
        session.last_message_at = datetime.now()
        session.updated_at = datetime.now()
        
        db.commit()
        db.refresh(message)
        
        # 缓存对话上下文（如果是用户消息）
        if message_data.message_type == 1:  # 用户消息
            context_data = {
                "last_user_message": message_data.content,
                "last_message_time": message.created_at.isoformat(),
                "session_type": session.session_type
            }
            cache_service.cache_conversation_context(str(session_id), context_data)
        
        return schemas.BaseResponse(
            success=True,
            message="对话消息创建成功",
            data={
                "id": message.id,
                "session_id": message.session_id,
                "message_type": message.message_type,
                "content": message.content,
                "created_at": message.created_at.isoformat()
            }
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建对话消息失败: {str(e)}"
        )


@router.get("/sessions/{session_id}/messages", response_model=schemas.BaseResponse)
def get_conversation_messages(
    session_id: int,
    limit: int = 50,
    offset: int = 0,
    current_user: user_models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取对话消息列表"""
    # 验证会话是否存在且属于当前用户
    session = db.query(conversation_models.ConversationSession).filter(
        conversation_models.ConversationSession.id == session_id,
        conversation_models.ConversationSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话会话不存在"
        )
    
    # 获取消息
    messages = db.query(conversation_models.ConversationMessage).filter(
        conversation_models.ConversationMessage.session_id == session_id
    ).order_by(
        conversation_models.ConversationMessage.created_at.asc()
    ).offset(offset).limit(limit).all()
    
    messages_data = []
    for message in messages:
        messages_data.append({
            "id": message.id,
            "session_id": message.session_id,
            "message_type": message.message_type,
            "message_type_name": get_message_type_name(message.message_type),
            "content": message.content,
            "metadata": message.metadata,
            "created_at": message.created_at.isoformat()
        })
    
    return schemas.BaseResponse(
        success=True,
        message="获取对话消息列表成功",
        data={
            "messages": messages_data,
            "total_count": len(messages_data),
            "offset": offset,
            "limit": limit
        }
    )


@router.post("/sessions/{session_id}/ai-reply", response_model=schemas.BaseResponse)
def generate_ai_reply(
    session_id: int,
    user_message: str,
    current_user: user_models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """生成AI回复（模拟）"""
    # 验证会话是否存在且属于当前用户
    session = db.query(conversation_models.ConversationSession).filter(
        conversation_models.ConversationSession.id == session_id,
        conversation_models.ConversationSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话会话不存在"
        )
    
    try:
        # 创建用户消息
        user_msg = conversation_models.ConversationMessage(
            session_id=session_id,
            message_type=1,  # 用户消息
            content=user_message
        )
        db.add(user_msg)
        
        # 生成AI回复（这里是模拟，实际应该调用AI服务）
        ai_reply_content = generate_mock_ai_reply(user_message, session.session_type, current_user, db)
        
        # 创建AI回复消息
        ai_msg = conversation_models.ConversationMessage(
            session_id=session_id,
            message_type=2,  # 助手消息
            content=ai_reply_content,
            metadata={"source": "mock_ai", "confidence": 0.85}
        )
        db.add(ai_msg)
        
        # 更新会话信息
        session.last_message_at = datetime.now()
        session.updated_at = datetime.now()
        
        db.commit()
        db.refresh(user_msg)
        db.refresh(ai_msg)
        
        return schemas.BaseResponse(
            success=True,
            message="AI回复生成成功",
            data={
                "user_message": {
                    "id": user_msg.id,
                    "content": user_msg.content,
                    "created_at": user_msg.created_at.isoformat()
                },
                "ai_reply": {
                    "id": ai_msg.id,
                    "content": ai_msg.content,
                    "metadata": ai_msg.metadata,
                    "created_at": ai_msg.created_at.isoformat()
                }
            }
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成AI回复失败: {str(e)}"
        )


@router.delete("/sessions/{session_id}", response_model=schemas.BaseResponse)
def delete_conversation_session(
    session_id: int,
    current_user: user_models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除对话会话"""
    session = db.query(conversation_models.ConversationSession).filter(
        conversation_models.ConversationSession.id == session_id,
        conversation_models.ConversationSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话会话不存在"
        )
    
    try:
        # 删除所有相关消息
        db.query(conversation_models.ConversationMessage).filter(
            conversation_models.ConversationMessage.session_id == session_id
        ).delete()
        
        # 删除会话
        db.delete(session)
        db.commit()
        
        # 清除相关缓存
        cache_service.delete(f"conversation:context:{session_id}")
        
        return schemas.BaseResponse(
            success=True,
            message="对话会话删除成功"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除对话会话失败: {str(e)}"
        )


def get_session_type_name(session_type: int) -> str:
    """获取会话类型名称"""
    session_types = {
        1: "营养咨询",
        2: "健康评估",
        3: "食物识别",
        4: "运动建议"
    }
    return session_types.get(session_type, "未知类型")


def get_session_status_name(status: int) -> str:
    """获取会话状态名称"""
    statuses = {
        1: "进行中",
        2: "已结束",
        3: "已暂停"
    }
    return statuses.get(status, "未知状态")


def get_message_type_name(message_type: int) -> str:
    """获取消息类型名称"""
    message_types = {
        1: "用户消息",
        2: "助手消息",
        3: "系统消息"
    }
    return message_types.get(message_type, "未知类型")


def generate_mock_ai_reply(user_message: str, session_type: int, current_user: user_models.User, db: Session) -> str:
    """生成模拟AI回复"""
    message_lower = user_message.lower()
    
    # 根据会话类型和用户消息内容生成不同的回复
    if session_type == 1:  # 营养咨询
        if any(keyword in message_lower for keyword in ["减肥", "减重", "瘦身"]):
            return "根据您的目标，建议您采用均衡饮食配合适量运动的方式。可以适当减少碳水化合物摄入，增加蛋白质和膳食纤维，每天保持300-500卡路里的热量缺口。具体的营养计划可以根据您的身体状况和运动习惯来制定。"
        elif any(keyword in message_lower for keyword in ["增肌", "增重", "长肌肉"]):
            return "增肌需要充足的蛋白质摄入，建议每公斤体重摄入1.6-2.2g蛋白质，同时保证适量的碳水化合物提供能量。配合规律的力量训练，确保充足的休息和睡眠。可以考虑在训练后30分钟内补充蛋白质。"
        else:
            return "感谢您的咨询！作为您的营养助手，我会根据您的具体情况提供个性化的营养建议。请告诉我更多关于您的饮食目标和当前状况的信息。"
    
    elif session_type == 2:  # 健康评估
        if any(keyword in message_lower for keyword in ["评估", "分析", "健康"]):
            return "基于您最近的饮食记录，我为您进行了健康评估。您的营养平衡度为良好，但建议增加膳食纤维的摄入，可以多吃全谷物、蔬菜和水果。同时注意控制钠的摄入量，建议每日不超过2300mg。"
        else:
            return "我可以帮您分析饮食习惯和营养状况。请上传您的饮食记录或告诉我您想了解的健康指标。"
    
    elif session_type == 3:  # 食物识别
        if any(keyword in message_lower for keyword in ["识别", "这是什么", "营养"]):
            return "请上传食物图片，我将为您识别食物种类并分析营养成分。我可以识别常见的食物，包括水果、蔬菜、主食、肉类等，并提供详细的营养信息。"
        else:
            return "我可以帮您识别食物并分析营养成分。请上传清晰的食物图片。"
    
    elif session_type == 4:  # 运动建议
        if any(keyword in message_lower for keyword in ["运动", "锻炼", "健身"]):
            return "根据您的健康目标，建议您每周进行150分钟中等强度的有氧运动，或75分钟高强度有氧运动，同时每周进行2-3次力量训练。可以从快走、游泳、骑自行车等开始，逐渐增加运动强度。"
        else:
            return "我可以为您制定个性化的运动计划。请告诉我您的运动目标、当前运动习惯和身体状况。"
    
    else:
        return "感谢您的消息！我是您的智能健康助手，可以为您提供营养咨询、健康评估、食物识别和运动建议等服务。请告诉我您需要什么帮助。" 