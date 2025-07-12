# 使用Langgraph构建的Agent的一个例子，（AI不用关注Agent的内部实现）
```python
from langgraph_sdk import get_client
client = get_client(url="http://127.0.0.1:2024")
# 调用营养师Agent进行分析
 # 创建营养师Agent
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

        # 创建线程
        thread = await client.threads.create()

        async for chunk in client.runs.stream(
                assistant_id=assistant["assistant_id"],
                thread_id=thread['thread_id'],
                input={
                    "image_data": image_base64,
                    "user_preferences": user_prefs
                }
        ):
            if chunk.data is not None:
                if chunk.data.get("current_step") == "completed":
                    print("Agent分析完成")
                    return AgentAnalysisData(
                        image_description=chunk.data.get("image_analysis"),
                        nutrition_facts=NutritionFacts(
                            **chunk.data.get("nutrition_analysis")
                        ),
                        recommendations=Recommendations(
                            **chunk.data.get("nutrition_advice")
                        )
                    )
```

## 集成到食物记录API的完整示例

以下是如何使用集成了Agent的食物记录API的完整示例：

### 1. 首先上传图片

```python
import requests
import base64

# 上传图片
files = {'file': open('food_image.jpg', 'rb')}
upload_response = requests.post(
    "http://localhost:8000/foods/upload-image",
    files=files,
    headers={"Authorization": "Bearer YOUR_JWT_TOKEN"}
)
# 使用object_name而不是file_url，更安全
object_name = upload_response.json()["data"]["object_name"]
```

### 2. 创建食物记录（自动调用Agent分析）

```python
from datetime import date

# 创建食物记录，会自动调用Agent分析图片
food_record_data = {
    "record_date": date.today().isoformat(),
    "meal_type": 1,  # 早餐
    "food_name": "早餐",
    "description": "今天的早餐",
    "image_url": object_name,  # 使用对象名，不是完整URL
    "recording_method": 1
}

record_response = requests.post(
    "http://localhost:8000/foods/records",
    json=food_record_data,
    headers={"Authorization": "Bearer YOUR_JWT_TOKEN"}
)

# 响应包含Agent分析结果
result = record_response.json()
print(f"记录ID: {result['data']['id']}")
print(f"分析状态: {result['data']['analysis_status']}")

# 如果有分析结果
if result['data']['analysis_result']:
    analysis = result['data']['analysis_result']['analysis']
    print(f"图片描述: {analysis['image_description']}")
    print(f"营养信息: {analysis['nutrition_facts']}")
    print(f"建议: {analysis['recommendations']}")
```

### 3. 查看详细的营养分析

```python
# 获取食物记录详情（包含营养详情）
record_id = result['data']['id']
detail_response = requests.get(
    f"http://localhost:8000/foods/records/{record_id}",
    headers={"Authorization": "Bearer YOUR_JWT_TOKEN"}
)

detail_result = detail_response.json()
if detail_result['data']['nutrition_detail']:
    nutrition = detail_result['data']['nutrition_detail']
    print(f"卡路里: {nutrition['calories']}")
    print(f"蛋白质: {nutrition['protein']}g")
    print(f"脂肪: {nutrition['fat']}g")
    print(f"碳水化合物: {nutrition['carbohydrates']}g")
```

### 4. 获取图片访问URL（当需要显示图片时）

```python
# 获取图片的访问URL
image_object_name = "food_images/123/1704096000.jpg"  # 从记录中获取
url_response = requests.get(
    "http://localhost:8000/foods/images/url",
    params={
        "object_name": image_object_name,
        "expires_minutes": 60  # URL有效期60分钟
    },
    headers={"Authorization": "Bearer YOUR_JWT_TOKEN"}
)

if url_response.status_code == 200:
    image_data = url_response.json()["data"]
    image_url = image_data["file_url"]
    print(f"图片URL: {image_url}")
    print(f"过期时间: {image_data['expires_at']}")
```

### 5. 获取每日营养汇总

```python
# 获取今日营养汇总
today = date.today()
summary_response = requests.get(
    f"http://localhost:8000/foods/daily-summary/{today.isoformat()}",
    headers={"Authorization": "Bearer YOUR_JWT_TOKEN"}
)

summary_result = summary_response.json()
if summary_result['success']:
    summary = summary_result['data']
    print(f"今日总卡路里: {summary['total_calories']}")
    print(f"今日总蛋白质: {summary['total_protein']}g")
    print(f"今日总脂肪: {summary['total_fat']}g")
    print(f"今日总碳水化合物: {summary['total_carbohydrates']}g")
```

