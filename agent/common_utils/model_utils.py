

import os
from functools import lru_cache

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_anthropic import ChatAnthropic
from langchain_community.chat_models import ChatTongyi

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_qwq import ChatQwQ, ChatQwen

from agent.utils.configuration import *


@lru_cache(maxsize=4)
def get_model(model_provider: Enum, model_name: str):
    load_dotenv(f".env", override=True)
    print(f"环境变量加载+++++++++++++++++++{os.getenv("OPENAI_API_KEY")}")
    match model_provider:
        # case "groq":
        #     return ChatGroq(model_name=model_name)
        case "anthropic":
            return ChatAnthropic(model_name=model_name)
        case "openai":
            return ChatOpenAI(model_name=model_name,streaming=False)
        case "deepseek":
            # 注意这里的deepseek是硅基流动的
            return init_chat_model(model_name)
        case "qwen":
            return ChatQwen(
                model="qwen3-32b",
                model_kwargs={
                    "enable_thinking": True,
                    },
                streaming=True
                )

        # case "yuanjing":
        #     if "qwen" in model_name:
        #         print("ChatQWQ")
        #         return ChatQwQ(
        #             model=model_name,
        #             streaming=False,
        #             api_key=access_token,
        #             api_base="https://maas-api.ai-yuanjing.com/openapi/compatible-mode/v1"
        #         )
        #     else:
        #         print("ChatOpenAI")
        #         return ChatOpenAI(
        #         api_key=access_token,
        #         base_url="https://maas-api.ai-yuanjing.com/openapi/compatible-mode/v1",
        #         model=model_name
        #     )
        case _:
            raise ValueError(f"Unsupported model type: {model_provider}")