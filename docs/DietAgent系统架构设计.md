# DietAgent系统架构设计

## 🏗️ 系统整体架构

### 架构概览
采用**微服务 + AI Agent + 事件驱动**的混合架构：

```
┌─────────────────────────────────────────────────────────────┐
│                        前端层                                │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │  Web App    │ │   微信端     │ │  管理后台    │            │
│  │  (Vue3)     │ │ (UniApp)    │ │ (React)     │            │
│  └─────────────┘ └─────────────┘ └─────────────┘            │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      API网关层                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                 Nginx + Kong                            │ │
│  │        (负载均衡、认证、限流、日志)                         │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                       核心服务层                             │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│ │  用户服务     │ │   AI分析服务  │ │   记录服务    │           │
│ │ (FastAPI)    │ │ (LangGraph)  │ │ (FastAPI)    │           │
│ └──────────────┘ └──────────────┘ └──────────────┘           │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│ │  健康评估服务 │ │   推荐服务    │ │   通知服务    │           │
│ │ (FastAPI)    │ │ (FastAPI)    │ │ (FastAPI)    │           │
│ └──────────────┘ └──────────────┘ └──────────────┘           │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      数据存储层                              │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│ │ PostgreSQL   │ │    Redis     │ │    MinIO     │           │
│ │  (主数据库)   │ │   (缓存)     │ │  (对象存储)   │           │
│ └──────────────┘ └──────────────┘ └──────────────┘           │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│ │ ClickHouse   │ │   LangMem    │ │  Milvus      │           │
│ │ (行为分析)    │ │ (长期记忆)    │ │ (向量数据库)  │           │
│ └──────────────┘ └──────────────┘ └──────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

## 📊 详细数据库设计

### 1. 用户管理模块

```sql
-- 用户基本信息表
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20) UNIQUE,
    password_hash VARCHAR(255),
    salt VARCHAR(32),
    avatar_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status INTEGER DEFAULT 1, -- 1:正常 0:禁用
    last_login_at TIMESTAMP
);

-- 第三方登录关联表
CREATE TABLE user_oauth (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    provider VARCHAR(20) NOT NULL, -- wechat, qq, apple
    provider_user_id VARCHAR(100) NOT NULL,
    access_token TEXT,
    refresh_token TEXT,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(provider, provider_user_id)
);

-- 用户详细信息表
CREATE TABLE user_profiles (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) UNIQUE,
    real_name VARCHAR(50),
    gender INTEGER, -- 1:男 2:女 0:未知
    birth_date DATE,
    height DECIMAL(5,2), -- cm
    weight DECIMAL(5,2), -- kg
    bmi DECIMAL(4,2),
    activity_level INTEGER DEFAULT 2, -- 1:久坐 2:轻度 3:中度 4:重度 5:超重度
    occupation VARCHAR(100),
    region VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户健康目标表
