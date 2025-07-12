-- -- 创建数据库
-- CREATE DATABASE dietagent;

-- 连接到dietagent数据库
\c dietagent;
-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

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

-- 长期记忆管理表
CREATE TABLE user_memory_contexts (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    memory_type INTEGER, -- 1:饮食习惯 2:健康状态 3:偏好记录 4:行为模式
    context_key VARCHAR(100),
    context_value JSONB,
    importance_score DECIMAL(3,2), -- 重要性评分 0-1
    last_accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP -- 记忆过期时间
);

-- 创建索引
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_food_records_user_date ON food_records(user_id, record_date);
CREATE INDEX idx_nutrition_details_food_record ON nutrition_details(food_record_id);
CREATE INDEX idx_daily_summary_user_date ON daily_nutrition_summary(user_id, summary_date);
CREATE INDEX idx_conversation_sessions_user ON conversation_sessions(user_id);
CREATE INDEX idx_conversation_messages_session ON conversation_messages(session_id);
CREATE INDEX idx_user_memory_contexts_user_type ON user_memory_contexts(user_id, memory_type, importance_score);

-- 插入测试数据
INSERT INTO users (username, email, password_hash, salt) VALUES 
('testuser', 'test@example.com', 'hashed_password', 'salt123');

-- 创建默认用户配置
INSERT INTO user_profiles (user_id, real_name, gender, height, weight, activity_level) VALUES 
(1, '测试用户', 1, 175.0, 70.0, 2);

INSERT INTO user_health_goals (user_id, goal_type, target_weight, target_date) VALUES 
(1, 1, 65.0, '2024-12-31');

INSERT INTO user_preferences (user_id, dietary_restrictions, spice_tolerance) VALUES 
(1, '["vegetarian"]', 3);

COMMIT; 