from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from shared.models.database import get_db
from shared.models import schemas
from shared.config.redis_config import cache_service

app = FastAPI(title="用户服务", version="1.0.0")
security = HTTPBearer()

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "user-service"}

@app.post("/register", response_model=schemas.BaseResponse)
async def register_user(
    user_data: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    """用户注册"""
    try:
        # TODO: 实现用户注册逻辑
        # 1. 检查用户名和邮箱是否已存在
        # 2. 密码加密
        # 3. 创建用户记录
        # 4. 返回用户信息
        
        return schemas.BaseResponse(
            success=True,
            message="用户注册成功",
            data={"user_id": 1, "username": user_data.username}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"注册失败: {str(e)}"
        )

@app.post("/login", response_model=schemas.BaseResponse)
async def login_user(
    login_data: schemas.UserLogin,
    db: Session = Depends(get_db)
):
    """用户登录"""
    try:
        # TODO: 实现用户登录逻辑
        # 1. 验证用户名和密码
        # 2. 生成JWT token
        # 3. 缓存用户会话
        # 4. 返回token
        
        token_data = {
            "access_token": "mock_access_token",
            "refresh_token": "mock_refresh_token",
            "token_type": "bearer",
            "expires_in": 3600
        }
        
        return schemas.BaseResponse(
            success=True,
            message="登录成功",
            data=token_data
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"登录失败: {str(e)}"
        )

@app.get("/profile", response_model=schemas.BaseResponse)
async def get_user_profile(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """获取用户资料"""
    try:
        # TODO: 实现获取用户资料逻辑
        # 1. 验证token
        # 2. 从缓存或数据库获取用户资料
        # 3. 返回用户资料
        
        user_profile = {
            "id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "real_name": "测试用户",
            "gender": 1,
            "height": 175.0,
            "weight": 70.0,
            "activity_level": 2
        }
        
        return schemas.BaseResponse(
            success=True,
            message="获取用户资料成功",
            data=user_profile
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"获取用户资料失败: {str(e)}"
        )

@app.put("/profile", response_model=schemas.BaseResponse)
async def update_user_profile(
    profile_data: schemas.UserProfileUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """更新用户资料"""
    try:
        # TODO: 实现更新用户资料逻辑
        # 1. 验证token
        # 2. 更新数据库
        # 3. 清除相关缓存
        # 4. 返回更新结果
        
        return schemas.BaseResponse(
            success=True,
            message="用户资料更新成功",
            data=profile_data.dict(exclude_unset=True)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"更新用户资料失败: {str(e)}"
        )

@app.post("/health-goals", response_model=schemas.BaseResponse)
async def create_health_goal(
    goal_data: schemas.HealthGoalCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """创建健康目标"""
    try:
        # TODO: 实现创建健康目标逻辑
        return schemas.BaseResponse(
            success=True,
            message="健康目标创建成功",
            data=goal_data.dict()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"创建健康目标失败: {str(e)}"
        )

@app.get("/health-goals", response_model=schemas.BaseResponse)
async def get_health_goals(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """获取健康目标列表"""
    try:
        # TODO: 实现获取健康目标逻辑
        goals = [
            {
                "id": 1,
                "goal_type": 1,
                "target_weight": 65.0,
                "target_date": "2024-12-31",
                "current_status": 1
            }
        ]
        
        return schemas.BaseResponse(
            success=True,
            message="获取健康目标成功",
            data=goals
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"获取健康目标失败: {str(e)}"
        )

@app.post("/diseases", response_model=schemas.BaseResponse)
async def add_disease(
    disease_data: schemas.DiseaseCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """添加疾病信息"""
    try:
        # TODO: 实现添加疾病信息逻辑
        return schemas.BaseResponse(
            success=True,
            message="疾病信息添加成功",
            data=disease_data.dict()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"添加疾病信息失败: {str(e)}"
        )

@app.post("/allergies", response_model=schemas.BaseResponse)
async def add_allergy(
    allergy_data: schemas.AllergyCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """添加过敏信息"""
    try:
        # TODO: 实现添加过敏信息逻辑
        return schemas.BaseResponse(
            success=True,
            message="过敏信息添加成功",
            data=allergy_data.dict()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"添加过敏信息失败: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 