CREATE TABLE user_health_goals (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    goal_type INTEGER NOT NULL, -- 1:减重 2:增重 3:增肌 4:减脂 5:疾病管理 6:维持
    target_weight DECIMAL(5,2),
    target_date DATE,
    current_status INTEGER DEFAULT 1, -- 1:进行中 2:已完成 3:已暂停
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户疾病信息表
CREATE TABLE user_diseases (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    disease_code VARCHAR(20), -- ICD-10编码
    disease_name VARCHAR(100) NOT NULL,
    severity_level INTEGER, -- 1:轻度 2:中度 3:重度
    diagnosed_date DATE,
    is_current BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户过敏信息表
CREATE TABLE user_allergies (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    allergen_type INTEGER, -- 1:食物 2:药物 3:环境
    allergen_name VARCHAR(100) NOT NULL,
    severity_level INTEGER, -- 1:轻微 2:中度 3:严重
    reaction_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. 食物记录模块

```sql
-- 食物记录主表
CREATE TABLE food_records (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    record_date DATE NOT NULL,
    meal_type INTEGER NOT NULL, -- 1:早餐 2:午餐 3:晚餐 4:加餐 5:零食
    food_name VARCHAR(200),
    description TEXT,
    image_url VARCHAR(255),
    image_analysis_result JSONB, -- AI分析的原始结果
    location_info JSONB, -- 地理位置信息
    recording_method INTEGER DEFAULT 1, -- 1:拍照 2:手动输入 3:语音 4:扫码
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 营养成分详情表
CREATE TABLE nutrition_details (
    id BIGSERIAL PRIMARY KEY,
    food_record_id BIGINT REFERENCES food_records(id),
    calories DECIMAL(8,2) DEFAULT 0, -- 大卡
    protein DECIMAL(8,2) DEFAULT 0, -- 蛋白质(g)
    fat DECIMAL(8,2) DEFAULT 0, -- 脂肪(g)
    carbohydrates DECIMAL(8,2) DEFAULT 0, -- 碳水化合物(g)
    dietary_fiber DECIMAL(8,2) DEFAULT 0, -- 膳食纤维(g)
    sugar DECIMAL(8,2) DEFAULT 0, -- 糖(g)
    sodium DECIMAL(8,2) DEFAULT 0, -- 钠(mg)
    cholesterol DECIMAL(8,2) DEFAULT 0, -- 胆固醇(mg)
    vitamin_a DECIMAL(8,2) DEFAULT 0, -- 维生素A(μg)
    vitamin_c DECIMAL(8,2) DEFAULT 0, -- 维生素C(mg)
    vitamin_d DECIMAL(8,2) DEFAULT 0, -- 维生素D(μg)
    calcium DECIMAL(8,2) DEFAULT 0, -- 钙(mg)
    iron DECIMAL(8,2) DEFAULT 0, -- 铁(mg)
    potassium DECIMAL(8,2) DEFAULT 0, -- 钾(mg)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 每日汇总表
CREATE TABLE daily_nutrition_summary (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    summary_date DATE NOT NULL,
    total_calories DECIMAL(8,2) DEFAULT 0,
    total_protein DECIMAL(8,2) DEFAULT 0,
    total_fat DECIMAL(8,2) DEFAULT 0,
    total_carbohydrates DECIMAL(8,2) DEFAULT 0,
    total_fiber DECIMAL(8,2) DEFAULT 0,
    total_sodium DECIMAL(8,2) DEFAULT 0,
    meal_count INTEGER DEFAULT 0,
    water_intake DECIMAL(6,2) DEFAULT 0, -- 饮水量(L)
    exercise_calories DECIMAL(8,2) DEFAULT 0, -- 运动消耗
    health_score DECIMAL(4,2), -- 当日健康评分
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, summary_date)
);

-- 体重记录表
CREATE TABLE weight_records (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    weight DECIMAL(5,2) NOT NULL,
    body_fat_percentage DECIMAL(4,2), -- 体脂率
    muscle_mass DECIMAL(5,2), -- 肌肉量
    bmi DECIMAL(4,2),
    measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    device_type VARCHAR(50) -- 测量设备类型
);
```

### 3. AI对话与记忆模块

```sql
-- 对话会话表
CREATE TABLE conversation_sessions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    session_type INTEGER DEFAULT 1, -- 1:营养咨询 2:食物识别 3:健康建议 4:食谱推荐
    langgraph_thread_id VARCHAR(100) UNIQUE,
    langgraph_assistant_id VARCHAR(100),
    title VARCHAR(200),
    status INTEGER DEFAULT 1, -- 1:活跃 2:已结束
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_message_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 消息记录表
CREATE TABLE conversation_messages (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT REFERENCES conversation_sessions(id),
    message_type INTEGER NOT NULL, -- 1:用户消息 2:AI回复 3:系统消息
    content TEXT NOT NULL,
    metadata JSONB, -- 附加信息，如图片、位置等
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户偏好设置表
CREATE TABLE user_preferences (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) UNIQUE,
    dietary_restrictions JSONB, -- 饮食限制 ["vegetarian", "halal", "kosher"]
    disliked_foods JSONB, -- 不喜欢的食物
    preferred_cuisines JSONB, -- 偏好菜系
    spice_tolerance INTEGER DEFAULT 3, -- 辣度耐受 1-5
    notification_settings JSONB, -- 通知设置
    privacy_settings JSONB, -- 隐私设置
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 长期记忆管理表 (与LangMem集成)
CREATE TABLE user_memory_contexts (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    memory_type INTEGER, -- 1:饮食习惯 2:健康状态 3:偏好记录 4:行为模式
    context_key VARCHAR(100),
    context_value JSONB,
    importance_score DECIMAL(3,2), -- 重要性评分 0-1
    last_accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP, -- 记忆过期时间
    INDEX(user_id, memory_type, importance_score)
);
```

### 4. 知识库与推荐模块

```sql
-- 食物基础知识库
CREATE TABLE food_database (
    id BIGSERIAL PRIMARY KEY,
    food_code VARCHAR(20) UNIQUE, -- 食物编码
    food_name VARCHAR(200) NOT NULL,
    food_name_en VARCHAR(200),
    category_id INTEGER,
    subcategory_id INTEGER,
    brand VARCHAR(100),
    serving_size DECIMAL(6,2), -- 标准份量(g)
    calories_per_100g DECIMAL(8,2),
    protein_per_100g DECIMAL(8,2),
    fat_per_100g DECIMAL(8,2),
    carb_per_100g DECIMAL(8,2),
    fiber_per_100g DECIMAL(8,2),
    sodium_per_100g DECIMAL(8,2),
    nutrition_grade CHAR(1), -- A-E营养等级
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 疾病-营养素关联表
CREATE TABLE disease_nutrition_relations (
    id BIGSERIAL PRIMARY KEY,
    disease_code VARCHAR(20),
    nutrient_name VARCHAR(50),
    relation_type INTEGER, -- 1:需要控制 2:需要增加 3:需要避免
    recommended_daily_amount DECIMAL(8,2),
    max_daily_amount DECIMAL(8,2),
    warning_threshold DECIMAL(8,2),
    description TEXT,
    evidence_level INTEGER -- 1-5 证据等级
);

-- 个性化推荐记录表
CREATE TABLE personalized_recommendations (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    recommendation_type INTEGER, -- 1:食物推荐 2:食谱推荐 3:运动建议 4:健康提醒
    content JSONB,
    reason TEXT, -- 推荐理由
    priority_score DECIMAL(3,2), -- 优先级评分
    status INTEGER DEFAULT 1, -- 1:待处理 2:已查看 3:已采纳 4:已忽略
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🏭 微服务架构设计

### 1. 用户服务 (User Service)
```python
# user_service/main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from . import models, schemas, crud, auth

app = FastAPI(title="用户服务", version="1.0.0")

@app.post("/register", response_model=schemas.UserResponse)
async def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    pass

@app.post("/login", response_model=schemas.TokenResponse)
async def login(credentials: schemas.LoginCredentials, db: Session = Depends(get_db)):
    """用户登录"""
    pass

@app.post("/oauth/{provider}")
async def oauth_login(provider: str, oauth_data: schemas.OAuthData):
    """第三方登录"""
    pass

@app.get("/profile", response_model=schemas.UserProfile)
async def get_profile(current_user: models.User = Depends(get_current_user)):
    """获取用户资料"""
    pass

@app.put("/profile")
async def update_profile(profile: schemas.UserProfileUpdate, 
                        current_user: models.User = Depends(get_current_user)):
    """更新用户资料"""
    pass
```

### 2. AI分析服务 (AI Analysis Service)
```python
# ai_service/main.py
from fastapi import FastAPI, UploadFile, File, Depends
from langchain_community.chat_models import ChatOpenAI
from langgraph.graph import StateGraph
from . import agents, states, tools

app = FastAPI(title="AI分析服务", version="1.0.0")

@app.post("/analyze/image")
async def analyze_food_image(
    file: UploadFile = File(...),
    user_context: dict = Depends(get_user_context)
):
    """食物图片分析"""
    # 使用你现有的LangGraph实现
    pass

@app.post("/chat/nutrition")
async def nutrition_chat(
    message: str,
    session_id: str,
    user_context: dict = Depends(get_user_context)
):
    """营养咨询对话"""
    pass

@app.post("/recommend/meals")
async def recommend_meals(
    user_id: int,
    preferences: dict,
    health_goals: list
):
    """个性化膳食推荐"""
    pass

@app.post("/analyze/health-trends")
async def analyze_health_trends(user_id: int, days: int = 30):
    """健康趋势分析"""
    pass
```

### 3. 记录服务 (Record Service)
```python
# record_service/main.py
from fastapi import FastAPI, Depends, BackgroundTasks
from . import models, schemas, crud

app = FastAPI(title="记录服务", version="1.0.0")

@app.post("/food-records", response_model=schemas.FoodRecordResponse)
async def create_food_record(
    record: schemas.FoodRecordCreate,
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(get_current_user)
):
    """创建食物记录"""
    # 保存记录到数据库
    # 异步触发营养分析
    background_tasks.add_task(analyze_nutrition, record.id)
    pass

@app.get("/food-records")
async def get_food_records(
    date_from: date = None,
    date_to: date = None,
    meal_type: int = None,
    current_user: models.User = Depends(get_current_user)
):
    """获取食物记录"""
    pass

@app.post("/weight-records")
async def create_weight_record(
    weight_data: schemas.WeightRecordCreate,
    current_user: models.User = Depends(get_current_user)
):
    """记录体重"""
    pass

@app.get("/daily-summary/{date}")
async def get_daily_summary(
    date: date,
    current_user: models.User = Depends(get_current_user)
):
    """获取每日营养汇总"""
    pass
```

### 4. 健康评估服务 (Health Assessment Service)
```python
# health_service/main.py
from fastapi import FastAPI, Depends
from . import calculators, analyzers

app = FastAPI(title="健康评估服务", version="1.0.0")

@app.post("/calculate/bmr")
async def calculate_bmr(user_data: schemas.UserBasicInfo):
    """计算基础代谢率"""
    pass

@app.post("/calculate/tdee")
async def calculate_tdee(user_data: schemas.UserBasicInfo, activity_level: int):
    """计算每日总能量消耗"""
    pass

@app.post("/assess/health-score")
async def assess_health_score(
    user_id: int,
    analysis_period: int = 7  # 天数
):
    """计算健康评分"""
    pass

@app.post("/analyze/nutrition-balance")
async def analyze_nutrition_balance(user_id: int, date: date):
    """分析营养平衡度"""
    pass

@app.get("/recommendations/daily-targets")
async def get_daily_targets(user_id: int):
    """获取每日营养目标"""
    pass
```

## 🔧 技术栈详细规划

### 后端技术栈
```yaml
核心框架:
  - FastAPI: Web框架，支持异步和自动API文档
  - LangGraph: AI Agent工作流引擎
  - SQLAlchemy: ORM框架
  - Alembic: 数据库迁移工具

数据存储:
  - PostgreSQL: 主数据库
  - Redis: 缓存和会话存储
  - MinIO: 对象存储(图片、文件)
  - ClickHouse: 行为分析数据仓库
  - Milvus: 向量数据库(语义搜索)

AI相关:
  - LangChain: LLM框架
  - LangMem: 长期记忆管理
  - OpenAI/Qwen: 多模态模型
  - Transformers: 本地模型推理

消息队列:
  - RabbitMQ: 异步任务处理
  - Celery: 后台任务执行

监控运维:
  - Prometheus: 指标监控
  - Grafana: 可视化面板
  - ELK Stack: 日志分析
  - Jaeger: 链路追踪
```

### 前端技术栈
```yaml
Web端:
  - Vue 3 + TypeScript
  - Vite: 构建工具
  - Pinia: 状态管理
  - Vue Router: 路由管理
  - Element Plus: UI组件库
  - ECharts: 数据可视化

移动端:
  - UniApp: 跨平台开发
  - Vue 3 + TypeScript
  - uni-ui: 组件库

管理后台:
  - React 18 + TypeScript
  - Next.js: 全栈框架
  - Ant Design: UI组件库
  - React Query: 数据获取
```

## 🚀 部署架构

### Docker Compose 配置优化
```yaml
# docker-compose.yml
version: '3.8'

services:
  # API网关
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - user-service
      - ai-service
      - record-service
      - health-service

  # 用户服务
  user-service:
    build: ./services/user_service
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/dietagent
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis

  # AI分析服务
  ai-service:
    build: ./services/ai_service
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - QWEN_API_KEY=${QWEN_API_KEY}
      - MILVUS_URI=milvus:19530
    depends_on:
      - milvus
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  # 记录服务
  record-service:
    build: ./services/record_service
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/dietagent
      - MINIO_ENDPOINT=minio:9000
    depends_on:
      - postgres
      - minio

  # 健康评估服务
  health-service:
    build: ./services/health_service
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432
      - CLICKHOUSE_URL=clickhouse://clickhouse:8123
    depends_on:
      - postgres
      - clickhouse

  # 数据库
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: dietagent
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/

  # 缓存
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

  # 对象存储
  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: admin
      MINIO_ROOT_PASSWORD: password123
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data

  # 向量数据库
  milvus:
    image: milvusdb/milvus:latest
    command: ["milvus", "run", "standalone"]
    environment:
      ETCD_ENDPOINTS: etcd:2379
      MINIO_ADDRESS: minio:9000
    ports:
      - "19530:19530"
    depends_on:
      - etcd
      - minio

  # 行为分析数据库
  clickhouse:
    image: clickhouse/clickhouse-server:latest
    ports:
      - "8123:8123"
      - "9009:9009"
    volumes:
      - clickhouse_data:/var/lib/clickhouse

  # 消息队列
  rabbitmq:
    image: rabbitmq:3-management-alpine
    environment:
      RABBITMQ_DEFAULT_USER: admin
      RABBITMQ_DEFAULT_PASS: password
    ports:
      - "5672:5672"
      - "15672:15672"
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq

  # 后台任务处理
  celery-worker:
    build: ./services/shared
    command: celery -A tasks worker --loglevel=info
    environment:
      - CELERY_BROKER_URL=amqp://admin:password@rabbitmq:5672//
      - DATABASE_URL=postgresql://user:pass@postgres:5432/dietagent
    depends_on:
      - rabbitmq
      - postgres

volumes:
  postgres_data:
  redis_data:
  minio_data:
  clickhouse_data:
  rabbitmq_data:
```

## 📱 功能模块详细设计

### 1. 用户个性化健康规则引擎

```python
# health_rules_engine.py
class HealthRulesEngine:
    def __init__(self):
        self.rules = {}
        
    def create_personalized_rules(self, user_profile: UserProfile):
        """根据用户信息创建个性化规则"""
        rules = []
        
        # 基于疾病的规则
        for disease in user_profile.diseases:
            rules.extend(self._create_disease_rules(disease))
        
        # 基于目标的规则
        if user_profile.goal_type == GoalType.WEIGHT_LOSS:
            rules.extend(self._create_weight_loss_rules(user_profile))
        
        # 基于过敏的规则
        for allergy in user_profile.allergies:
            rules.extend(self._create_allergy_rules(allergy))
            
        return rules
    
    def evaluate_food_item(self, food_item: FoodItem, user_rules: List[Rule]):
        """评估食物是否符合用户健康规则"""
        score = 10.0  # 基础分数
        warnings = []
        
        for rule in user_rules:
            result = rule.evaluate(food_item)
            score += result.score_adjustment
            if result.warning:
                warnings.append(result.warning)
        
        return HealthEvaluation(score=score, warnings=warnings)
```

### 2. 智能营养分析与建议生成

```python
# nutrition_analyzer.py
class NutritionAnalyzer:
    def __init__(self, llm_model, user_context):
        self.llm = llm_model
        self.user_context = user_context
        
    async def analyze_meal_composition(self, food_items: List[FoodItem]):
        """分析餐食组成和营养平衡"""
        
        # 计算总营养成分
        total_nutrition = self._calculate_total_nutrition(food_items)
        
        # 评估营养平衡
        balance_score = self._evaluate_nutrition_balance(total_nutrition)
        
        # 生成个性化建议
        recommendations = await self._generate_recommendations(
            total_nutrition, balance_score
        )
        
        return NutritionAnalysis(
            total_nutrition=total_nutrition,
            balance_score=balance_score,
            recommendations=recommendations
        )
    
    async def _generate_recommendations(self, nutrition, balance_score):
        """使用LLM生成个性化建议"""
        prompt = f"""
        用户信息：{self.user_context}
        本餐营养成分：{nutrition}
        营养平衡评分：{balance_score}
        
        请提供专业的营养建议，包括：
        1. 本餐的优点和不足
        2. 下一餐的建议调整
        3. 长期饮食建议
        4. 特定人群注意事项
        """
        
        response = await self.llm.ainvoke(prompt)
        return self._parse_recommendations(response.content)
```

### 3. 长期记忆管理与上下文维护

```python
# memory_manager.py
from langmem import LangMem

class UserMemoryManager:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.memory = LangMem(
            namespace=f"user_{user_id}",
            storage_backend="postgresql://...",
            vector_store="milvus://..."
        )
    
    async def update_dietary_habits(self, food_record: FoodRecord):
        """更新用户饮食习惯记忆"""
        
        # 提取关键信息
        habits = {
            "preferred_meal_times": self._extract_meal_timing(food_record),
            "food_preferences": self._extract_food_preferences(food_record),
            "portion_sizes": self._extract_portion_patterns(food_record),
            "cooking_methods": self._extract_cooking_preferences(food_record)
        }
        
        # 存储到长期记忆
        await self.memory.store(
            key="dietary_habits",
            content=habits,
            importance=0.8,
            decay_rate=0.1  # 缓慢衰减
        )
    
    async def get_personalized_context(self) -> dict:
        """获取用户个性化上下文"""
        
        # 检索相关记忆
        dietary_habits = await self.memory.retrieve("dietary_habits")
        health_trends = await self.memory.retrieve("health_trends")
        preferences = await self.memory.retrieve("preferences")
        
        return {
            "dietary_habits": dietary_habits,
            "health_trends": health_trends,
            "preferences": preferences,
            "last_updated": datetime.now()
        }
```

### 4. 健康度评估算法

```python
# health_scorer.py
class HealthScorer:
    def __init__(self):
        self.weights = {
            "nutrition_balance": 0.3,
            "calorie_balance": 0.2,
            "food_variety": 0.15,
            "meal_timing": 0.1,
            "hydration": 0.1,
            "exercise_correlation": 0.1,
            "consistency": 0.05
        }
    
    def calculate_daily_health_score(self, user_id: int, date: date) -> float:
        """计算每日健康评分"""
        
        scores = {}
        
        # 营养平衡评分
        scores["nutrition_balance"] = self._score_nutrition_balance(user_id, date)
        
        # 热量平衡评分
        scores["calorie_balance"] = self._score_calorie_balance(user_id, date)
        
        # 食物多样性评分
        scores["food_variety"] = self._score_food_variety(user_id, date)
        
        # 用餐时间规律性评分
        scores["meal_timing"] = self._score_meal_timing(user_id, date)
        
        # 水分摄入评分
        scores["hydration"] = self._score_hydration(user_id, date)
        
        # 运动相关性评分
        scores["exercise_correlation"] = self._score_exercise_correlation(user_id, date)
        
        # 饮食一致性评分（7天内）
        scores["consistency"] = self._score_consistency(user_id, date, days=7)
        
        # 加权计算总分
        total_score = sum(score * self.weights[key] for key, score in scores.items())
        
        return min(10.0, max(0.0, total_score))
    
    def calculate_trend_health_score(self, user_id: int, days: int = 30) -> dict:
        """计算健康趋势评分"""
        
        daily_scores = []
        for i in range(days):
            date = datetime.now().date() - timedelta(days=i)
            score = self.calculate_daily_health_score(user_id, date)
            daily_scores.append(score)
        
        return {
            "current_score": daily_scores[0],
            "average_score": sum(daily_scores) / len(daily_scores),
            "trend": self._calculate_trend(daily_scores),
            "improvement_suggestions": self._generate_improvement_suggestions(daily_scores)
        }
```

## 🔒 安全性与隐私保护

### 1. 数据安全
```python
# security.py
from cryptography.fernet import Fernet
import hashlib

class SecurityManager:
    def __init__(self):
        self.encryption_key = Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """加密敏感数据"""
        return self.cipher.encrypt(data.encode()).decode()
    
    def hash_password(self, password: str, salt: str) -> str:
        """密码哈希"""
        return hashlib.pbkdf2_hmac('sha256', 
                                  password.encode(), 
                                  salt.encode(), 
                                  100000).hex()
    
    def anonymize_user_data(self, user_data: dict) -> dict:
        """用户数据匿名化"""
        sensitive_fields = ['name', 'email', 'phone']
        anonymized = user_data.copy()
        
        for field in sensitive_fields:
            if field in anonymized:
                anonymized[field] = self._generate_anonymous_id()
        
        return anonymized
```

### 2. API安全
```python
# api_security.py
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """添加安全头"""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

@app.post("/api/sensitive-endpoint")
@limiter.limit("5/minute")  # 限流
async def sensitive_endpoint(
    request: Request,
    current_user: User = Depends(get_current_user_with_2fa)  # 双因子认证
):
    pass
```

## 📊 监控与运维

### 1. 系统监控
```python
# monitoring.py
from prometheus_client import Counter, Histogram, Gauge
import time

# 定义指标
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
ACTIVE_USERS = Gauge('active_users_total', 'Number of active users')

@app.middleware("http")
async def monitoring_middleware(request: Request, call_next):
    """监控中间件"""
    start_time = time.time()
    
    response = await call_next(request)
    
    # 记录指标
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path
    ).inc()
    
    REQUEST_DURATION.observe(time.time() - start_time)
    
    return response
```

### 2. 健康检查
```python
# health_check.py
@app.get("/health")
async def health_check():
    """系统健康检查"""
    checks = {
        "database": await check_database_connection(),
        "redis": await check_redis_connection(),
        "minio": await check_minio_connection(),
        "ai_service": await check_ai_service(),
        "memory_service": await check_memory_service()
    }
    
    all_healthy = all(checks.values())
    
    return {
        "status": "healthy" if all_healthy else "unhealthy",
        "checks": checks,
        "timestamp": datetime.now().isoformat()
    }
```

## 🚀 实施路线图

### 阶段1：核心功能开发 (4-6周)
1. ✅ 用户注册登录系统
2. ✅ 图片上传和AI分析
3. ✅ 基础营养记录功能
4. ✅ 简单的健康评分

### 阶段2：智能化增强 (6-8周)
1. 🔄 长期记忆集成（LangMem）
2. 🔄 个性化推荐引擎
3. 🔄 对话式交互
4. 🔄 健康趋势分析

### 阶段3：生态完善 (8-10周)
1. ⏳ 移动端开发（UniApp）
2. ⏳ 第三方登录集成
3. ⏳ 数据导出功能
4. ⏳ 社交分享功能

### 阶段4：规模化部署 (4-6周)
1. ⏳ 微服务拆分
2. ⏳ 容器化部署
3. ⏳ 监控运维体系
4. ⏳ 性能优化

## 💡 创新特性建议

### 1. AI驱动的预测性健康管理
- 基于历史数据预测用户健康趋势
- 提前预警潜在健康风险
- 智能调整饮食建议

### 2. 社交化健康管理
- 家庭健康管理功能
- 健康挑战和激励机制
- 专业营养师在线咨询


### 3. IoT设备集成
- 智能体重秤数据同步
- 运动手环数据整合
- 智能厨房设备联动

### 4. AR/VR体验
- AR食物识别和营养展示
- VR虚拟营养教育
- 3D食物建模和分量估算

这个架构设计为DietAgent提供了一个可扩展、高性能、智能化的完整解决方案。建议按照实施路线图逐步开发，优先完成核心功能，再逐步增加智能化特性。 

## 🧩 核心模块详细设计与实现思路

### 1. 自定义健康规则引擎

#### 设计思路
- **规则驱动架构**：采用规则引擎模式，支持动态配置和热更新
- **多维度规则体系**：疾病、目标、过敏、个人偏好多维度规则
- **智能推理机制**：结合专家知识和AI学习的混合推理

#### 实现方案
```python
# rules_engine/core.py
class RuleEngine:
    """健康规则引擎核心"""
    
    def __init__(self):
        self.rule_chains = {
            'disease_rules': DiseaseRuleChain(),
            'goal_rules': GoalRuleChain(), 
            'allergy_rules': AllergyRuleChain(),
            'preference_rules': PreferenceRuleChain()
        }
    
    def evaluate_food(self, food_item: FoodItem, user_profile: UserProfile):
        """食物评估主流程"""
        evaluation_result = EvaluationResult()
        
        for chain_name, rule_chain in self.rule_chains.items():
            result = rule_chain.evaluate(food_item, user_profile)
            evaluation_result.merge(result)
        
        return evaluation_result

# 疾病规则链示例
class DiseaseRuleChain:
    def __init__(self):
        self.rules = {
            'diabetes': DiabetesRule(),
            'hypertension': HypertensionRule(),
            'kidney_disease': KidneyDiseaseRule()
        }
    
    def evaluate(self, food_item, user_profile):
        results = []
        for disease in user_profile.diseases:
            if disease.code in self.rules:
                rule = self.rules[disease.code]
                result = rule.apply(food_item, disease.severity)
                results.append(result)
        return self._aggregate_results(results)
```

#### 规则配置系统
```yaml
# config/disease_rules.yaml
diabetes:
  nutrients_to_watch:
    carbohydrates:
      warning_threshold: 45  # 每餐碳水>45g警告
      danger_threshold: 60   # 每餐碳水>60g危险
    sugar:
      warning_threshold: 15
      danger_threshold: 25
  
  recommended_foods:
    - "全麦食品"
    - "蔬菜类"
    - "瘦肉蛋白"
  
  foods_to_avoid:
    - "高糖饮料"
    - "糖果甜点"
    - "白米白面"

hypertension:
  nutrients_to_watch:
    sodium:
      warning_threshold: 800  # 每餐钠>800mg警告
      danger_threshold: 1200
```

### 2. 图片识别与营养分析模块

#### 多模态AI识别流程
```python
# ai_analysis/vision_pipeline.py
class FoodVisionPipeline:
    """食物视觉识别管道"""
    
    def __init__(self):
        self.detector = FoodDetector()      # 食物检测
        self.classifier = FoodClassifier()  # 食物分类
        self.estimator = PortionEstimator() # 分量估算
        self.nutrition_db = NutritionDB()   # 营养数据库
    
    async def analyze_image(self, image_data: bytes) -> FoodAnalysisResult:
        # 1. 食物检测与分割
        detected_foods = await self.detector.detect(image_data)
        
        # 2. 食物分类识别
        classified_foods = []
        for food_region in detected_foods:
            food_type = await self.classifier.classify(food_region)
            portion = await self.estimator.estimate_portion(food_region)
            classified_foods.append({
                'type': food_type,
                'confidence': food_type.confidence,
                'portion_grams': portion,
                'bbox': food_region.bbox
            })
        
        # 3. 营养成分计算
        nutrition_analysis = await self._calculate_nutrition(classified_foods)
        
        return FoodAnalysisResult(
            detected_foods=classified_foods,
            nutrition_facts=nutrition_analysis,
            analysis_confidence=self._calculate_overall_confidence(classified_foods)
        )
```

#### 营养计算引擎（这个不采用，具体逻辑放在Agent中）
```python
# nutrition/calculator.py
class NutritionCalculator:
    """营养成分计算器"""
    
    def calculate_meal_nutrition(self, food_items: List[FoodItem]) -> NutritionSummary:
        """计算整餐营养成分"""
        total_nutrition = NutritionFacts()
        
        for item in food_items:
            # 从数据库获取100g营养成分
            base_nutrition = self.nutrition_db.get_nutrition(item.food_code)
            
            # 按实际重量计算
            actual_nutrition = self._scale_nutrition(
                base_nutrition, 
                item.weight_grams / 100
            )
            
            total_nutrition += actual_nutrition
        
        return NutritionSummary(
            total_nutrition=total_nutrition,
            macronutrient_ratios=self._calculate_ratios(total_nutrition),
            vitamin_coverage=self._assess_vitamin_coverage(total_nutrition)
        )
```

### 3. 智能记录与打卡系统

#### 多模式记录支持
```python
# recording/recorder.py
class FoodRecorder:
    """食物记录器"""
    
    def __init__(self):
        self.image_processor = ImageProcessor()
        self.voice_processor = VoiceProcessor()
        self.manual_input = ManualInputHandler()
        self.barcode_scanner = BarcodeScanner()
    
    async def record_food(self, record_request: RecordRequest) -> RecordResult:
        """统一记录入口"""
        if record_request.type == RecordType.IMAGE:
            return await self._record_by_image(record_request)
        elif record_request.type == RecordType.VOICE:
            return await self._record_by_voice(record_request)
        elif record_request.type == RecordType.MANUAL:
            return await self._record_manually(record_request)
        elif record_request.type == RecordType.BARCODE:
            return await self._record_by_barcode(record_request)
    
    async def _record_by_voice(self, request):
        """语音记录处理"""
        # 语音转文字
        text = await self.voice_processor.speech_to_text(request.audio_data)
        
        # NLP提取食物信息
        food_entities = await self._extract_food_entities(text)
        
        # 生成记录
        return await self._create_record_from_entities(food_entities, request.user_id)
```

#### 智能提醒系统
```python
# reminders/smart_reminder.py
class SmartReminderSystem:
    """智能提醒系统"""
    
    def __init__(self):
        self.scheduler = CeleryScheduler()
        self.user_behavior_analyzer = UserBehaviorAnalyzer()
    
    async def schedule_personalized_reminders(self, user_id: int):
        """个性化提醒调度"""
        user_patterns = await self.user_behavior_analyzer.analyze(user_id)
        
        # 基于用户习惯设置提醒
        meal_times = user_patterns.typical_meal_times
        for meal_type, typical_time in meal_times.items():
            # 在用餐前30分钟提醒
            reminder_time = typical_time - timedelta(minutes=30)
            
            self.scheduler.schedule_daily_task(
                user_id=user_id,
                task_type=f"meal_reminder_{meal_type}",
                execution_time=reminder_time,
                message=self._generate_personalized_message(user_id, meal_type)
            )
```

### 4. 对话式交互与渐进式提问

#### 对话管理系统
```python
# conversation/manager.py
class ConversationManager:
    """对话管理器"""
    
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.context_manager = ContextManager()
        self.response_generator = ResponseGenerator()
        self.memory_manager = MemoryManager()
    
    async def process_message(self, user_id: int, message: str, session_id: str):
        """处理用户消息"""
        # 1. 意图识别
        intent = await self.intent_classifier.classify(message)
        
        # 2. 上下文管理
        context = await self.context_manager.get_context(user_id, session_id)
        context.add_user_message(message, intent)
        
        # 3. 生成响应
        response = await self.response_generator.generate(
            intent=intent,
            context=context,
            user_profile=await self._get_user_profile(user_id)
        )
        
        # 4. 更新记忆
        await self.memory_manager.update_conversation_memory(
            user_id, session_id, message, response
        )
        
        return response

# 意图分类示例
class IntentClassifier:
    INTENTS = {
        'food_inquiry': ['这个能吃吗', '可以吃什么', '今天吃什么'],
        'nutrition_question': ['营养成分', '热量多少', '含糖量'],
        'cooking_advice': ['怎么做', '烹饪方法', '食谱'],
        'health_consultation': ['健康吗', '对身体好吗', '会不会']
    }
```

#### 渐进式提问引擎
```python
# conversation/progressive_questioning.py
class ProgressiveQuestioningEngine:
    """渐进式提问引擎"""
    
    def __init__(self):
        self.question_trees = self._load_question_trees()
        self.user_info_collector = UserInfoCollector()
    
    async def generate_follow_up_question(self, user_id: int, current_topic: str):
        """生成后续问题"""
        # 获取用户已知信息
        known_info = await self.user_info_collector.get_known_info(user_id)
        
        # 选择问题树
        question_tree = self.question_trees[current_topic]
        
        # 找到下一个合适的问题
        next_question = question_tree.get_next_question(known_info)
        
        return next_question
    
    def _load_question_trees(self):
        """加载问题树配置"""
        return {
            'dietary_assessment': DietaryAssessmentTree(),
            'health_goals': HealthGoalsTree(),
            'lifestyle_analysis': LifestyleAnalysisTree()
        }

# 问题树示例
class DietaryAssessmentTree:
    def __init__(self):
        self.questions = {
            'root': "想了解一下您的饮食习惯，您平时喜欢吃什么类型的食物？",
            'cuisine_preference': {
                'question': "您更偏爱中式、西式还是其他风味的料理？",
                'next': ['spice_level', 'cooking_method']
            },
            'spice_level': {
                'question': "您能接受多辣的食物？(1-5级)",
                'next': ['cooking_method']
            },
            'cooking_method': {
                'question': "您更喜欢清淡的烹饪方式还是重口味的？",
                'next': ['meal_frequency']
            }
        }
```

### 5. 历史数据分析与代谢计算

#### 代谢率计算引擎
```python
# metabolism/calculator.py
class MetabolismCalculator:
    """代谢率计算器"""
    
    def calculate_bmr(self, user_profile: UserProfile) -> float:
        """基础代谢率计算"""
        if user_profile.gender == Gender.MALE:
            # Harris-Benedict公式 (男性)
            bmr = 88.362 + (13.397 * user_profile.weight) + \
                  (4.799 * user_profile.height) - (5.677 * user_profile.age)
        else:
            # Harris-Benedict公式 (女性)
            bmr = 447.593 + (9.247 * user_profile.weight) + \
                  (3.098 * user_profile.height) - (4.330 * user_profile.age)
        
        return bmr
    
    def calculate_tdee(self, bmr: float, activity_level: ActivityLevel) -> float:
        """总日能量消耗计算"""
        activity_multipliers = {
            ActivityLevel.SEDENTARY: 1.2,
            ActivityLevel.LIGHT: 1.375,
            ActivityLevel.MODERATE: 1.55,
            ActivityLevel.ACTIVE: 1.725,
            ActivityLevel.VERY_ACTIVE: 1.9
        }
        return bmr * activity_multipliers[activity_level]
    
    def analyze_metabolism_trend(self, user_id: int, days: int = 30):
        """代谢趋势分析"""
        # 获取历史数据
        history = self._get_user_history(user_id, days)
        
        # 计算代谢指标
        metrics = []
        for record in history:
            daily_intake = record.total_calories
            estimated_expenditure = self._estimate_daily_expenditure(record)
            metabolic_rate = self._calculate_metabolic_efficiency(
                daily_intake, estimated_expenditure, record.weight_change
            )
            metrics.append(metabolic_rate)
        
        return MetabolismTrendAnalysis(
            average_rate=np.mean(metrics),
            trend_direction=self._calculate_trend(metrics),
            recommendations=self._generate_metabolism_recommendations(metrics)
        )
```

#### 智能数据挖掘
```python
# analytics/data_mining.py
class NutritionDataMiner:
    """营养数据挖掘器"""
    
    def __init__(self):
        self.pattern_detector = PatternDetector()
        self.correlation_analyzer = CorrelationAnalyzer()
        self.anomaly_detector = AnomalyDetector()
    
    async def mine_user_patterns(self, user_id: int) -> UserPatternInsights:
        """挖掘用户行为模式"""
        # 获取用户数据
        user_data = await self._get_comprehensive_user_data(user_id)
        
        # 模式检测
        eating_patterns = self.pattern_detector.detect_eating_patterns(user_data)
        health_correlations = self.correlation_analyzer.find_correlations(user_data)
        anomalies = self.anomaly_detector.detect_anomalies(user_data)
        
        return UserPatternInsights(
            eating_patterns=eating_patterns,
            health_correlations=health_correlations,
            anomalies=anomalies,
            actionable_insights=self._generate_insights(
                eating_patterns, health_correlations, anomalies
            )
        )
    
    def detect_eating_patterns(self, user_data):
        """检测饮食模式"""
        patterns = {}
        
        # 时间模式
        patterns['meal_timing'] = self._analyze_meal_timing(user_data.meals)
        
        # 食物偏好模式
        patterns['food_preferences'] = self._analyze_food_preferences(user_data.meals)
        
        # 营养摄入模式
        patterns['nutrition_patterns'] = self._analyze_nutrition_patterns(user_data.nutrition)
        
        # 周期性模式
        patterns['cyclical_patterns'] = self._analyze_cyclical_patterns(user_data)
        
        return patterns
```

### 6. 健康度评估与预警系统

#### 综合健康评分模型
```python
# health_assessment/scorer.py
class HealthScoreCalculator:
    """健康评分计算器"""
    
    def __init__(self):
        self.scoring_models = {
            'nutrition_balance': NutritionBalanceScorer(),
            'dietary_variety': DietaryVarietyScorer(),
            'meal_regularity': MealRegularityScorer(),
            'hydration_status': HydrationScorer(),
            'metabolic_health': MetabolicHealthScorer()
        }
        
        # 权重可根据用户特征动态调整
        self.base_weights = {
            'nutrition_balance': 0.35,
            'dietary_variety': 0.20,
            'meal_regularity': 0.15,
            'hydration_status': 0.15,
            'metabolic_health': 0.15
        }
    
    def calculate_comprehensive_score(self, user_id: int, assessment_period: int = 7):
        """计算综合健康评分"""
        user_data = self._get_user_data(user_id, assessment_period)
        user_profile = self._get_user_profile(user_id)
        
        # 根据用户特征调整权重
        weights = self._adjust_weights_for_user(self.base_weights, user_profile)
        
        scores = {}
        for component, scorer in self.scoring_models.items():
            scores[component] = scorer.calculate_score(user_data, user_profile)
        
        # 加权计算总分
        total_score = sum(scores[comp] * weights[comp] for comp in scores)
        
        return HealthScore(
            total_score=total_score,
            component_scores=scores,
            trend_analysis=self._analyze_score_trend(user_id),
            improvement_suggestions=self._generate_improvement_suggestions(scores)
        )

# 营养平衡评分器示例
class NutritionBalanceScorer:
    def calculate_score(self, user_data, user_profile):
        """计算营养平衡评分"""
        daily_summaries = user_data.daily_summaries
        
        balance_scores = []
        for summary in daily_summaries:
            # 宏量营养素比例评分
            macro_score = self._score_macronutrient_balance(summary)
            
            # 微量营养素充足度评分
            micro_score = self._score_micronutrient_adequacy(summary)
            
            # 热量平衡评分
            calorie_score = self._score_calorie_balance(summary, user_profile)
            
            daily_score = (macro_score * 0.4 + micro_score * 0.3 + calorie_score * 0.3)
            balance_scores.append(daily_score)
        
        return np.mean(balance_scores)
```

#### 智能预警系统
```python
# alerts/warning_system.py
class HealthWarningSystem:
    """健康预警系统"""
    
    def __init__(self):
        self.risk_assessors = {
            'nutrition_deficiency': NutritionDeficiencyAssessor(),
            'chronic_disease_risk': ChronicDiseaseRiskAssessor(),
            'eating_disorder_risk': EatingDisorderRiskAssessor(),
            'metabolic_syndrome_risk': MetabolicSyndromeAssessor()
        }
        
        self.notification_service = NotificationService()
    
    async def assess_health_risks(self, user_id: int):
        """评估健康风险"""
        user_data = await self._get_comprehensive_user_data(user_id)
        user_profile = await self._get_user_profile(user_id)
        
        risk_assessments = {}
        alerts_to_send = []
        
        for risk_type, assessor in self.risk_assessors.items():
            risk_level, details = assessor.assess_risk(user_data, user_profile)
            risk_assessments[risk_type] = {
                'level': risk_level,
                'details': details,
                'confidence': details.confidence
            }
            
            # 生成必要的预警
            if risk_level >= RiskLevel.MEDIUM:
                alert = self._create_alert(risk_type, risk_level, details)
                alerts_to_send.append(alert)
        
        # 发送预警通知
        for alert in alerts_to_send:
            await self.notification_service.send_health_alert(user_id, alert)
        
        return HealthRiskAssessment(
            risk_assessments=risk_assessments,
            overall_risk_level=self._calculate_overall_risk(risk_assessments),
            recommendations=self._generate_risk_mitigation_recommendations(risk_assessments)
        )

# 营养缺乏风险评估器示例
class NutritionDeficiencyAssessor:
    def assess_risk(self, user_data, user_profile):
        """评估营养缺乏风险"""
        recent_intake = user_data.recent_nutrition_summary  # 最近7天
        recommended_intake = self._get_recommended_intake(user_profile)
        
        deficiencies = []
        overall_risk = RiskLevel.LOW
        
        for nutrient, recommended in recommended_intake.items():
            actual = recent_intake.get(nutrient, 0)
            adequacy_ratio = actual / recommended
            
            if adequacy_ratio < 0.5:  # 严重不足
                deficiencies.append({
                    'nutrient': nutrient,
                    'severity': 'severe',
                    'adequacy_ratio': adequacy_ratio
                })
                overall_risk = max(overall_risk, RiskLevel.HIGH)
            elif adequacy_ratio < 0.7:  # 不足
                deficiencies.append({
                    'nutrient': nutrient,
                    'severity': 'moderate',
                    'adequacy_ratio': adequacy_ratio
                })
                overall_risk = max(overall_risk, RiskLevel.MEDIUM)
        
        return overall_risk, DeficiencyDetails(
            deficiencies=deficiencies,
            confidence=self._calculate_confidence(user_data),
            recommendations=self._generate_deficiency_recommendations(deficiencies)
        )
```

### 7. 社交与激励系统

#### 社交化健康管理
```python
# social/family_health.py
class FamilyHealthManager:
    """家庭健康管理"""
    
    def __init__(self):
        self.family_analyzer = FamilyPatternAnalyzer()
        self.group_recommender = GroupRecommendationEngine()
    
    async def create_family_group(self, creator_id: int, family_members: List[int]):
        """创建家庭健康小组"""
        family_group = FamilyGroup(
            creator_id=creator_id,
            members=family_members,
            shared_goals=await self._identify_shared_goals(family_members),
            group_settings=await self._initialize_group_settings(family_members)
        )
        
        # 分析家庭饮食模式
        family_patterns = await self.family_analyzer.analyze_family_patterns(family_members)
        
        # 生成家庭健康计划
        family_plan = await self._generate_family_health_plan(family_group, family_patterns)
        
        return family_group, family_plan
    
    async def generate_family_meal_recommendations(self, family_group_id: int):
        """生成家庭餐食推荐"""
        members = await self._get_family_members(family_group_id)
        
        # 考虑所有成员的健康需求
        combined_requirements = self._combine_health_requirements(members)
        
        # 生成适合全家的餐食推荐
        meal_recommendations = await self.group_recommender.recommend_family_meals(
            combined_requirements
        )
        
        return meal_recommendations

# 健康挑战系统
class HealthChallengeSystem:
    """健康挑战系统"""
    
    def create_challenge(self, challenge_type: str, participants: List[int], duration: int):
        """创建健康挑战"""
        challenge_templates = {
            'water_intake': WaterIntakeChallenge(),
            'vegetable_variety': VegetableVarietyChallenge(),
            'cooking_frequency': CookingFrequencyChallenge(),
            'meal_regularity': MealRegularityChallenge()
        }
        
        challenge = challenge_templates[challenge_type].create(
            participants=participants,
            duration=duration,
            start_date=datetime.now()
        )
        
        return challenge
```

### 8. IoT设备集成框架

#### 设备连接与数据同步
```python
# iot/device_integration.py
class IoTDeviceManager:
    """IoT设备管理器"""
    
    def __init__(self):
        self.device_connectors = {
            'smart_scale': SmartScaleConnector(),
            'fitness_tracker': FitnessTrackerConnector(),
            'smart_kitchen': SmartKitchenConnector(),
            'water_bottle': SmartWaterBottleConnector()
        }
        
        self.data_synchronizer = DataSynchronizer()
    
    async def connect_device(self, user_id: int, device_type: str, device_config: dict):
        """连接IoT设备"""
        connector = self.device_connectors[device_type]
        
        # 设备认证和配对
        device = await connector.authenticate_and_pair(device_config)
        
        # 注册设备到用户账户
        await self._register_device_to_user(user_id, device)
        
        # 启动数据同步
        await self.data_synchronizer.start_sync(device)
        
        return device
    
    async def sync_device_data(self, device_id: str):
        """同步设备数据"""
        device = await self._get_device(device_id)
        connector = self.device_connectors[device.type]
        
        # 获取设备数据
        raw_data = await connector.fetch_data(device)
        
        # 数据清洗和标准化
        cleaned_data = await self._clean_and_standardize_data(raw_data, device.type)
        
        # 存储到数据库
        await self._store_device_data(device.user_id, cleaned_data)
        
        # 触发相关分析
        await self._trigger_analysis_updates(device.user_id, cleaned_data)

# 智能体重秤连接器示例
class SmartScaleConnector:
    async def fetch_data(self, device):
        """获取体重秤数据"""
        # 连接设备API
        scale_data = await self._connect_to_scale_api(device.api_credentials)
        
        return ScaleData(
            weight=scale_data['weight'],
            body_fat_percentage=scale_data.get('body_fat'),
            muscle_mass=scale_data.get('muscle_mass'),
            bone_mass=scale_data.get('bone_mass'),
            water_percentage=scale_data.get('water_percentage'),
            timestamp=scale_data['measured_at']
        )
```

### 9. AR/VR体验模块

#### AR食物识别与展示
```python
# ar_vr/ar_experience.py
class ARFoodExperience:
    """AR食物体验"""
    
    def __init__(self):
        self.ar_renderer = ARRenderer()
        self.nutrition_visualizer = NutritionVisualizer()
        self.portion_estimator = AR3DPortionEstimator()
    
    async def render_nutrition_overlay(self, camera_feed, food_detection_result):
        """渲染营养信息叠加层"""
        # 为每个检测到的食物创建AR标签
        ar_elements = []
        
        for food_item in food_detection_result.detected_foods:
            # 创建3D营养信息卡片
            nutrition_card = await self.nutrition_visualizer.create_3d_card(
                food_item.nutrition_facts
            )
            
            # 定位到食物位置
            positioned_card = self.ar_renderer.position_element(
                nutrition_card,
                world_position=food_item.world_coordinates
            )
            
            ar_elements.append(positioned_card)
        
        # 渲染AR场景
        ar_scene = self.ar_renderer.compose_scene(camera_feed, ar_elements)
        
        return ar_scene
    
    async def estimate_3d_portion(self, food_item, reference_objects):
        """3D分量估算"""
        # 使用参考物体（如硬币、手等）进行尺度校准
        scale_factor = self._calculate_scale_factor(reference_objects)
        
        # 3D重建食物模型
        food_3d_model = await self._reconstruct_3d_model(food_item)
        
        # 计算实际体积和重量
        volume = self._calculate_volume(food_3d_model, scale_factor)
        estimated_weight = self._estimate_weight_from_volume(volume, food_item.density)
        
        return PortionEstimate(
            volume_ml=volume,
            weight_grams=estimated_weight,
            confidence=self._calculate_estimation_confidence(food_3d_model)
        )

# VR营养教育模块
class VRNutritionEducation:
    """VR营养教育"""
    
    def __init__(self):
        self.vr_environment = VREnvironment()
        self.interactive_lessons = InteractiveLessonEngine()
    
    async def create_nutrition_lesson(self, lesson_topic: str, user_level: str):
        """创建VR营养课程"""
        lesson_content = await self.interactive_lessons.generate_lesson(
            topic=lesson_topic,
            difficulty_level=user_level
        )
        
        # 创建VR环境
        vr_scene = self.vr_environment.create_kitchen_scene()
        
        # 添加交互式食材
        interactive_ingredients = self._create_interactive_ingredients(lesson_content.ingredients)
        vr_scene.add_objects(interactive_ingredients)
        
        # 添加虚拟营养师指导
        virtual_nutritionist = self._create_virtual_guide(lesson_content.guidance)
        vr_scene.add_character(virtual_nutritionist)
        
        return VRLesson(
            scene=vr_scene,
            learning_objectives=lesson_content.objectives,
            interactive_tasks=lesson_content.tasks
        )
```

## 🔄 系统集成与数据流

### 数据流架构图（微服务不采用）
```mermaid
graph TB
    A[用户输入] --> B[API网关]
    B --> C[负载均衡器]
    C --> D[微服务集群]
    
    D --> E[用户服务]
    D --> F[AI分析服务]
    D --> G[记录服务]
    D --> H[健康评估服务]
    
    F --> I[LangGraph Agent]
    I --> J[视觉模型]
    I --> K[语言模型]
    
    E --> L[PostgreSQL]
    G --> L
    H --> L
    
    F --> M[Redis缓存]
    G --> N[MinIO对象存储]
    H --> O[ClickHouse分析库]
    
    I --> P[LangMem记忆]
    I --> Q[Milvus向量库]
    
    R[IoT设备] --> S[设备网关]
    S --> G
    
    T[第三方API] --> U[API适配器]
    U --> D
```

### 事件驱动架构
```python
# events/event_system.py
class EventBus:
    """事件总线"""
    
    def __init__(self):
        self.subscribers = defaultdict(list)
        self.message_broker = RabbitMQBroker()
    
    def subscribe(self, event_type: str, handler: Callable):
        """订阅事件"""
        self.subscribers[event_type].append(handler)
    
    async def publish(self, event: Event):
        """发布事件"""
        # 本地处理
        for handler in self.subscribers[event.type]:
            await handler(event)
        
        # 跨服务传播
        await self.message_broker.publish(event.type, event.data)

# 事件定义
@dataclass
class FoodRecordCreatedEvent(Event):
    type = "food_record_created"
    user_id: int
    record_id: int
    food_data: dict
    timestamp: datetime

@dataclass 
class HealthScoreUpdatedEvent(Event):
    type = "health_score_updated"
    user_id: int
    new_score: float
    previous_score: float
    change_reason: str

# 事件处理器示例
class NutritionAnalysisEventHandler:
    async def handle_food_record_created(self, event: FoodRecordCreatedEvent):
        """处理食物记录创建事件"""
        # 触发营养分析
        await self.nutrition_analyzer.analyze_async(event.record_id)
        
        # 更新日总结
        await self.daily_summary_updater.update(event.user_id, event.timestamp.date())
        
        # 检查健康预警
        await self.health_warning_system.check_warnings(event.user_id)
```

## 📈 性能优化策略

### 缓存策略
```python
# cache/strategy.py
class CacheStrategy:
    """缓存策略"""
    
    def __init__(self):
        self.redis_client = RedisClient()
        self.memory_cache = MemoryCache()
    
    async def get_user_nutrition_summary(self, user_id: int, date: date):
        """获取用户营养汇总（带缓存）"""
        cache_key = f"nutrition_summary:{user_id}:{date}"
        
        # L1: 内存缓存
        cached_data = self.memory_cache.get(cache_key)
        if cached_data:
            return cached_data
        
        # L2: Redis缓存
        cached_data = await self.redis_client.get(cache_key)
        if cached_data:
            # 回填L1缓存
            self.memory_cache.set(cache_key, cached_data, ttl=300)
            return cached_data
        
        # L3: 数据库查询
        data = await self._fetch_from_database(user_id, date)
        
        # 更新缓存
        await self.redis_client.setex(cache_key, 3600, data)  # 1小时
        self.memory_cache.set(cache_key, data, ttl=300)       # 5分钟
        
        return data

# 异步任务优化
class AsyncTaskOptimizer:
    """异步任务优化器"""
    
    def __init__(self):
        self.task_queue = CeleryQueue()
        self.batch_processor = BatchProcessor()
    
    async def optimize_nutrition_analysis(self, food_records: List[FoodRecord]):
        """批量优化营养分析"""
        # 按相似性分组
        grouped_records = self._group_by_similarity(food_records)
        
        # 批量处理相似食物
        for group in grouped_records:
            await self.batch_processor.process_similar_foods(group)
```

## 🛡️ 错误处理与容错机制

### 服务容错设计
```python
# resilience/circuit_breaker.py
class CircuitBreaker:
    """熔断器"""
    
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, func, *args, **kwargs):
        """调用受保护的函数"""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise CircuitBreakerOpenException()
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"

# 优雅降级
class GracefulDegradation:
    """优雅降级"""
    
    async def get_nutrition_analysis_with_fallback(self, food_image):
        """带降级的营养分析"""
        try:
            # 尝试AI分析
            return await self.ai_analyzer.analyze(food_image)
        except AIServiceUnavailableException:
            # 降级到基础识别
            return await self.basic_analyzer.analyze(food_image)
        except Exception:
            # 最终降级到手动输入提示
            return self._generate_manual_input_suggestion()
```

这个完善的系统架构设计涵盖了你草稿中提到的所有核心功能，并且提供了具体的实现思路和技术方案。整个架构具有高度的可扩展性、容错性和智能化特性，能够支撑一个完整的AI营养师应用的运行。 