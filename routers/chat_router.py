"""
LangGraph 聊天 Agent 路由
集成聊天机器人功能，支持与后端对话系统的完整交互
"""

from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, Dict, Any, List, AsyncGenerator
from langgraph_sdk import get_client
import asyncio
import json

from shared.models.database import get_db
from shared.models import schemas, user_models, conversation_models
from shared.utils.auth import get_current_user
from shared.config.redis_config import cache_service

router = APIRouter(prefix="/chat", tags=["AI对话"])



@router.post("/send-message-stream")
async def send_chat_message_stream(
    session_id: Optional[int] = None,
    message: str = "",
    session_type: int = 1,
    current_user: user_models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """发送聊天消息并返回流式响应"""
    
    async def generate_response() -> AsyncGenerator[str, None]:
        try:
            # 1. 处理会话
            session = None
            if session_id:
                # 验证已存在的会话
                session = db.query(conversation_models.ConversationSession).filter(
                    conversation_models.ConversationSession.id == session_id,
                    conversation_models.ConversationSession.user_id == current_user.id
                ).first()
                
                if not session:
                    yield f"data: {json.dumps({'error': '对话会话不存在'})}\n\n"
                    return
            else:
                # 创建新会话
                session = conversation_models.ConversationSession(
                    user_id=current_user.id,
                    session_type=session_type,
                    title=f"对话 - {datetime.now().strftime('%Y%m%d %H:%M')}",
                    status=1
                )
                db.add(session)
                db.commit()
                db.refresh(session)
            
            # 发送会话信息
            yield f"data: {json.dumps({'type': 'session', 'data': {'session_id': session.id}})}\n\n"
            
            # 2. 创建用户消息记录
            user_message = conversation_models.ConversationMessage(
                session_id=session.id,
                message_type=1,  # 用户消息
                content=message
            )
            db.add(user_message)
            db.commit()
            db.refresh(user_message)
            
            # 3. 获取用户上下文数据
            user_context = await get_user_context(current_user.id, db)
            recent_meals = await get_recent_meals(current_user.id, db)
            health_goals = await get_health_goals(current_user.id, db)
            conversation_history = await get_conversation_history(session.id, db)
            
            # 4. 调用 LangGraph Agent
            client = get_client(url="http://127.0.0.1:2024")
            
            # 创建或获取 LangGraph thread
            if not session.langgraph_thread_id:
                thread = await client.threads.create()
                session.langgraph_thread_id = thread['thread_id']
                db.commit()
            
            # 创建助手（如果需要）
            assistant = await client.assistants.create(
                graph_id="chat_agent",
                config={
                    "configurable": {
                        "analysis_model_provider": "openai",
                        "analysis_model": "gpt-4o-mini"
                    }
                }
            )
            
            # 5. 流式运行聊天 Agent
            yield f"data: {json.dumps({'type': 'status', 'message': '正在生成回复...'})}\n\n"
            
            full_response = ""
            
            async for chunk in client.runs.stream(
                assistant_id=assistant["assistant_id"],
                thread_id=session.langgraph_thread_id,
                input={
                    "user_message": message,
                    "session_id": str(session.id),
                    "session_type": session_type,
                    "user_id": current_user.id,
                    "user_context": user_context,
                    "recent_meals": recent_meals,
                    "health_goals": health_goals,
                    "conversation_history": conversation_history
                },
                stream_mode="messages-tuple"
            ):
                if chunk.event != "messages":
                    continue
                
                message_chunk, metadata = chunk.data
                print(message_chunk)
                # 检查是否有内容
                if message_chunk.get("content") and message_chunk.get("type")=="AIMessageChunk":
                    content = message_chunk["content"]
                    full_response += content
                    
                    # 流式输出内容
                    yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
            
            # 6. 创建AI回复消息记录
            ai_message = conversation_models.ConversationMessage(
                session_id=session.id,
                message_type=2,  # 助手消息
                content=full_response,
                message_metadata={
                    "stream_generated": True,
                    "assistant_id": assistant["assistant_id"]
                }
            )
            db.add(ai_message)
            
            # 7. 更新会话信息
            session.last_message_at = datetime.now()
            session.updated_at = datetime.now()
            
            db.commit()
            db.refresh(ai_message)
            
            # 8. 缓存对话上下文
            context_data = {
                "last_user_message": message,
                "last_ai_response": full_response,
                "last_message_time": ai_message.created_at.isoformat(),
                "session_type": session.session_type
            }
            cache_service.cache_conversation_context(str(session.id), context_data)
            
            # 发送完成信号
            yield f"data: {json.dumps({'type': 'complete', 'message_id': ai_message.id})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': f'发送消息失败: {str(e)}'})}\n\n"
    
    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )


@router.post("/send-message", response_model=schemas.BaseResponse)
async def send_chat_message(
    session_id: Optional[int] = None,
    message: str = "",
    session_type: int = 1,
    current_user: user_models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """发送聊天消息并获取AI回复"""
    
    try:
        # 1. 处理会话
        if session_id:
            # 验证已存在的会话
            session = db.query(conversation_models.ConversationSession).filter(
                conversation_models.ConversationSession.id == session_id,
                conversation_models.ConversationSession.user_id == current_user.id
            ).first()
            
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="对话会话不存在"
                )
        else:
            # 创建新会话
            session = conversation_models.ConversationSession(
                user_id=current_user.id,
                session_type=session_type,
                title=f"对话 - {datetime.now().strftime('%Y%m%d %H:%M')}",
                status=1
            )
            db.add(session)
            db.commit()
            db.refresh(session)
        
        # 2. 创建用户消息记录
        user_message = conversation_models.ConversationMessage(
            session_id=session.id,
            message_type=1,  # 用户消息
            content=message
        )
        db.add(user_message)
        
        # 3. 获取用户上下文数据
        user_context = await get_user_context(current_user.id, db)
        recent_meals = await get_recent_meals(current_user.id, db)
        health_goals = await get_health_goals(current_user.id, db)
        conversation_history = await get_conversation_history(session.id, db)
        
        # 4. 调用 LangGraph Agent
        client = get_client(url="http://127.0.0.1:2024")
        
        # 创建或获取 LangGraph thread
        if not session.langgraph_thread_id:
            thread = await client.threads.create()
            session.langgraph_thread_id = thread['thread_id']
            db.commit()
        
        # 创建助手（如果需要）
        assistant = await client.assistants.create(
            graph_id="chat_agent",
            config={
                "configurable": {
                    "analysis_model_provider": "openai",
                    "analysis_model": "gpt-4o-mini"
                }
            }
        )
        
        # 运行聊天 Agent (非流式版本，兼容现有API)
        full_response = ""
        metadata = {}
        suggestions = []
        
        async for chunk in client.runs.stream(
            assistant_id=assistant["assistant_id"],
            thread_id=session.langgraph_thread_id,
            input={
                "user_message": message,
                "session_id": str(session.id),
                "session_type": session_type,
                "user_id": current_user.id,
                "user_context": user_context,
                "recent_meals": recent_meals,
                "health_goals": health_goals,
                "conversation_history": conversation_history
            },
            stream_mode="messages-tuple"
        ):
            if chunk.event != "messages":
                continue
            
            message_chunk, chunk_metadata = chunk.data
            
            # 累积完整响应
            if message_chunk.get("content"):
                full_response += message_chunk["content"]
                
            # 保存元数据
            if chunk_metadata:
                metadata.update(chunk_metadata)
        
        # 5. 获取AI回复
        ai_response = full_response if full_response else '抱歉，我现在无法回复您的消息。'
        
        # 6. 创建AI回复消息记录
        ai_message = conversation_models.ConversationMessage(
            session_id=session.id,
            message_type=2,  # 助手消息
            content=ai_response,
            message_metadata={
                **metadata,
                "suggestions": suggestions,
                # "langgraph_run_id": run.get('run_id')
            }
        )
        db.add(ai_message)
        
        # 7. 更新会话信息
        session.last_message_at = datetime.now()
        session.updated_at = datetime.now()
        
        db.commit()
        db.refresh(user_message)
        db.refresh(ai_message)
        
        # 8. 缓存对话上下文
        context_data = {
            "last_user_message": message,
            "last_ai_response": ai_response,
            "last_message_time": ai_message.created_at.isoformat(),
            "session_type": session.session_type
        }
        cache_service.cache_conversation_context(str(session.id), context_data)
        
        return schemas.BaseResponse(
            success=True,
            message="消息发送成功",
            data={
                "session_id": session.id,
                "langgraph_thread_id": session.langgraph_thread_id,
                "user_message": {
                    "id": user_message.id,
                    "content": user_message.content,
                    "created_at": user_message.created_at.isoformat()
                },
                "ai_response": {
                    "id": ai_message.id,
                    "content": ai_message.content,
                    "metadata": ai_message.message_metadata,
                    "created_at": ai_message.created_at.isoformat()
                },
                "suggestions": suggestions
            }
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发送消息失败: {str(e)}"
        )


