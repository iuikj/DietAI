from typing import Optional, List, Dict, TypedDict
from pydantic import BaseModel
from shared.models.schemas import AgentAnalysisData

# 对话Agent的输入状态
class DialogueAgentInput(TypedDict):
    user_id: int
    session_id: int
    food_analysis: AgentAnalysisData  # 与食物分析Agent输出完全一致
    history: Optional[List[Dict]]  # 历史消息
    context: Optional[Dict]        # 其他上下文
    user_input: Optional[str]      # 用户本轮输入

# 对话Agent的输出状态
class DialogueAgentOutput(TypedDict):
    reply: str                     # AI回复内容
    reply_stream: Optional[List[str]]  # SSE流式分段内容
    metadata: Optional[Dict]       # 额外元数据 