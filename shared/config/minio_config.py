from datetime import timedelta

from minio import Minio
from minio.error import S3Error
import os
from typing import Optional
import io

from .settings import get_settings

settings = get_settings()

class MinioConfig:
    """MinIO配置类"""
    
    def __init__(self):
        self.endpoint = settings.minio_endpoint
        self.access_key = settings.minio_access_key
        self.secret_key = settings.minio_secret_key
        self.secure = settings.minio_secure
        self.bucket_name = settings.minio_bucket
        
    def get_client(self) -> Minio:
        """获取MinIO客户端"""
        return Minio(
            endpoint=self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure
        )

class MinioManager:
    """MinIO管理器"""
    
    def __init__(self, config: MinioConfig = None):
        self.config = config or MinioConfig()
        self.client = None
        self.bucket_name = self.config.bucket_name
        self._initialized = False
    
    def _ensure_initialized(self):
        """确保客户端已初始化"""
        if not self._initialized:
            try:
                self.client = self.config.get_client()
                self._ensure_bucket_exists()
                self._initialized = True
            except Exception as e:
                print(f"MinIO initialization failed: {e}")
                self._initialized = False
                raise
    
    def _ensure_bucket_exists(self):
        """确保bucket存在"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                print(f"Created bucket: {self.bucket_name}")
        except S3Error as e:
            print(f"Error creating bucket: {e}")
    
    def upload_file(self, object_name: str, file_data: bytes, content_type: str = "application/octet-stream") -> bool:
        """上传文件"""
        try:
            self._ensure_initialized()
            # 将bytes转换为流
            file_stream = io.BytesIO(file_data)
            
            # 上传文件
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=file_stream,
                length=len(file_data),
                content_type=content_type
            )
            
            return True
        except S3Error as e:
            print(f"Error uploading file: {e}")
            return False
    
    def upload_file_from_path(self, object_name: str, file_path: str, content_type: str = None) -> bool:
        """从路径上传文件"""
        try:
            self._ensure_initialized()
            self.client.fput_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                file_path=file_path,
                content_type=content_type
            )
            return True
        except S3Error as e:
            print(f"Error uploading file from path: {e}")
            return False
    
    def download_file(self, object_name: str) -> Optional[bytes]:
        """下载文件"""
        try:
            self._ensure_initialized()
            response = self.client.get_object(self.bucket_name, object_name)
            return response.read()
        except S3Error as e:
            print(f"Error downloading file: {e}")
            return None
    
    def download_file_to_path(self, object_name: str, file_path: str) -> bool:
        """下载文件到路径"""
        try:
            self._ensure_initialized()
            self.client.fget_object(self.bucket_name, object_name, file_path)
            return True
        except S3Error as e:
            print(f"Error downloading file to path: {e}")
            return False
    
    def delete_file(self, object_name: str) -> bool:
        """删除文件"""
        try:
            self._ensure_initialized()
            self.client.remove_object(self.bucket_name, object_name)
            return True
        except S3Error as e:
            print(f"Error deleting file: {e}")
            return False
    
    def list_files(self, prefix: str = "") -> list:
        """列出文件"""
        try:
            self._ensure_initialized()
            objects = self.client.list_objects(self.bucket_name, prefix=prefix)
            return [obj.object_name for obj in objects]
        except S3Error as e:
            print(f"Error listing files: {e}")
            return []
    
    def get_file_url(self, object_name: str, expires:timedelta = timedelta(days=7)) -> Optional[str]:
        """获取文件的预签名URL"""
        try:
            self._ensure_initialized()
            url = self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                expires=expires
            )
            return url
        except S3Error as e:
            print(f"Error getting file URL: {e}")
            return None
    
    def get_upload_url(self, object_name: str, expires: int = 3600) -> Optional[str]:
        """获取上传的预签名URL"""
        try:
            self._ensure_initialized()
            url = self.client.presigned_put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                expires=expires
            )
            return url
        except S3Error as e:
            print(f"Error getting upload URL: {e}")
            return None
    
    def file_exists(self, object_name: str) -> bool:
        """检查文件是否存在"""
        try:
            self._ensure_initialized()
            self.client.stat_object(self.bucket_name, object_name)
            return True
        except S3Error:
            return False
    
    def get_file_info(self, object_name: str) -> Optional[dict]:
        """获取文件信息"""
        try:
            self._ensure_initialized()
            stat = self.client.stat_object(self.bucket_name, object_name)
            return {
                "object_name": stat.object_name,
                "size": stat.size,
                "etag": stat.etag,
                "last_modified": stat.last_modified,
                "content_type": stat.content_type,
                "metadata": stat.metadata
            }
        except S3Error as e:
            print(f"Error getting file info: {e}")
            return None

# 全局实例（延迟初始化）
def get_minio_client():
    """获取MinIO客户端实例"""
    global _minio_client
    if '_minio_client' not in globals():
        _minio_client = MinioManager()
    return _minio_client

minio_client = get_minio_client() 