## API响应格式

### 图片上传的响应格式

```json
{
  "success": true,
  "message": "图片上传成功",
  "data": {
    "file_id": "food_images/123/1704096000.jpg",
    "file_name": "breakfast.jpg",
    "file_url": "https://minio.example.com/...",
    "object_name": "food_images/123/1704096000.jpg",
    "file_size": 204800,
    "content_type": "image/jpeg",
    "upload_time": "2024-01-15T08:00:00Z"
  }
}
```

### 创建食物记录的响应格式

```json
{
  "success": true,
  "message": "食物记录创建成功，图片分析已完成",
  "data": {
    "id": 123,
    "user_id": 456,
    "record_date": "2024-01-15",
    "meal_type": 1,
    "food_name": "早餐",
    "description": "今天的早餐",
    "image_url": "food_images/123/1704096000.jpg",
    "recording_method": 1,
    "analysis_status": 3,
    "created_at": "2024-01-15T08:00:00Z",
    "analysis_result": {
      "success": true,
      "analysis": {
        "image_description": "这是一份包含煎蛋、吐司和水果的早餐",
        "nutrition_facts": {
          "calories": 450,
          "protein": 20,
          "fat": 18,
          "carbohydrates": 55,
          "dietary_fiber": 8,
          "sugar": 15,
          "sodium": 380,
          "confidence_score": 0.85
        },
        "recommendations": [
          "这是一份营养均衡的早餐",
          "建议增加一些蔬菜来提高纤维摄入量"
        ]
      }
    }
  }
}
```

### 获取图片URL的响应格式

```json
{
  "success": true,
  "message": "获取图片URL成功",
  "data": {
    "object_name": "food_images/123/1704096000.jpg",
    "file_url": "https://minio.example.com/...",
    "expires_in": 3600,
    "expires_at": "2024-01-15T09:00:00Z"
  }
}
```

## 对话的流式输出

LLM tokens¶
Use the messages-tuple streaming mode to stream Large Language Model (LLM) outputs token by token from any part of your graph, including nodes, tools, subgraphs, or tasks.

The streamed output from messages-tuple mode is a tuple (message_chunk, metadata) where:

message_chunk: the token or message segment from the LLM.
metadata: a dictionary containing details about the graph node and LLM invocation.
Example graph
```python
from dataclasses import dataclass

from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START

@dataclass
class MyState:
    topic: str
    joke: str = ""

llm = init_chat_model(model="openai:gpt-4o-mini")

def call_model(state: MyState):
    """Call the LLM to generate a joke about a topic"""
    llm_response = llm.invoke( 
        [
            {"role": "user", "content": f"Generate a joke about {state.topic}"}
        ]
    )
    return {"joke": llm_response.content}

graph = (
    StateGraph(MyState)
    .add_node(call_model)
    .add_edge(START, "call_model")
    .compile()
)

```

流式输出
```python
async for chunk in client.runs.stream(
    thread_id,
    assistant_id,
    input={"topic": "ice cream"},
    stream_mode="messages-tuple",
):
    if chunk.event != "messages":
        continue

    message_chunk, metadata = chunk.data  
    if message_chunk["content"]:
        print(message_chunk["content"], end="|", flush=True)
```


## 分析状态说明

- `analysis_status = 1`: 待分析
- `analysis_status = 2`: 分析中
- `analysis_status = 3`: 已完成

## 注意事项

1. **Agent服务**: 确保Langgraph Agent服务在 `http://127.0.0.1:2024` 运行
2. **异步处理**: 图片分析可能需要几秒钟时间
3. **错误处理**: 如果Agent分析失败，记录仍会创建但状态为"待分析"
4. **缓存**: 营养汇总会自动缓存以提高性能
5. **图片安全**: 
   - 数据库中存储的是对象名，不是完整URL
   - 需要显示图片时，调用专门的接口获取临时URL
   - 图片URL有过期时间，提高安全性
   - 只能访问自己上传的图片

## 安全性改进

- **对象名存储**: 数据库中不直接存储完整的MinIO URL
- **权限控制**: 只能访问自己上传的图片文件
- **临时URL**: 图片访问URL有过期时间限制
- **路径验证**: 严格验证图片路径格式，防止非法访问