@router.post("/start-session", response_model=schemas.BaseResponse)
async def start_chat_session(
    session_data: schemas.ConversationSessionCreate,
    current_user: user_models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """开始新的聊天会话"""
    
    try:
        # 创建新会话
        session = conversation_models.ConversationSession(
            user_id=current_user.id,
            session_type=session_data.session_type,
            title=session_data.title or f"对话 - {datetime.now().strftime('%Y%m%d %H:%M')}",
            status=1
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        # 创建 LangGraph thread
        client = get_client(url="http://127.0.0.1:2024")
        thread = await client.threads.create()
        
        # 更新会话的 LangGraph thread ID
        session.langgraph_thread_id = thread['thread_id']
        db.commit()
        
        return schemas.BaseResponse(
            success=True,
            message="聊天会话创建成功",
            data={
                "session_id": session.id,
                "langgraph_thread_id": session.langgraph_thread_id,
                "session_type": session.session_type,
                "title": session.title,
                "created_at": session.created_at.isoformat()
            }
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建聊天会话失败: {str(e)}"
        )


@router.get("/sessions/{session_id}/context", response_model=schemas.BaseResponse)
async def get_session_context(
    session_id: int,
    current_user: user_models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取会话上下文信息"""
    
    # 验证会话权限
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
        # 获取上下文数据
        user_context = await get_user_context(current_user.id, db)
        recent_meals = await get_recent_meals(current_user.id, db)
        health_goals = await get_health_goals(current_user.id, db)
        
        # 获取缓存的对话上下文
        cached_context = cache_service.get_conversation_context(str(session_id))
        
        return schemas.BaseResponse(
            success=True,
            message="获取会话上下文成功",
            data={
                "session_id": session_id,
                "user_context": user_context,
                "recent_meals": recent_meals,
                "health_goals": health_goals,
                "cached_context": cached_context
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取会话上下文失败: {str(e)}"
        )


# 辅助函数
async def get_user_context(user_id: int, db: Session) -> Dict[str, Any]:
    """获取用户上下文信息"""
    user = db.query(user_models.User).filter(user_models.User.id == user_id).first()
    if not user:
        return {}
    
    # 获取用户档案信息
    user_profile = db.query(user_models.UserProfile).filter(
        user_models.UserProfile.user_id == user_id
    ).first()
    
    context = {
        "username": user.username,
        # "age": user_profile.age if user_profile else None,
        "gender": user_profile.gender if user_profile else None,
        "height": float(user_profile.height) if user_profile and user_profile.height else None,
        "weight": float(user_profile.weight) if user_profile and user_profile.weight else None,
        "activity_level": user_profile.activity_level if user_profile else None
    }
    
    return {k: v for k, v in context.items() if v is not None}


async def get_recent_meals(user_id: int, db: Session, limit: int = 5) -> List[Dict[str, Any]]:
    """获取最近的饮食记录"""
    try:
        from shared.models.food_models import FoodRecord
        
        recent_records = db.query(FoodRecord).filter(
            FoodRecord.user_id == user_id
        ).order_by(FoodRecord.record_date.desc(), FoodRecord.created_at.desc()).limit(limit).all()
        
        meals = []
        for record in recent_records:
            meal_data = {
                "food_name": record.food_name,
                "meal_type": record.meal_type,
                "record_date": record.record_date.isoformat(),
            }
            
            # 安全地处理nutrition_detail中的decimal字段
            if record.nutrition_detail:
                if hasattr(record.nutrition_detail, 'calories') and record.nutrition_detail.calories is not None:
                    meal_data["calories"] = float(record.nutrition_detail.calories)
                    
            meals.append(meal_data)
        
        return meals
    except Exception as e:
        # 如果表不存在或其他错误，返回空列表
        print(f"Error getting recent meals: {e}")
        return []


async def get_health_goals(user_id: int, db: Session) -> Dict[str, Any]:
    """获取健康目标"""
    try:
        from shared.models.user_models import HealthGoal
        
        goals = db.query(HealthGoal).filter(
            HealthGoal.user_id == user_id,
            HealthGoal.status == 1  # 活跃状态
        ).first()
        
        if not goals:
            return {}
        
        result = {}
        
        # 安全地转换 decimal 字段
        if hasattr(goals, 'goal_type') and goals.goal_type is not None:
            result["goal_type"] = goals.goal_type
            
        if hasattr(goals, 'target_weight') and goals.target_weight is not None:
            result["target_weight"] = float(goals.target_weight)
            
        if hasattr(goals, 'target_body_fat') and goals.target_body_fat is not None:
            result["target_body_fat"] = float(goals.target_body_fat)
            
        if hasattr(goals, 'daily_calorie_target') and goals.daily_calorie_target is not None:
            result["daily_calorie_target"] = int(goals.daily_calorie_target)
            
        if hasattr(goals, 'target_date') and goals.target_date is not None:
            result["target_date"] = goals.target_date.isoformat()
        
        return result
        
    except Exception as e:
        # 如果表不存在或其他错误，返回空字典
        print(f"Error getting health goals: {e}")
        return {}


async def get_conversation_history(session_id: int, db: Session, limit: int = 10) -> List[Dict[str, Any]]:
    """获取对话历史"""
    messages = db.query(conversation_models.ConversationMessage).filter(
        conversation_models.ConversationMessage.session_id == session_id
    ).order_by(conversation_models.ConversationMessage.created_at.asc()).limit(limit).all()
    
    history = []
    for msg in messages:
        history.append({
            "role": "user" if msg.message_type == 1 else "assistant",
            "content": msg.content,
            "timestamp": msg.created_at.isoformat()
        })
    
    return history


@router.get("/sessions", response_model=schemas.BaseResponse)
async def get_chat_sessions(
        session_type: Optional[int] = None,
        limit: int = 10,
        current_user: user_models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """获取用户的聊天会话列表 - 前端专用"""
    try:
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

            sessions_data.append({
                "id": session.id,
                "title": session.title,
                "session_type": session.session_type,
                "session_type_name": get_session_type_name(session.session_type),
                "last_message": last_message.content[:50] + "..." if last_message and len(
                    last_message.content) > 50 else last_message.content if last_message else "暂无消息",
                "last_message_time": session.last_message_at.isoformat() if session.last_message_at else session.created_at.isoformat(),
                "message_count": db.query(conversation_models.ConversationMessage).filter(
                    conversation_models.ConversationMessage.session_id == session.id
                ).count()
            })

        return schemas.BaseResponse(
            success=True,
            message="获取会话列表成功",
            data=sessions_data
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取会话列表失败: {str(e)}"
        )


@router.get("/sessions/{session_id}/messages", response_model=schemas.BaseResponse)
async def get_session_messages(
        session_id: int,
        limit: int = 50,
        current_user: user_models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """获取会话消息历史 - 前端专用"""
    try:
        # 验证会话权限
        session = db.query(conversation_models.ConversationSession).filter(
            conversation_models.ConversationSession.id == session_id,
            conversation_models.ConversationSession.user_id == current_user.id
        ).first()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )

        # 获取消息
        messages = db.query(conversation_models.ConversationMessage).filter(
            conversation_models.ConversationMessage.session_id == session_id
        ).order_by(conversation_models.ConversationMessage.created_at.asc()).limit(limit).all()

        messages_data = []
        for msg in messages:
            messages_data.append({
                "id": msg.id,
                "role": "user" if msg.message_type == 1 else "assistant",
                "content": msg.content,
                "timestamp": msg.created_at.isoformat(),
                "metadata": msg.message_metadata
            })

        return schemas.BaseResponse(
            success=True,
            message="获取消息历史成功",
            data={
                "session_id": session_id,
                "session_title": session.title,
                "session_type": session.session_type,
                "messages": messages_data
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取消息历史失败: {str(e)}"
        )


@router.delete("/sessions/{session_id}", response_model=schemas.BaseResponse)
async def delete_session(
        session_id: int,
        current_user: user_models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """删除聊天会话 - 前端专用"""
    try:
        # 验证会话权限
        session = db.query(conversation_models.ConversationSession).filter(
            conversation_models.ConversationSession.id == session_id,
            conversation_models.ConversationSession.user_id == current_user.id
        ).first()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )

        # 删除所有消息
        db.query(conversation_models.ConversationMessage).filter(
            conversation_models.ConversationMessage.session_id == session_id
        ).delete()

        # 删除会话
        db.delete(session)
        db.commit()

        return schemas.BaseResponse(
            success=True,
            message="会话删除成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除会话失败: {str(e)}"
        )


def get_session_type_name(session_type: int) -> str:
    """获取会话类型名称"""
    session_types = {
        1: "营养咨询",
        2: "健康评估",
        3: "食物识别",
        4: "运动建议"
    }
    return session_types.get(session_type, "通用咨询")