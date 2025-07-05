# DietAgent

DietAgent 是一个智能营养师AI助手，具备图片识别、个性化建议、健康管理等核心功能。

## 项目目标
- 智能化：多模态AI分析食物营养成分
- 个性化：基于用户健康状况的定制化建议
- 交互式：渐进式对话和长期记忆管理
- 全面性：从记录到分析到建议的完整闭环

## 核心架构
- 微服务：用户服务、AI分析服务、记录服务、健康评估服务
- 数据存储：PostgreSQL、Redis、MinIO
- AI能力：LangGraph、LangChain、LLM
- 前端：Web（Vue3）、移动端（UniApp，后续）

## 主要技术栈
- FastAPI、SQLAlchemy、Alembic
- PostgreSQL、Redis、MinIO
- LangGraph、LangChain
- Docker、Docker Compose

## 目录结构
```
services/
  user_service/         # 用户服务
  ai_service/           # AI分析服务
  record_service/       # 记录服务
  health_service/       # 健康评估服务
shared/
  models/               # 数据模型
  utils/                # 公共工具
  config/               # 配置文件
infrastructure/
  docker/               # 容器配置
  k8s/                  # K8s配置
  monitoring/           # 监控配置
frontend/
  web/                  # Web端（后续）
  mobile/               # 移动端（后续）
docs/                   # 项目文档
main.py                 # 启动入口（开发调试用）
pyproject.toml          # Python依赖管理
```

## 快速开始
1. 安装依赖：`uv pip install .`
2. 启动服务：`docker-compose up -d`
3. 访问API文档：`http://localhost:8000/docs`

---
详细设计与开发计划见 docs/ 目录。

