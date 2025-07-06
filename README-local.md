# DietAI - 智能饮食健康管理系统

## 📋 项目概述

DietAI 是一个基于人工智能的智能饮食健康管理系统，通过多模态AI技术为用户提供个性化的营养分析、健康建议和饮食管理服务。系统集成了图像识别、自然语言处理、知识图谱等先进技术，为用户打造全方位的健康管理体验。

### 🎯 项目愿景

- **智能化**：基于多模态AI分析食物营养成分，提供精准的健康评估
- **个性化**：根据用户健康状况、疾病史、过敏信息等提供定制化建议
- **交互式**：支持对话式AI助手，提供渐进式指导和长期记忆管理
- **全面性**：从食物记录到营养分析，从健康评估到个性化建议的完整闭环

## ✨ 核心功能

### 🔍 智能食物识别
- 📸 **图像识别**：上传食物图片，AI自动识别食物类型和营养成分
- 🗣️ **语音输入**：支持语音描述食物，智能转换为营养数据
- 📱 **条码扫描**：扫描食品包装条码，快速获取营养信息
- ✍️ **手动输入**：支持手动录入食物信息

### 🧠 AI健康助手
- 💬 **对话式AI**：基于LangGraph的智能对话系统
- 🎯 **个性化建议**：根据用户健康状况提供定制化饮食建议
- 📊 **营养分析**：详细的营养成分分析和健康评分
- 🔄 **长期记忆**：AI助手具备长期记忆能力，提供连贯的健康指导

### 👤 用户健康管理
- 📝 **健康档案**：完整的用户健康信息管理
- 🎯 **目标设定**：支持减重、增重、增肌、减脂等多种健康目标
- 🏥 **疾病管理**：针对特定疾病的饮食建议和监控
- 🚫 **过敏管理**：过敏原识别和避免建议

### 📈 数据分析与报告
- 📊 **营养统计**：每日、每周、每月的营养摄入统计
- 📈 **趋势分析**：体重、健康指标变化趋势
- 📋 **健康报告**：定期生成个人健康分析报告
- 🏆 **目标追踪**：健康目标完成情况监控

## 🏗️ 技术架构

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        前端层                                │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │   Web端     │ │   移动端     │ │   管理端     │            │
│  │   (Vue3)    │ │  (UniApp)   │ │  (React)    │            │
│  └─────────────┘ └─────────────┘ └─────────────┘            │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      API网关层                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              FastAPI + Nginx                            │ │
│  │         (路由分发、认证、限流、CORS)                        │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                       业务服务层                             │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│ │  用户服务     │ │   AI分析服务  │ │   记录服务    │           │
│ │ (FastAPI)    │ │ (LangGraph)  │ │ (FastAPI)    │           │
│ └──────────────┘ └──────────────┘ └──────────────┘           │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│ │  健康评估服务 │ │   AI助手服务  │ │   通知服务    │           │
│ │ (FastAPI)    │ │ (LangChain)  │ │ (FastAPI)    │           │
│ └──────────────┘ └──────────────┘ └──────────────┘           │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      数据存储层                              │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│ │ PostgreSQL   │ │    Redis     │ │    MinIO     │           │
│ │  (主数据库)   │ │   (缓存)     │ │  (文件存储)   │           │
│ └──────────────┘ └──────────────┘ └──────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

### 🛠️ 技术栈

#### 后端技术
- **Web框架**：FastAPI 0.110+ - 高性能异步API框架
- **ORM**：SQLAlchemy 2.0+ - 现代Python ORM
- **数据库**：PostgreSQL 15+ - 企业级关系型数据库
- **缓存**：Redis 7+ - 高性能内存数据库
- **文件存储**：MinIO - 兼容S3的对象存储
- **认证**：JWT + OAuth2 - 安全认证体系

#### AI技术栈
- **AI框架**：LangGraph 0.3+ - 状态管理的AI Agent框架
- **LLM集成**：LangChain 0.3+ - 多模型集成框架
- **支持模型**：
  - OpenAI GPT-4/GPT-3.5
  - Anthropic Claude 3
  - 阿里通义千问
  - 自定义模型接入
- **向量数据库**：支持多种向量存储方案

#### 前端技术
- **Web端**：Vue 3 + TypeScript + Vite
- **移动端**：UniApp + Vue 3 (支持多平台)
- **UI组件**：Element Plus / Uni-UI
- **状态管理**：Pinia
- **HTTP客户端**：Axios

