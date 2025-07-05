from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Date, Numeric, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from .database import Base


class ConversationSession(Base):
    """对话会话表"""
    __tablename__ = "conversation_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_type = Column(Integer, default=1)  # 1:营养咨询 2:健康评估 3:食物识别 4:运动建议
    langgraph_thread_id = Column(String(100), nullable=True)  # LangGraph线程ID
    title = Column(String(200), nullable=True)
    status = Column(Integer, default=1)  # 1:进行中 2:已结束 3:已暂停
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_message_at = Column(DateTime, nullable=True)
    
    # 关系
    user = relationship("User", back_populates="conversations")
    messages = relationship("ConversationMessage", back_populates="session")
    
    # 索引
    __table_args__ = (
        Index('idx_conversation_sessions_user_id', 'user_id'),
        Index('idx_conversation_sessions_thread_id', 'langgraph_thread_id'),
    )


class ConversationMessage(Base):
    """对话消息表"""
    __tablename__ = "conversation_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("conversation_sessions.id"), nullable=False)
    message_type = Column(Integer, nullable=False)  # 1:用户消息 2:助手消息 3:系统消息
    content = Column(Text, nullable=False)
    message_metadata = Column(JSON, nullable=True)  # 额外的元数据，如图片URL、分析结果等
    created_at = Column(DateTime, default=func.now())
    
    # 关系
    session = relationship("ConversationSession", back_populates="messages")
    
    # 索引
    __table_args__ = (
        Index('idx_conversation_messages_session_id', 'session_id'),
        Index('idx_conversation_messages_created_at', 'created_at'),
    )


class ConversationContext(Base):
    """对话上下文表"""
    __tablename__ = "conversation_contexts"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("conversation_sessions.id"), nullable=False)
    context_type = Column(String(50), nullable=False)  # user_profile, recent_meals, health_goals等
    context_data = Column(JSON, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关系
    session = relationship("ConversationSession")
    
    # 索引
    __table_args__ = (
        Index('idx_conversation_contexts_session_id', 'session_id'),
        Index('idx_conversation_contexts_type', 'context_type'),
    ) 