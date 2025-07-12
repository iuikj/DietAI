import os
from dataclasses import dataclass, fields
from enum import Enum
from typing import Any, Optional

from langchain_core.runnables import RunnableConfig


class VisionModel(Enum):
    QWEN = "qwen"
    OPENAI = "openai"


class AnalysisModel(Enum):
    QWEN = "qwen"
    OPENAI = "openai"


@dataclass(kw_only=True)
class Configuration:
    vision_model_provider: VisionModel = VisionModel.QWEN
    vision_model: str = "qwen-vl-max"
    analysis_model_provider: AnalysisModel = AnalysisModel.QWEN
    analysis_model: str = "qwen3-32b"

    @classmethod
    def from_runnable_config(
            cls, config: Optional[RunnableConfig] = None
    ) -> "Configuration":
        """从RunnableConfig创建Configuration实例"""
        configurable = (
            config["configurable"] if config and "configurable" in config else {}
        )
        values: dict[str, Any] = {
            f.name: os.environ.get(f.name.upper(), configurable.get(f.name))
            for f in fields(cls)
            if f.init
        }
        return cls(**{k: v for k, v in values.items() if v})