#### 基础设施
- **容器化**：Docker + Docker Compose
- **进程管理**：Uvicorn + Gunicorn
- **反向代理**：Nginx
- **监控**：Prometheus + Grafana
- **日志**：ELK Stack

## 🚀 快速开始

### 环境要求

- Python 3.12+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+

### 安装步骤

#### 1. 克隆项目
```bash
git clone https://github.com/your-username/DietAI.git
cd DietAI
```

#### 2. 配置环境变量
```bash
# 复制环境变量模板
cp env.example .env

# 编辑环境变量文件
nano .env
```

#### 3. 使用Docker Compose启动（推荐）
```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f dietai-backend
```

#### 4. 本地开发环境

```bash
# 1. 安装Python依赖（使用uv）
uv sync

# 2. 启动数据库服务
docker-compose up -d postgres redis minio

# 3. 初始化数据库
alembic upgrade head

# 4. 启动后端服务
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 5. 启动前端服务（另开终端）
cd frontend/web/DietAI_Front_Web
npm install
npm run dev
```

### 🔗 服务地址

启动成功后，可通过以下地址访问：

- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **前端应用**: http://localhost:3000
- **MinIO控制台**: http://localhost:9001
- **Redis管理**: http://localhost:6379

### 🧪 验证安装

```bash
# 健康检查
curl http://localhost:8000/health

# 查看API文档
curl http://localhost:8000/docs
```

## 📚 API文档

### 认证相关

#### 用户注册
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "username": "user123",
  "email": "user@example.com",
  "password": "password123"
}
```

#### 用户登录
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "user123",
  "password": "password123"
}
```

### 食物记录

#### 上传食物图片
```http
POST /api/v1/food/upload
Content-Type: multipart/form-data
Authorization: Bearer <token>

{
  "file": <image_file>,
  "meal_type": 1,
  "description": "早餐"
}
```

#### 获取食物记录
```http
GET /api/v1/food/records?date=2024-01-01
Authorization: Bearer <token>
```

### AI对话

#### 发送消息
```http
POST /api/v1/conversation/chat
Content-Type: application/json
Authorization: Bearer <token>

{
  "message": "今天的饮食怎么样？",
  "conversation_id": "uuid-string"
}
```

### 健康数据

#### 获取营养统计
```http
GET /api/v1/health/nutrition/summary?start_date=2024-01-01&end_date=2024-01-31
Authorization: Bearer <token>
```

### 完整API文档

启动服务后访问 http://localhost:8000/docs 查看完整的交互式API文档。

## 🔧 配置说明

### 环境变量配置

```bash
# 应用配置
DIETAI_ENV=development
DIETAI_DEBUG=true
DIETAI_VERSION=0.1.0
DIETAI_SECRET_KEY=your-secret-key-here

# 数据库配置
DIETAI_DATABASE_URL=postgresql://user:pass@localhost:5432/dietai_db
DIETAI_REDIS_HOST=localhost
DIETAI_REDIS_PORT=6379
DIETAI_REDIS_PASSWORD=

# MinIO配置
DIETAI_MINIO_ENDPOINT=localhost:9000
DIETAI_MINIO_ACCESS_KEY=minioadmin
DIETAI_MINIO_SECRET_KEY=minioadmin
DIETAI_MINIO_SECURE=false

# AI配置
DIETAI_OPENAI_API_KEY=your-openai-key
DIETAI_ANTHROPIC_API_KEY=your-anthropic-key
DIETAI_DASHSCOPE_API_KEY=your-dashscope-key

# CORS配置
DIETAI_CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

### 数据库迁移

```bash
# 生成迁移文件
alembic revision --autogenerate -m "描述变更"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

## 🚦 开发指南

### 项目结构

```
DietAI/
├── agent/                    # AI Agent模块
│   ├── agent.py             # 主Agent逻辑
│   ├── common_utils/        # 通用工具
│   └── utils/               # Agent工具集
├── routers/                 # FastAPI路由
│   ├── auth_router.py       # 认证路由
│   ├── user_router.py       # 用户路由
│   ├── food_router.py       # 食物路由
│   ├── health_router.py     # 健康路由
│   └── conversation_router.py # 对话路由
├── shared/                  # 共享模块
│   ├── config/             # 配置管理
│   ├── models/             # 数据模型
│   └── utils/              # 通用工具
├── frontend/               # 前端项目
│   ├── web/                # Web端
│   └── mobile/             # 移动端
├── infrastructure/         # 基础设施
│   ├── docker/             # Docker配置
│   ├── k8s/                # Kubernetes配置
│   └── monitoring/         # 监控配置
├── docs/                   # 项目文档
├── main.py                 # 应用入口
├── pyproject.toml          # Python依赖
└── docker-compose.yml      # Docker编排
```

