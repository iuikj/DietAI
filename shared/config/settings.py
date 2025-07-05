import os
from functools import lru_cache
from typing import Optional, List
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # 基础配置
    app_name: str = Field(default="DietAI", description="应用名称")
    version: str = Field(default="1.0.0", description="版本号")
    debug: bool = Field(default=False, description="调试模式")
    log_level: str = Field(default="INFO", description="日志级别")

    # 服务器配置
    # host: str = Field(default="0.0.0.0", description="服务器主机")
    host: str = Field(default="localhost", description="服务器主机")
    port: int = Field(default=8000, description="服务器端口")
    reload: bool = Field(default=False, description="热重载")

    # 数据库配置
    database_url: str = Field(
        default="postgresql://postgres:123456@localhost:5432/dietai_db",
        description="数据库连接URL"
    )
    database_echo: bool = Field(default=False, description="是否打印SQL")

    # Redis配置
    redis_host: str = Field(default="localhost", description="Redis主机")
    redis_port: int = Field(default=6379, description="Redis端口")
    redis_password: Optional[str] = Field(default=2168, description="Redis密码")
    redis_db: int = Field(default=5, description="Redis数据库")
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis连接URL")

    # MinIO配置
    minio_endpoint: str = Field(default="localhost:9000", description="MinIO端点")
    minio_access_key: str = Field(default="minioadmin", description="MinIO访问密钥")
    minio_secret_key: str = Field(default="minioadmin", description="MinIO秘密密钥")
    minio_secure: bool = Field(default=False, description="是否使用HTTPS")
    minio_bucket: str = Field(default="dietai-bucket", description="MinIO存储桶")

    # JWT配置
    jwt_secret_key: str = Field(
        default="your-super-secret-jwt-key-change-this-in-production",
        description="JWT密钥"
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT算法")
    jwt_access_token_expire_minutes: int = Field(default=30, description="访问令牌过期时间(分钟)")
    jwt_refresh_token_expire_days: int = Field(default=7, description="刷新令牌过期时间(天)")

    # 密码配置
    password_min_length: int = Field(default=8, description="密码最小长度")
    password_hash_rounds: int = Field(default=12, description="密码哈希轮次")

    # CORS配置
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080", "http://127.0.0.1:3000"],
        description="允许的CORS源"
    )
    cors_methods: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        description="允许的HTTP方法"
    )
    cors_headers: List[str] = Field(
        default=["*"],
        description="允许的HTTP头"
    )

    # 文件上传配置
    max_file_size: int = Field(default=10 * 1024 * 1024, description="最大文件大小(字节)")
    allowed_file_types: List[str] = Field(
        default=["image/jpeg", "image/png", "image/gif"],
        description="允许的文件类型"
    )

    # 邮件配置
    email_enabled: bool = Field(default=False, description="是否启用邮件")
    smtp_host: str = Field(default="smtp.gmail.com", description="SMTP主机")
    smtp_port: int = Field(default=587, description="SMTP端口")
    smtp_user: str = Field(default="", description="SMTP用户名")
    smtp_password: str = Field(default="", description="SMTP密码")
    smtp_use_tls: bool = Field(default=True, description="是否使用TLS")

    # 缓存配置
    cache_default_ttl: int = Field(default=3600, description="默认缓存过期时间(秒)")
    cache_user_profile_ttl: int = Field(default=1800, description="用户资料缓存过期时间(秒)")
    cache_nutrition_ttl: int = Field(default=7200, description="营养数据缓存过期时间(秒)")

    # AI服务配置（预留）
    ai_service_enabled: bool = Field(default=False, description="是否启用AI服务")
    ai_service_url: str = Field(default=" http://127.0.0.1:2024", description="AI服务URL")
    ai_service_timeout: int = Field(default=30, description="AI服务超时时间(秒)")

    # 健康检查配置
    health_check_enabled: bool = Field(default=True, description="是否启用健康检查")
    health_check_interval: int = Field(default=30, description="健康检查间隔(秒)")

    @validator('redis_url', pre=True)
    def build_redis_url(cls, v, values):
        """构建Redis连接URL"""
        if isinstance(v, str) and v.startswith('redis://'):
            return v

        host = values.get('redis_host', 'localhost')
        port = values.get('redis_port', 6379)
        password = values.get('redis_password')
        db = values.get('redis_db', 0)

        if password:
            return f"redis://:{password}@{host}:{port}/{db}"
        return f"redis://{host}:{port}/{db}"

    @validator('cors_origins', pre=True)
    def parse_cors_origins(cls, v):
        """解析CORS源"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v

    @validator('cors_methods', pre=True)
    def parse_cors_methods(cls, v):
        """解析CORS方法"""
        if isinstance(v, str):
            return [method.strip() for method in v.split(',')]
        return v

    @validator('allowed_file_types', pre=True)
    def parse_allowed_file_types(cls, v):
        """解析允许的文件类型"""
        if isinstance(v, str):
            return [file_type.strip() for file_type in v.split(',')]
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "DIETAI_"
        case_sensitive = False
        extra = "ignore"  # 忽略额外字段


@lru_cache()
def get_settings() -> Settings:
    """获取应用配置（带缓存）"""
    return Settings()


# 导出常用配置
settings = get_settings()
