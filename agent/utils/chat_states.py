from typing import Dict, List, Optional, TypedDict, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph import MessagesState, add_messages
from langchain_openai.chat_models.base import BaseChatOpenAI


class ChatState(TypedDict):
    """聊天机器人状态管理"""
    # 输入信息
    user_message: str
    session_id: Optional[str]
    session_type: int  # 1:营养咨询 2:健康评估 3:食物识别 4:运动建议
    user_id: int
    
    # 上下文信息
    conversation_history: Annotated[List[BaseMessage], add_messages]
    user_context: Optional[Dict]  # 用户档案、健康目标等
    recent_meals: Optional[List[Dict]]  # 最近的饮食记录
    health_goals: Optional[Dict]  # 健康目标
    
    # 处理过程
    context_analysis: Optional[str]  # 上下文分析结果
    response_content: str  # 生成的回复内容
    response_metadata: Optional[Dict]  # 回复的元数据
    
    # 控制信息
    current_step: str
    error_message: Optional[str]
    
    # 模型配置
    chat_model: BaseChatOpenAI


class ChatInputState(TypedDict):
    """聊天输入状态"""
    user_message: str
    session_id: Optional[str]
    session_type: int
    user_id: int