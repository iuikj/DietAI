# 使用Langgraph构建的Agent的一个例子，（AI不用关注Agent的内部实现）
```python
from langgraph_sdk import get_client
client = get_client(url="http://127.0.0.1:2024")
# 调用营养师Agent进行分析
assistant = await client.assistants.create(
    graph_id="nutrition_agent",
    config={
        "configurable": {
            "vision_model_provider": "openai",
            "vision_model": "gpt-4.1-nano-2025-04-14",
            "analysis_model_provider": "openai",
            "analysis_model": "o3-mini-2025-01-31"
        }
    }
)
thread = await client.threads.create()
run = await client.runs.create(
    assistant_id=assistant["assistant_id"],
    thread_id=thread['thread_id'],
    input={
        "image_data": image_base64,
        "user_preferences": user_prefs
    }
)
print("Processing...")
while True:
    result = await client.threads.get_state(thread["thread_id"])
    current_step = result.get('values').get("current_step")
    print(f"Current step: {current_step}")
    if result.get('values').get("error_message") is not None:
        print(result.get('values').get("error_message"))
        raise HTTPException(status_code=500, detail=result["error_message"])
    if current_step == "completed":
        print(json.dumps(result,indent=2))
        break
# result = await client.threads.get_state(thread["thread_id"])
print(result
result=result.get("values"
# 格式化返回结果
response = {
    "success": True,
    "filename": file.filename,
    "analysis": {
        "image_description": result["image_analysis"],
        "nutrition_facts": result["nutrition_analysis"] if result["nutrition_analysis"] else None,
        "recommendations": result["nutrition_advice"] if result["nutrition_advice"] else None
    },
    "processing_step": result["current_step"]
}
```