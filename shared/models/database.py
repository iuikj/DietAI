from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os

# 导入配置
from ..config.settings import get_settings

settings = get_settings()

# 创建数据库引擎
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={"client_encoding": "utf8"},
    echo=settings.debug  # 开发环境显示SQL
)

# 会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 基础模型类
Base = declarative_base()

# 元数据
metadata = MetaData()


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db():
    """获取异步数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        await db.close()


def create_tables():
    """创建所有数据库表"""
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """删除所有数据库表"""
    Base.metadata.drop_all(bind=engine)


def get_database_url() -> str:
    """获取数据库连接URL"""
    return settings.database_url
