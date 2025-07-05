#!/usr/bin/env python3
"""
测试Redis修复的简单脚本
"""

import sys
import os
from datetime import timedelta

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared.config.redis_config import redis_manager

def test_redis_expire_types():
    """测试Redis过期时间类型处理"""
    print("正在测试Redis过期时间类型处理...")
    
    # 测试1: 整数类型
    try:
        result = redis_manager.set("test:int", "value1", 300)
        print(f"✅ 整数类型过期时间测试: {result}")
    except Exception as e:
        print(f"❌ 整数类型过期时间测试失败: {e}")
    
    # 测试2: timedelta类型
    try:
        result = redis_manager.set("test:timedelta", "value2", timedelta(minutes=5))
        print(f"✅ timedelta类型过期时间测试: {result}")
    except Exception as e:
        print(f"❌ timedelta类型过期时间测试失败: {e}")
    
    # 测试3: 字符串类型（应该被转换为整数）
    try:
        result = redis_manager.set("test:string", "value3", "600")
        print(f"✅ 字符串类型过期时间测试: {result}")
    except Exception as e:
        print(f"❌ 字符串类型过期时间测试失败: {e}")
    
    # 测试4: 无效类型（应该返回False）
    try:
        result = redis_manager.set("test:invalid", "value4", {"invalid": "type"})
        print(f"✅ 无效类型过期时间测试: {result} (应该为False)")
    except Exception as e:
        print(f"❌ 无效类型过期时间测试失败: {e}")
    
    # 清理测试数据
    redis_manager.delete("test:int")
    redis_manager.delete("test:timedelta")
    redis_manager.delete("test:string")
    redis_manager.delete("test:invalid")
    
    print("✅ 测试完成！")

if __name__ == "__main__":
    test_redis_expire_types() 