### 编码规范

#### Python代码规范
```python
# 使用Type Hints
from typing import Optional, List, Dict, Any

async def get_user_profile(user_id: int) -> Optional[Dict[str, Any]]:
    """获取用户档案信息"""
    # 实现逻辑
    pass

# 使用Pydantic进行数据验证
from pydantic import BaseModel, Field

class UserCreateRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    password: str = Field(..., min_length=6)
```

#### 错误处理
```python
from fastapi import HTTPException, status

async def get_user(user_id: int):
    try:
        user = await user_service.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        return user
    except Exception as e:
        logger.error(f"获取用户失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误"
        )
```

### 测试指南

#### 运行测试
```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_auth.py

# 运行测试并生成覆盖率报告
pytest --cov=. --cov-report=html
```

#### 测试示例
```python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_user_registration():
    response = client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 200
    assert response.json()["success"] == True
```

## 📈 性能优化

### 数据库优化
- 合理使用索引
- 数据库连接池配置
- 查询语句优化
- 读写分离

### 缓存策略
- Redis缓存热点数据
- 应用层缓存
- CDN静态资源加速

### API性能
- 异步处理
- 批量操作
- 分页查询
- 响应压缩

## 🔒 安全考虑

### 认证安全
- JWT Token管理
- 密码加密存储
- 会话管理
- 多因素认证

### 数据安全
- 数据加密传输
- 敏感数据脱敏
- 访问权限控制
- 数据备份策略

### API安全
- 请求限流
- 参数验证
- SQL注入防护
- XSS防护

## 🐛 问题排查

### 常见问题

#### 1. 数据库连接失败
```bash
# 检查数据库服务状态
docker-compose ps postgres

# 查看数据库日志
docker-compose logs postgres

# 测试数据库连接
psql -h localhost -U dietai -d dietai_db
```

#### 2. Redis连接失败
```bash
# 检查Redis服务
docker-compose ps redis

# 测试Redis连接
redis-cli -h localhost -p 6379 ping
```

#### 3. MinIO访问失败
```bash
# 检查MinIO服务
docker-compose ps minio

# 访问MinIO控制台
open http://localhost:9001
```

### 日志查看

```bash
# 查看应用日志
docker-compose logs -f dietai-backend

# 查看特定服务日志
docker-compose logs -f postgres
docker-compose logs -f redis
docker-compose logs -f minio
```

## 📊 监控运维

### 健康检查
```bash
# 应用健康检查
curl http://localhost:8000/health

# 数据库健康检查
curl http://localhost:8000/health/db

# 服务状态检查
docker-compose ps
```

### 性能监控
- 接口响应时间
- 数据库查询性能
- 内存使用情况
- CPU负载监控

## 🤝 贡献指南

### 提交代码

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/new-feature`)
3. 提交代码 (`git commit -am 'Add new feature'`)
4. 推送到分支 (`git push origin feature/new-feature`)
5. 创建Pull Request

### 代码审查

- 代码风格检查
- 单元测试覆盖
- 性能影响评估
- 安全性检查

## 📄 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。

## 🆘 技术支持

- **文档**: [项目Wiki](https://github.com/your-username/DietAI/wiki)
- **问题反馈**: [GitHub Issues](https://github.com/your-username/DietAI/issues)
- **讨论交流**: [GitHub Discussions](https://github.com/your-username/DietAI/discussions)

## 🗺️ 开发路线图

### 已完成功能 ✅
- [x] 用户认证系统
- [x] 基础数据模型
- [x] 食物记录API
- [x] AI对话基础框架
- [x] Docker部署配置

### 开发中功能 🚧
- [ ] 图像识别功能
- [ ] 营养分析算法
- [ ] 个性化推荐系统
- [ ] 移动端应用

### 计划功能 📋
- [ ] 社区功能
- [ ] 健康报告生成
- [ ] 第三方设备集成
- [ ] 多语言支持

---

## 📞 联系我们

如果您在使用过程中遇到问题或有任何建议，请通过以下方式联系我们：

- **Email**: support@dietai.com
- **GitHub**: [DietAI项目](https://github.com/your-username/DietAI)
- **官网**: https://dietai.com

感谢您对DietAI项目的关注和支持！ 🙏

