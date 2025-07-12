# DietAI 前端认证系统集成指南

## 概述

本指南介绍如何使用DietAI Flutter应用的认证系统，该系统已与后端API完全集成。

## 功能特性

✅ **用户注册** - 支持用户名、邮箱、密码和可选手机号注册  
✅ **用户登录** - 支持用户名/邮箱登录  
✅ **自动令牌管理** - JWT访问令牌和刷新令牌自动管理  
✅ **令牌刷新** - 自动刷新过期的访问令牌  
✅ **密码修改** - 安全的密码修改功能  
✅ **用户信息获取** - 获取当前登录用户信息  
✅ **退出登录** - 清除本地令牌并退出  
✅ **路由保护** - 自动重定向未认证用户  

## 快速开始

### 1. 配置后端API地址

编辑 `lib/core/constants/api_config.dart` 文件：

```dart
class ApiConfig {
  // 修改为您的后端服务器实际IP地址
  static const String devLocalNetworkUrl = 'http://192.168.1.100:8000';
  
  // 其他配置...
}
```

**重要：** 确保将IP地址修改为运行后端服务的实际IP地址。

### 2. 启动后端服务

确保您的Python FastAPI后端服务在对应端口上运行：

```bash
# 在后端项目目录中
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 运行Flutter应用

```bash
# 在frontend_flutter目录中
flutter run
```

## API接口对应关系

| 功能 | 前端方法 | 后端接口 | 说明 |
|------|----------|----------|------|
| 用户注册 | `AuthService.register()` | `POST /auth/register` | 创建新用户账户 |
| 用户登录 | `AuthService.login()` | `POST /auth/login` | 用户身份验证 |
| 刷新令牌 | `ApiService._refreshToken()` | `POST /auth/refresh-token` | 自动令牌刷新 |
| 获取用户信息 | `AuthService.getCurrentUser()` | `GET /auth/me` | 获取当前用户详情 |
| 修改密码 | `AuthService.changePassword()` | `POST /auth/change-password` | 更新用户密码 |
| 退出登录 | `AuthService.logout()` | `POST /auth/logout` | 用户登出 |
| 验证令牌 | `AuthService.isTokenValid()` | `GET /auth/verify-token` | 检查令牌有效性 |

## 页面和路由

### 认证相关页面

- **登录页面** (`/login`) - `LoginPage`
- **注册页面** (`/register`) - `RegisterPage`  
- **修改密码页面** (`/change-password`) - `ChangePasswordPage`

### 路由保护

应用使用GoRouter实现路由保护：

- 未登录用户自动重定向到登录页面
- 已登录用户无法访问认证页面（会重定向到首页）
- 令牌过期时自动尝试刷新，失败则重定向到登录页面

## 状态管理

使用Riverpod进行状态管理：

```dart
// 监听认证状态
final authState = ref.watch(authStateProvider);

// 获取当前用户
final currentUser = ref.watch(currentUserProvider);

// 检查登录状态
final isLoggedIn = ref.watch(isLoggedInProvider);

// 执行登录
await ref.read(authStateProvider.notifier).login(
  username: 'user@example.com',
  password: 'password123',
);
```

## 数据模型

### 用户模型 (User)
```dart
class User {
  final int id;
  final String username;
  final String email;
  final String? phone;
  final String? avatarUrl;
  final int status;
  final String createdAt;
  final String? lastLoginAt;
}
```

### 请求模型
- `LoginRequest` - 登录请求
- `RegisterRequest` - 注册请求  
- `ChangePasswordRequest` - 密码修改请求

### 响应模型
- `AuthResponse` - 认证响应（包含访问令牌和刷新令牌）
- `ApiResponse<T>` - 通用API响应封装

## 安全特性

### 令牌存储
- 使用 `flutter_secure_storage` 安全存储令牌
- 访问令牌和刷新令牌分别存储
- 应用重启后自动恢复认证状态

### 自动令牌刷新
- API调用返回401时自动尝试刷新令牌
- 刷新成功后重新发送原始请求
- 刷新失败后清除令牌并重定向到登录页面

### 网络拦截器
- 自动添加Authorization头部
- 统一错误处理
- 请求/响应日志记录（仅调试模式）

## 错误处理

### 网络错误
- 连接超时：120秒（AI分析需要较长时间）
- 自动重试失败的令牌刷新请求
- 用户友好的错误消息显示

### 表单验证
- 实时输入验证
- 统一的错误提示样式
- 防止重复提交

## 自定义配置

### 修改超时时间
在 `app_constants.dart` 中：
```dart
static const int requestTimeout = 120000; // 120秒
static const int connectTimeout = 15000; // 15秒
```

### 修改存储键
```dart
static const String accessTokenKey = 'access_token';
static const String refreshTokenKey = 'refresh_token';
```

## 故障排除

### 常见问题

1. **无法连接到后端**
   - 检查 `api_config.dart` 中的IP地址是否正确
   - 确保后端服务正在运行
   - 检查防火墙设置

2. **令牌刷新失败**
   - 检查后端是否支持刷新令牌接口
   - 验证令牌格式是否正确

3. **页面无法加载**
   - 检查路由配置
   - 确认认证状态管理正常工作

### 调试技巧

1. 启用网络日志：
   ```dart
   // 在 api_service.dart 中已启用 PrettyDioLogger
   ```

2. 检查认证状态：
   ```dart
   // 在任何Widget中
   print('当前用户: ${ref.read(currentUserProvider)}');
   print('登录状态: ${ref.read(isLoggedInProvider)}');
   ```

## 最佳实践

1. **安全性**
   - 定期更新依赖包
   - 使用HTTPS（生产环境）
   - 设置合理的令牌过期时间

2. **用户体验**
   - 提供清晰的错误消息
   - 实现加载状态指示
   - 支持自动保存登录状态

3. **性能**
   - 合理设置请求超时时间
   - 实现请求缓存（如需要）
   - 优化网络请求

## 更新历史

- **v1.0.0** - 初始版本，完整的认证功能集成
- 支持所有后端认证接口
- 实现自动令牌管理
- 添加路由保护功能 