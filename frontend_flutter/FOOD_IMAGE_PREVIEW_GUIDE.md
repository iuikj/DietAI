# 食物图片预览功能使用指南

## 功能概述

本功能允许前端通过后端API获取存储在MinIO中的食物图片，并在Flutter应用中显示。图片数据通过base64编码传输，确保安全性和兼容性。

## 后端API

### 新增API接口

#### 获取食物记录图片数据
```
GET /foods/images/data/{record_id}
```

**参数：**
- `record_id` (路径参数): 食物记录ID

**响应：**
```json
{
  "success": true,
  "message": "获取图片数据成功",
  "data": {
    "record_id": 123,
    "image_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
    "content_type": "image/jpeg",
    "file_size": 102400,
    "object_name": "food_images/1/1234567890.jpg"
  }
}
```

## 前端组件

### 1. FoodImagePreview 组件

用于显示单个食物记录的图片。

```dart
FoodImagePreview(
  foodRecord: foodRecord,
  width: 200,
  height: 150,
  fit: BoxFit.cover,
  showFullScreen: true,
  showLoadingIndicator: true,
)
```

**参数说明：**
- `foodRecord`: 食物记录对象
- `width`: 图片宽度（可选）
- `height`: 图片高度（可选）
- `fit`: 图片适配方式
- `showFullScreen`: 是否支持全屏预览
- `showLoadingIndicator`: 是否显示加载指示器

### 2. FoodImageGridPreview 组件

用于显示多个食物记录的图片网格。

```dart
FoodImageGridPreview(
  foodRecords: foodRecords,
  crossAxisCount: 2,
  spacing: 8.0,
  childAspectRatio: 1.0,
  showFullScreen: true,
)
```

**参数说明：**
- `foodRecords`: 食物记录列表
- `crossAxisCount`: 网格列数
- `spacing`: 网格间距
- `childAspectRatio`: 子项宽高比
- `showFullScreen`: 是否支持全屏预览

### 3. FoodRecordCard 组件

集成了图片预览功能的食物记录卡片。

```dart
FoodRecordCard(
  foodRecord: foodRecord,
  onTap: () {
    // 处理点击事件
  },
  showImage: true,
  showNutrition: true,
)
```

## 配置说明

### API配置

在 `lib/core/constants/api_config.dart` 中配置MinIO地址：

```dart
// MinIO配置
static const String devMinioUrl = 'http://localhost:9000';
static const String devLocalNetworkMinioUrl = 'http://10.70.130.211:9000';
```

### 依赖配置

在 `pubspec.yaml` 中添加必要的依赖：

```yaml
dependencies:
  photo_view: ^0.14.0
  cached_network_image: ^3.3.0
```

## 使用示例

### 1. 在列表页面中使用

```dart
ListView.builder(
  itemCount: foodRecords.length,
  itemBuilder: (context, index) {
    final record = foodRecords[index];
    return FoodRecordCard(
      foodRecord: record,
      onTap: () {
        // 处理点击事件
      },
    );
  },
)
```

### 2. 在详情页面中使用

```dart
Column(
  children: [
    // 其他内容...
    if (foodRecord.imageUrl != null)
      SizedBox(
        height: 200,
        child: FoodImagePreview(
          foodRecord: foodRecord,
          fit: BoxFit.cover,
          showFullScreen: true,
        ),
      ),
  ],
)
```

### 3. 在网格布局中使用

```dart
FoodImageGridPreview(
  foodRecords: foodRecordsWithImages,
  crossAxisCount: 2,
  spacing: 8.0,
)
```

## 功能特性

### 1. 自动加载
- 组件会自动从后端获取图片数据
- 支持加载状态显示
- 错误处理和重试机制

### 2. 全屏预览
- 点击图片可进入全屏预览模式
- 支持缩放和拖动
- 黑色背景，沉浸式体验

### 3. 性能优化
- 图片数据缓存
- 懒加载机制
- 内存管理

### 4. 错误处理
- 网络错误处理
- 图片格式错误处理
- 用户友好的错误提示

## 注意事项

1. **网络配置**：确保前端能够访问后端的8000端口和MinIO的9000端口
2. **图片大小**：建议图片大小不超过10MB，以确保良好的加载性能
3. **权限控制**：后端会验证用户权限，确保用户只能访问自己的图片
4. **缓存策略**：图片数据会缓存在内存中，避免重复请求

## 故障排除

### 1. 图片无法显示
- 检查网络连接
- 确认MinIO服务是否正常运行
- 检查图片URL格式是否正确

### 2. 加载缓慢
- 检查图片文件大小
- 确认网络带宽
- 考虑图片压缩

### 3. 权限错误
- 确认用户已登录
- 检查token是否有效
- 确认图片属于当前用户

## 更新日志

- v1.0.0: 初始版本，支持基本的图片预览功能
- 支持全屏预览和网格布局
- 添加错误处理和加载状态
- 集成到食物记录卡片组件中 