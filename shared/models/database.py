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
    pool_size=20,  # 增加连接池大小
    max_overflow=0,  # 不允许连接池溢出
    echo=settings.debug,  # 开发环境显示SQL
    isolation_level="READ_COMMITTED"  # 设置事务隔离级别
)

# 会话工厂
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine,
    expire_on_commit=False  # 防止会话过期问题
)

# 基础模型类
Base = declarative_base()

# 元数据
metadata = MetaData()


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        print(f"数据库会话异常: {str(e)}")
        try:
            db.rollback()
        except Exception as rollback_error:
            print(f"回滚失败: {str(rollback_error)}")
        raise e
    finally:
        try:
            db.close()
        except Exception as close_error:
            print(f"关闭数据库会话失败: {str(close_error)}")


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
