from typing import Dict, List
from enum import IntEnum
from pydantic import BaseModel, Field

class ChatResponse(BaseModel):
    """聊天机器人响应结构"""
    success: bool = Field(description="是否成功")
    response_content: str = Field(description="回复内容")
    session_id: str = Field(description="会话ID")
    session_type: int = Field(description="会话类型")
    metadata: Dict = Field(description="元数据信息")
    suggestions: List[str] = Field(description="建议操作列表")