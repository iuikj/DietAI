import redis
import json
from typing import Any, Optional, Union
from datetime import timedelta
import os

from .settings import get_settings

settings = get_settings()


class RedisConfig:
    """Redis配置类"""
    
    def __init__(self):
        self.host = settings.redis_host
        self.port = settings.redis_port
        self.password = settings.redis_password
        self.db = settings.redis_db
        self.decode_responses = True
        self.max_connections = 10
        
    def get_url(self) -> str:
        """获取Redis连接URL"""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class RedisManager:
    """Redis管理器"""
    
    def __init__(self, config: RedisConfig = None):
        self.config = config or RedisConfig()
        self.pool = redis.ConnectionPool(
            host=self.config.host,
            port=self.config.port,
            password=self.config.password,
            db=self.config.db,
            decode_responses=self.config.decode_responses,
            max_connections=self.config.max_connections
        )
        self.client = redis.Redis(connection_pool=self.pool)
        
    def get_client(self) -> redis.Redis:
        """获取Redis客户端"""
        return self.client
    
    def set(self, key: str, value: Any, expire: Optional[Union[int, timedelta]] = None) -> bool:
        """设置缓存"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            
            if expire:
                if isinstance(expire, timedelta):
                    expire = int(expire.total_seconds())
                elif isinstance(expire, int):
                    # 如果是整数，直接使用
                    pass
                else:
                    # 如果是其他类型，尝试转换为整数
                    try:
                        expire = int(expire)
                    except (ValueError, TypeError):
                        print(f"Invalid expire type: {type(expire)}, value: {expire}")
                        return False
                return self.client.setex(key, expire, value)
            else:
                return self.client.set(key, value)
        except Exception as e:
            print(f"Redis set error: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        try:
            value = self.client.get(key)
            if value is None:
                return None
            
            # 尝试解析JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            print(f"Redis get error: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            print(f"Redis delete error: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            print(f"Redis exists error: {e}")
            return False
    
    def expire(self, key: str, seconds: int) -> bool:
        """设置过期时间"""
        try:
            return bool(self.client.expire(key, seconds))
        except Exception as e:
            print(f"Redis expire error: {e}")
            return False
    
    def hset(self, name: str, key: str, value: Any) -> bool:
        """设置哈希字段"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            return bool(self.client.hset(name, key, value))
        except Exception as e:
            print(f"Redis hset error: {e}")
            return False
    
    def hget(self, name: str, key: str) -> Optional[Any]:
        """获取哈希字段"""
        try:
            value = self.client.hget(name, key)
            if value is None:
                return None
            
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            print(f"Redis hget error: {e}")
            return None
    
    def hgetall(self, name: str) -> dict:
        """获取所有哈希字段"""
        try:
            data = self.client.hgetall(name)
            result = {}
            for key, value in data.items():
                try:
                    result[key] = json.loads(value)
                except json.JSONDecodeError:
                    result[key] = value
            return result
        except Exception as e:
            print(f"Redis hgetall error: {e}")
            return {}

class CacheService:
    """缓存服务"""
    
    def __init__(self, redis_manager: RedisManager):
        self.redis = redis_manager
    
    # 用户相关缓存
    def cache_user_profile(self, user_id: int, profile_data: dict, expire_seconds: int = 3600):
        """缓存用户资料"""
        key = f"user:profile:{user_id}"
        return self.redis.set(key, profile_data, expire_seconds)
    
    def get_user_profile(self, user_id: int) -> Optional[dict]:
        """获取用户资料缓存"""
        key = f"user:profile:{user_id}"
        return self.redis.get(key)
    
    def cache_user_session(self, user_id: int, session_data: dict, expire_seconds: int = 1800):
        """缓存用户会话"""
        key = f"user:session:{user_id}"
        return self.redis.set(key, session_data, expire_seconds)
    
    def get_user_session(self, user_id: int) -> Optional[dict]:
        """获取用户会话缓存"""
        key = f"user:session:{user_id}"
        return self.redis.get(key)
    
    # 营养数据缓存
    def cache_daily_nutrition(self, user_id: int, date: str, nutrition_data: dict, expire_seconds: int = 7200):
        """缓存每日营养汇总"""
        key = f"nutrition:daily:{user_id}:{date}"
        return self.redis.set(key, nutrition_data, expire_seconds)
    
    def get_daily_nutrition(self, user_id: int, date: str) -> Optional[dict]:
        """获取每日营养汇总缓存"""
        key = f"nutrition:daily:{user_id}:{date}"
        return self.redis.get(key)
    
    # 食物识别缓存
    def cache_food_analysis(self, image_hash: str, analysis_result: dict, expire_seconds: int = 86400):
        """缓存食物分析结果"""
        key = f"food:analysis:{image_hash}"
        return self.redis.set(key, analysis_result, expire_seconds)
    
    def get_food_analysis(self, image_hash: str) -> Optional[dict]:
        """获取食物分析结果缓存"""
        key = f"food:analysis:{image_hash}"
        return self.redis.get(key)
    
    # 健康评分缓存
    def cache_health_score(self, user_id: int, score_data: dict, expire_seconds: int = 3600):
        """缓存健康评分"""
        key = f"health:score:{user_id}"
        return self.redis.set(key, score_data, expire_seconds)
    
    def get_health_score(self, user_id: int) -> Optional[dict]:
        """获取健康评分缓存"""
        key = f"health:score:{user_id}"
        return self.redis.get(key)
    
    # 对话上下文缓存
    def cache_conversation_context(self, session_id: str, context_data: dict, expire_seconds: int = 1800):
        """缓存对话上下文"""
        key = f"conversation:context:{session_id}"
        return self.redis.set(key, context_data, expire_seconds)
    
    def get_conversation_context(self, session_id: str) -> Optional[dict]:
        """获取对话上下文缓存"""
        key = f"conversation:context:{session_id}"
        return self.redis.get(key)
    
    def clear_user_cache(self, user_id: int):
        """清除用户相关缓存"""
        patterns = [
            f"user:profile:{user_id}",
            f"user:session:{user_id}",
            f"nutrition:daily:{user_id}:*",
            f"health:score:{user_id}"
        ]
        for pattern in patterns:
            if "*" in pattern:
                # 使用SCAN命令查找匹配的键
                keys = self.redis.client.keys(pattern)
                if keys:
                    self.redis.client.delete(*keys)
            else:
                self.redis.delete(pattern)


# 全局实例
redis_manager = RedisManager()
cache_service = CacheService(redis_manager) 