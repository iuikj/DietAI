from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from shared.models.database import get_db
from shared.models.schemas import (
    UserCreate, UserLogin, BaseResponse, TokenResponse, 
    RefreshTokenRequest, PasswordChangeRequest
)
from shared.utils.auth import (
    AuthService, authenticate_user, create_user, 
    get_current_user, update_user_password, update_last_login
)
from shared.models.user_models import User

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=BaseResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    try:
        # 创建用户
        user = create_user(
            db=db,
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            phone=user_data.phone
        )
        
        return BaseResponse(
            success=True,
            message="注册成功",
            data={
                "user_id": user.id,
                "username": user.username,
                "email": user.email
            }
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册失败: {str(e)}"
        )


@router.post("/login", response_model=BaseResponse)
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """用户登录"""
    try:
        # 验证用户
        user = authenticate_user(db, login_data.username, login_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        # 生成令牌
        token_data = AuthService.create_token_pair(user.id, user.username)
        
        # 更新最后登录时间
        update_last_login(db, user)
        
        return BaseResponse(
            success=True,
            message="登录成功",
            data=token_data
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录失败: {str(e)}"
        )


@router.post("/refresh-token", response_model=BaseResponse)
async def refresh_token(refresh_data: RefreshTokenRequest, db: Session = Depends(get_db)):
    """刷新访问令牌"""
    try:
        # 验证刷新令牌
        payload = AuthService.verify_token(refresh_data.refresh_token)
        
        # 检查令牌类型
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="刷新令牌无效"
            )
        
        # 获取用户信息
        user_id = payload.get("sub")
        username = payload.get("username")
        
        if not user_id or not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="令牌信息不完整"
            )
        
        # 验证用户是否存在且有效
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user or user.status != 1:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在或已被禁用"
            )
        
        # 生成新的令牌对
        token_data = AuthService.create_token_pair(user.id, user.username)
        
        return BaseResponse(
            success=True,
            message="令牌刷新成功",
            data=token_data
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"令牌刷新失败: {str(e)}"
        )


@router.post("/logout", response_model=BaseResponse)
async def logout(current_user: User = Depends(get_current_user)):
    """用户登出"""
    try:
        # 这里可以实现令牌黑名单机制
        # 目前简单返回成功，客户端删除令牌即可
        return BaseResponse(
            success=True,
            message="登出成功",
            data={"user_id": current_user.id}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登出失败: {str(e)}"
        )


@router.post("/change-password", response_model=BaseResponse)
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """修改密码"""
    try:
        # 验证旧密码
        if not AuthService.verify_password(password_data.old_password, current_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="旧密码错误"
            )
        
        # 更新密码
        success = update_user_password(db, current_user, password_data.new_password)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="密码更新失败"
            )
        
        return BaseResponse(
            success=True,
            message="密码修改成功",
            data={"user_id": current_user.id}
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"密码修改失败: {str(e)}"
        )


@router.get("/me", response_model=BaseResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    try:
        return BaseResponse(
            success=True,
            message="获取用户信息成功",
            data={
                "id": current_user.id,
                "username": current_user.username,
                "email": current_user.email,
                "phone": current_user.phone,
                "avatar_url": current_user.avatar_url,
                "status": current_user.status,
                "created_at": current_user.created_at,
                "last_login_at": current_user.last_login_at
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户信息失败: {str(e)}"
        )


@router.get("/verify-token", response_model=BaseResponse)
async def verify_token_endpoint(current_user: User = Depends(get_current_user)):
    """验证令牌有效性"""
    try:
        return BaseResponse(
            success=True,
            message="令牌有效",
            data={
                "user_id": current_user.id,
                "username": current_user.username,
                "valid": True
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"令牌验证失败: {str(e)}"
        ) 