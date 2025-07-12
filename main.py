import uvicorn
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging
import time
from datetime import datetime

# 导入配置
from shared.config.settings import get_settings
from shared.models.database import create_tables, engine
from shared.models import user_models, food_models, conversation_models

# 导入路由
from routers.auth_router import router as auth_router
from routers.user_router import router as user_router
from routers.food_router import router as food_router
from routers.health_router import router as health_router
from routers.chat_router import router as chat_router
from routers.analysis_chat_router import router as analysis_chat_router

settings = get_settings()

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("正在启动DietAI后端服务...")
    
    # 创建数据库表
    try:
        create_tables()
        logger.info("数据库表创建完成")
    except Exception as e:
        logger.error(f"数据库表创建失败: {e}")
        raise
    
    # 测试数据库连接
    try:
        with engine.connect() as conn:
            logger.info("数据库连接测试成功")
    except Exception as e:
        logger.error(f"数据库连接测试失败: {e}")
        raise
    
    logger.info("DietAI后端服务启动完成")
    yield
    
    # 关闭时执行
    logger.info("正在关闭DietAI后端服务...")

# 创建FastAPI应用
app = FastAPI(
    title="DietAI Backend API",
    description="DietAI智能饮食健康管理后端服务",
    version=settings.version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)

# 添加受信任主机中间件
if not settings.debug:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # 生产环境应该配置具体的域名
    )


# 自定义中间件
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """添加请求处理时间头"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录请求日志"""
    start_time = time.time()
    
    # 记录请求信息
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"请求开始: {request.method} {request.url} - IP: {client_ip}")
    
    response = await call_next(request)
    
    # 记录响应信息
    process_time = time.time() - start_time
    logger.info(f"请求完成: {request.method} {request.url} - 状态码: {response.status_code} - 耗时: {process_time:.4f}s")
    
    return response


# 全局异常处理
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "error_code": f"HTTP_{exc.status_code}",
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """请求验证异常处理"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "请求参数验证失败",
            "error_code": "VALIDATION_ERROR",
            "details": exc.errors(),
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    logger.error(f"未处理的异常: {type(exc).__name__}: {str(exc)}")
    
    if settings.debug:
        # 开发环境返回详细错误信息
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "服务器内部错误",
                "error_code": "INTERNAL_ERROR",
                "details": str(exc),
                "timestamp": datetime.now().isoformat()
            }
        )
    else:
        # 生产环境返回通用错误信息
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "服务器内部错误，请稍后重试",
                "error_code": "INTERNAL_ERROR",
                "timestamp": datetime.now().isoformat()
            }
        )


# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "DietAI Backend API",
        "version": settings.version,
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


# 健康检查
@app.get("/health")
async def health_check():
    """健康检查"""
    try:
        # 检查数据库连接
        with engine.connect() as conn:
            db_status = "healthy"
    except Exception as e:
        logger.error(f"数据库健康检查失败: {e}")
        db_status = "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" else "unhealthy",
        "database": db_status,
        "timestamp": datetime.now().isoformat(),
        "version": settings.version
    }


# 注册路由
app.include_router(auth_router, prefix="/api", tags=["认证"])
app.include_router(user_router, prefix="/api", tags=["用户"])
app.include_router(food_router, prefix="/api", tags=["食物"])
app.include_router(health_router, prefix="/api", tags=["健康"])
app.include_router(chat_router, prefix="/api", tags=["AI对话"])
app.include_router(analysis_chat_router, prefix="/api", tags=["分析页面聊天"])

# 启动服务器
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
