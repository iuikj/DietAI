# DietAI Flutter 部署指南

> 本文档详细说明如何将 DietAI Flutter 应用部署到 Android 手机上，重点记录了与 Flutter 默认 Gradle 配置的所有差异，以及因网络环境导致的常见部署问题和解决方案。

---

## 目录

1. [环境准备](#1-环境准备)
2. [项目配置概览](#2-项目配置概览)
3. [与默认 Gradle 配置的差异（重点）](#3-与默认-gradle-配置的差异重点)
4. [后端服务部署](#4-后端服务部署)
5. [Flutter 应用构建与安装](#5-flutter-应用构建与安装)
6. [网络配置详解](#6-网络配置详解)
7. [常见问题与故障排除](#7-常见问题与故障排除)
8. [配置清单速查表](#8-配置清单速查表)

---

## 1. 环境准备

### 1.1 必需工具

| 工具 | 最低版本 | 说明 |
|------|---------|------|
| Flutter SDK | >= 3.10.0 | 当前稳定频道 |
| Dart SDK | >= 3.0.0 | 随 Flutter 附带 |
| Android SDK | API 34+ | 需安装 Build Tools、Platform Tools |
| Android NDK | 27.0.12077973 | **必须与项目一致**（见下方说明） |
| Java / JDK | 11 | **不要使用 17+**，可能导致兼容性问题 |
| Gradle | 8.12 | 由 gradle-wrapper 自动管理 |

### 1.2 验证环境

```bash
flutter doctor -v
```

确认输出中以下项目全部通过：
- Flutter（版本 >= 3.10.0）
- Android toolchain
- Connected device（已连接手机或模拟器）

### 1.3 手机准备

1. 进入 **设置 → 关于手机**，连续点击 **版本号** 7 次，开启**开发者模式**
2. 进入 **设置 → 开发者选项**：
   - 开启 **USB 调试**
   - 开启 **USB 安装**（部分品牌手机需要）
   - 关闭 **MIUI 优化**（小米手机）或关闭类似的厂商安全限制
3. 用 USB 线连接电脑，手机弹窗选择 **允许 USB 调试**
4. 验证连接：
   ```bash
   flutter devices
   # 或
   adb devices
   ```

---

## 2. 项目配置概览

### 2.1 技术栈版本

```
Flutter SDK:          >= 3.10.0 (stable)
Dart SDK:             >= 3.0.0 < 4.0.0
Android Gradle Plugin: 8.7.3
Gradle:               8.12
Kotlin:               2.1.0
Java:                 11
NDK:                  27.0.12077973
```

### 2.2 项目文件结构（Android 相关）

```
frontend_flutter/
├── android/
│   ├── build.gradle.kts          ← 根级构建脚本（已大量修改）
│   ├── settings.gradle.kts       ← Gradle 设置（已修改插件版本）
│   ├── gradle.properties         ← 全局属性（已大量修改）
│   ├── local.properties          ← 本地 SDK 路径（需每人修改）
│   ├── gradle/wrapper/
│   │   └── gradle-wrapper.properties  ← Gradle 版本（已升级）
│   └── app/
│       └── build.gradle.kts      ← 应用级构建脚本（已修改 NDK）
```

---

## 3. 与默认 Gradle 配置的差异（重点）

> **这是本文档最核心的部分。** 以下逐文件列出本项目对 Flutter 默认生成的 Android 配置所做的所有修改，以及修改原因。

### 3.1 `gradle.properties` — JVM 内存 + 代理配置

#### 默认配置

```properties
org.gradle.jvmargs=-Xmx4G
android.useAndroidX=true
android.enableJetifier=true
```

#### 本项目配置

```properties
org.gradle.jvmargs=-Xmx8G -XX:MaxMetaspaceSize=4G -XX:ReservedCodeCacheSize=512m -XX:+HeapDumpOnOutOfMemoryError
android.useAndroidX=true
android.enableJetifier=true
systemProp.http.proxyHost=127.0.0.1
systemProp.http.proxyPort=7890
systemProp.https.proxyHost=127.0.0.1
systemProp.https.proxyPort=7890
systemProp.socks.proxyHost=127.0.0.1
systemProp.socks.proxyPort=7890
```

#### 差异说明

| 配置项 | 默认值 | 修改后 | 修改原因 |
|--------|--------|--------|---------|
| `-Xmx` | 4G | **8G** | 项目依赖较多（camera、riverpod、dio 等），编译时 JVM 堆内存不足会导致 `OutOfMemoryError`，提升到 8G 保证大型项目稳定编译 |
| `-XX:MaxMetaspaceSize` | 无 | **4G** | 防止类加载器占用过多元空间导致 OOM |
| `-XX:ReservedCodeCacheSize` | 无 | **512m** | 提升 JIT 编译缓存，加速重复编译 |
| `-XX:+HeapDumpOnOutOfMemoryError` | 无 | **启用** | OOM 时自动生成堆转储文件，便于排查构建失败 |
| `systemProp.http.proxyHost/Port` | 无 | **127.0.0.1:7890** | **国内网络环境**无法直接访问 Google Maven/Gradle 仓库，需通过本地代理下载依赖 |
| `systemProp.https.proxyHost/Port` | 无 | **127.0.0.1:7890** | HTTPS 代理，同上 |
| `systemProp.socks.proxyHost/Port` | 无 | **127.0.0.1:7890** | SOCKS5 代理，覆盖部分使用 SOCKS 协议的下载 |

> **部署注意：** 代理端口 `7890` 是 Clash 的默认端口。**你需要根据自己的代理软件修改这些端口号**，或在不需要代理时**注释掉或删除**这 6 行代理配置。常见代理端口参考：
> - Clash: HTTP/SOCKS5 通常 `7890`
> - V2Ray: HTTP 通常 `10809`，SOCKS5 通常 `10808`
> - SSR: HTTP 通常 `1080`
> - 如果已配置阿里云镜像仓库（见 3.2），且不需要访问 Google 直连仓库，可以完全删除代理配置

---

### 3.2 `build.gradle.kts`（根级）— Maven 仓库镜像

#### 默认配置

```kotlin
allprojects {
    repositories {
        google()
        mavenCentral()
    }
}
```

#### 本项目配置

```kotlin
buildscript {
    repositories {
        maven { url = uri("https://maven.aliyun.com/repository/public/") }
        maven { url = uri("https://maven.aliyun.com/repository/gradle-plugin/") }
        google()
        mavenCentral()
    }
}

allprojects {
    repositories {
        google()
        mavenCentral()
        maven { url = uri("https://maven.aliyun.com/repository/public/") }
        maven { url = uri("https://maven.aliyun.com/repository/google/") }
        maven { url = uri("https://maven.aliyun.com/repository/gradle-plugin/") }
        maven { url = uri("https://mirrors.huaweicloud.com/repository/maven/") }
    }
}
```

#### 差异说明

| 修改 | 说明 |
|------|------|
| 新增 `buildscript.repositories` 块 | 默认 Flutter 项目不包含此块，添加阿里云镜像确保 Gradle 插件本身能快速下载 |
| 新增 **阿里云 public 仓库** | 加速 Maven Central 依赖下载，国内速度从 KB/s 提升到 MB/s |
| 新增 **阿里云 google 仓库** | Google Maven 仓库的国内镜像，解决 `dl.google.com` 被墙/超慢的问题 |
| 新增 **阿里云 gradle-plugin 仓库** | Gradle 插件的国内镜像 |
| 新增 **华为云 Maven 仓库** | 作为阿里云的备选镜像，提高下载成功率 |

> **关键点：** 这些镜像仓库是**国内开发必备**的。如果不添加，首次 `flutter build apk` 可能会卡在依赖下载环节数小时甚至失败。

---

### 3.3 `settings.gradle.kts` — 插件版本升级

#### 默认配置（Flutter 3.10 生成）

```kotlin
plugins {
    id("dev.flutter.flutter-plugin-loader") version "1.0.0"
    id("com.android.application") version "8.1.0" apply false
    id("org.jetbrains.kotlin.android") version "1.9.0" apply false
}
```

#### 本项目配置

```kotlin
plugins {
    id("dev.flutter.flutter-plugin-loader") version "1.0.0"
    id("com.android.application") version "8.7.3" apply false
    id("org.jetbrains.kotlin.android") version "2.1.0" apply false
}
```

#### 差异说明

| 插件 | 默认版本 | 修改后 | 修改原因 |
|------|---------|--------|---------|
| Android Gradle Plugin | 8.1.0 | **8.7.3** | 支持最新的编译工具链和 API 35+，修复旧版本的已知 bug |
| Kotlin | 1.9.0 | **2.1.0** | 部分依赖库（如 `flutter_secure_storage`）要求 Kotlin 2.0+，旧版本会编译报错 |

---

### 3.4 `gradle-wrapper.properties` — Gradle 版本升级

#### 默认配置

```properties
distributionUrl=https\://services.gradle.org/distributions/gradle-8.3-all.zip
```

#### 本项目配置

```properties
distributionUrl=https\://services.gradle.org/distributions/gradle-8.12-all.zip
```

#### 差异说明

| 项目 | 默认 | 修改后 | 修改原因 |
|------|------|--------|---------|
| Gradle 版本 | 8.3 | **8.12** | Android Gradle Plugin 8.7.3 **强制要求** Gradle >= 8.9，使用 8.12 获得最佳兼容性和构建性能 |

> **注意：** Gradle 版本与 AGP 版本有严格的对应关系。如果 Gradle 版本过低会直接报错：
> ```
> Minimum supported Gradle version is 8.9. Current version is 8.3.
> ```

---

### 3.5 `app/build.gradle.kts` — NDK 版本指定

#### 默认配置

```kotlin
android {
    compileSdk = flutter.compileSdkVersion
    // 没有 ndkVersion 配置
}
```

#### 本项目配置

```kotlin
android {
    compileSdk = flutter.compileSdkVersion
    ndkVersion = "27.0.12077973"
}
```

#### 差异说明

| 项目 | 默认 | 修改后 | 修改原因 |
|------|------|--------|---------|
| NDK 版本 | 未指定 | **27.0.12077973** | `camera` 和 `image` 等插件包含 C/C++ 原生代码，需要 NDK 编译。不指定版本时 Gradle 会使用系统安装的任意版本，可能导致 ABI 不兼容。显式指定确保所有开发者使用相同的 NDK。|

> **部署操作：** 确保通过 Android SDK Manager 安装了该版本 NDK：
> ```
> Android Studio → SDK Manager → SDK Tools → NDK (Side by side) → 勾选 27.0.12077973
> ```
> 或命令行：
> ```bash
> sdkmanager "ndk;27.0.12077973"
> ```

---

### 3.6 `local.properties` — 本地路径配置

#### 说明

此文件**不提交到 Git**（已在 `.gitignore` 中），每个开发者需要根据自己的环境创建。

```properties
sdk.dir=D:\\DevelopFiles\\Android_sdk          # 修改为你的 Android SDK 路径
flutter.sdk=D:\\DevelopFiles\\flutter           # 修改为你的 Flutter SDK 路径
flutter.buildMode=debug
flutter.versionName=1.0.0
flutter.versionCode=1
```

> **注意：** Windows 路径使用双反斜杠 `\\`。如果你的 SDK 安装在默认位置：
> ```properties
> # Windows 默认
> sdk.dir=C:\\Users\\<用户名>\\AppData\\Local\\Android\\Sdk
> flutter.sdk=C:\\src\\flutter
>
> # macOS 默认
> sdk.dir=/Users/<用户名>/Library/Android/sdk
> flutter.sdk=/Users/<用户名>/flutter
>
> # Linux 默认
> sdk.dir=/home/<用户名>/Android/Sdk
> flutter.sdk=/home/<用户名>/flutter
> ```

---

### 3.7 差异总结表

| 文件 | 修改项 | 原因分类 |
|------|--------|---------|
| `gradle.properties` | JVM 内存增大到 8G | 性能优化 |
| `gradle.properties` | 添加 HTTP/HTTPS/SOCKS 代理 | **国内网络** |
| `build.gradle.kts` | 添加阿里云 + 华为云 Maven 镜像 | **国内网络** |
| `settings.gradle.kts` | AGP 升级到 8.7.3 | 依赖兼容性 |
| `settings.gradle.kts` | Kotlin 升级到 2.1.0 | 依赖兼容性 |
| `gradle-wrapper.properties` | Gradle 升级到 8.12 | AGP 版本要求 |
| `app/build.gradle.kts` | 指定 NDK 27.0.12077973 | 原生插件编译 |
| `local.properties` | 自定义 SDK 路径 | 本地环境适配 |

---

## 4. 后端服务部署

Flutter 应用需要连接后端 API 才能正常工作。以下是后端启动步骤。

### 4.1 使用 Docker（推荐）

```bash
# 在项目根目录执行
cd D:\DevelopFiles\AIGC\DietAI

# 启动数据服务（PostgreSQL + Redis + MinIO）
docker-compose up -d postgres redis minio

# 等待服务就绪后，初始化数据库
alembic upgrade head

# 启动后端 API
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 启动 LangGraph AI 代理（另开终端）
langgraph dev --port 2024
```

### 4.2 手动部署数据服务

如果不使用 Docker，需分别安装并配置：
- PostgreSQL 15+（创建数据库 `dietai_db`）
- Redis 7+（设置密码 `2168`）
- MinIO（默认用户名密码 `minioadmin/minioadmin`）

### 4.3 环境变量配置

复制 `env.example` 为 `.env`，填入 API 密钥：

```bash
cp env.example .env
```

必填项：
```
OPENAI_API_KEY=sk-xxx        # AI 图像分析必需
REDIS_PASSWORD=2168           # Redis 密码
```

---

## 5. Flutter 应用构建与安装

### 5.1 修改 API 地址（关键步骤）

编辑 `lib/core/constants/api_config.dart`，将 IP 地址改为你电脑的局域网 IP：

```dart
class ApiConfig {
  static const String devBaseUrl = 'http://localhost:8000';
  static const String devLocalNetworkUrl = 'http://<你的电脑IP>:8000';  // ← 修改这里

  static const String devMinioUrl = 'http://localhost:9000';
  static const String devLocalNetworkMinioUrl = 'http://<你的电脑IP>:9000';  // ← 修改这里
}
```

**查看电脑 IP 的方法：**
```bash
# Windows
ipconfig
# 找到 "无线局域网适配器 WLAN" 下的 IPv4 地址，如 192.168.0.136

# macOS / Linux
ifconfig | grep "inet "
# 或
ip addr show | grep "inet "
```

> **为什么需要改 IP？**
> 手机通过 USB 或 WiFi 连接时，`localhost` 指的是手机本身，而不是你的电脑。必须使用电脑的局域网 IP 才能让手机访问电脑上运行的后端服务。

### 5.2 安装依赖

```bash
cd frontend_flutter

# 安装 Dart 依赖
flutter pub get

# 生成序列化代码（如果修改了 model）
flutter packages pub run build_runner build --delete-conflicting-outputs
```

### 5.3 Debug 模式安装到手机

```bash
# 确认手机已连接
flutter devices

# 安装并运行（debug 模式，支持热重载）
flutter run
# 如果有多个设备，指定设备
flutter run -d <device_id>
```

### 5.4 Release 模式构建 APK

```bash
# 构建 release APK
flutter build apk

# APK 输出位置
# build/app/outputs/flutter-apk/app-release.apk

# 构建分架构 APK（体积更小）
flutter build apk --split-per-abi
# 输出:
# app-armeabi-v7a-release.apk   (32位 ARM，老设备)
# app-arm64-v8a-release.apk     (64位 ARM，大多数现代手机)
# app-x86_64-release.apk        (x86 模拟器)
```

### 5.5 直接安装 APK 到手机

```bash
# 通过 adb 安装
adb install build/app/outputs/flutter-apk/app-release.apk

# 如果已安装旧版本
adb install -r build/app/outputs/flutter-apk/app-release.apk
```

---

## 6. 网络配置详解

### 6.1 Gradle 依赖下载（构建时）

构建时 Gradle 需要从以下仓库下载 Android 编译工具和依赖库：

```
Google Maven (dl.google.com)         → 阿里云镜像替代
Maven Central (repo1.maven.org)      → 阿里云镜像替代
Gradle Plugin Portal (plugins.gradle.org)  → 阿里云镜像替代
Gradle Distribution (services.gradle.org)  → 需代理或手动下载
```

**方案选择：**

| 方案 | 适用场景 | 操作 |
|------|---------|------|
| **方案 A：镜像 + 代理** | 有代理软件 | 保留 `build.gradle.kts` 中的镜像，同时在 `gradle.properties` 中配置代理端口 |
| **方案 B：仅镜像** | 无代理软件 | 保留 `build.gradle.kts` 中的镜像，**删除** `gradle.properties` 中的代理配置 |
| **方案 C：仅代理** | 代理稳定 | 可删除镜像配置，仅保留代理 |

> **推荐方案 B**，因为阿里云 + 华为云镜像已经覆盖了绝大多数依赖。只有极少数新发布的包可能需要直连 Google。

### 6.2 Gradle Distribution 下载

首次构建时 Gradle Wrapper 会下载 `gradle-8.12-all.zip`（约 250MB）。如果下载缓慢：

**方案 1：使用代理**
确保 `gradle.properties` 中的代理配置正确。

**方案 2：手动下载放置**
1. 从镜像站下载：`https://mirrors.cloud.tencent.com/gradle/gradle-8.12-all.zip`
2. 计算文件 URL 的哈希作为目录名：
   ```bash
   # 找到 Gradle 缓存目录
   # Windows: C:\Users\<用户名>\.gradle\wrapper\dists\gradle-8.12-all\<hash>\
   # macOS/Linux: ~/.gradle/wrapper/dists/gradle-8.12-all/<hash>/
   ```
3. 将下载的 zip 放入对应 `<hash>` 目录即可

**方案 3：修改为腾讯云镜像源**
编辑 `gradle-wrapper.properties`：
```properties
distributionUrl=https\://mirrors.cloud.tencent.com/gradle/gradle-8.12-all.zip
```

### 6.3 Flutter App 运行时网络（运行时）

应用运行时的网络请求流向：

```
手机 App
   ├─→ http://<电脑IP>:8000/api/*       (FastAPI 后端)
   └─→ http://<电脑IP>:9000/*           (MinIO 图片存储)
```

**确保以下条件：**
1. 手机和电脑在**同一局域网**（连同一个 WiFi）
2. 电脑防火墙允许 `8000` 和 `9000` 端口入站
3. `api_config.dart` 中的 IP 地址正确

**Windows 防火墙放行：**
```powershell
# 以管理员身份运行 PowerShell
netsh advfirewall firewall add rule name="DietAI-Backend" dir=in action=allow protocol=TCP localport=8000
netsh advfirewall firewall add rule name="DietAI-MinIO" dir=in action=allow protocol=TCP localport=9000
```

### 6.4 Android 明文 HTTP 流量

Android 9 (API 28) 及以上版本默认禁止明文 HTTP 流量。本项目在 debug 和 profile 模式下通过 `AndroidManifest.xml` 已声明 `INTERNET` 权限，但**未配置 `network_security_config.xml`**。

如果在 release 模式下遇到网络请求失败，需要添加网络安全配置：

**步骤 1：创建** `android/app/src/main/res/xml/network_security_config.xml`
```xml
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <domain-config cleartextTrafficPermitted="true">
        <domain includeSubdomains="true">192.168.0.136</domain>
        <!-- 添加你的开发服务器IP -->
        <domain includeSubdomains="true">10.0.2.2</domain>
        <!-- Android 模拟器访问宿主机 -->
    </domain-config>
</network-security-config>
```

**步骤 2：在** `AndroidManifest.xml` 的 `<application>` 标签中添加引用
```xml
<application
    android:networkSecurityConfig="@xml/network_security_config"
    android:label="dietai_flutter"
    ...>
```

> **注意：** 生产环境应使用 HTTPS，不需要此配置。

---

## 7. 常见问题与故障排除

### 7.1 Gradle 构建失败

#### 问题：`Could not resolve all files for configuration`

```
> Could not resolve com.android.tools.build:gradle:8.7.3
```

**原因：** 无法从 Google Maven 下载 AGP。

**解决：**
1. 确认 `build.gradle.kts` 中已添加阿里云镜像
2. 确认代理配置正确，或关闭代理配置
3. 清理缓存重试：
   ```bash
   cd android
   ./gradlew clean
   cd ..
   flutter clean
   flutter pub get
   flutter run
   ```

#### 问题：`OutOfMemoryError: Java heap space`

**原因：** JVM 堆内存不足。

**解决：** 确认 `gradle.properties` 中 `-Xmx` 至少为 `4G`，推荐 `8G`。

#### 问题：`Minimum supported Gradle version is X.X`

**原因：** Gradle 版本与 AGP 不匹配。

**解决：** 确保 `gradle-wrapper.properties` 中的 Gradle 版本与 AGP 版本兼容：

| AGP 版本 | 最低 Gradle 版本 |
|----------|-----------------|
| 8.7.x | 8.9 |
| 8.5.x | 8.7 |
| 8.3.x | 8.4 |
| 8.1.x | 8.0 |

#### 问题：`NDK not configured` 或 `No version of NDK matched`

**原因：** 未安装指定版本的 NDK。

**解决：**
```bash
# 通过命令行安装
sdkmanager "ndk;27.0.12077973"

# 或通过 Android Studio:
# SDK Manager → SDK Tools → 勾选 "Show Package Details"
# → NDK (Side by side) → 勾选 27.0.12077973
```

---

### 7.2 网络请求失败

#### 问题：手机连不上后端 API

**排查步骤：**

1. **检查 IP 地址**：`api_config.dart` 中的 IP 必须是电脑的局域网 IP
2. **检查同一网络**：手机和电脑连接同一 WiFi
3. **检查后端运行**：在电脑浏览器访问 `http://<IP>:8000/docs` 能打开
4. **检查防火墙**：暂时关闭 Windows 防火墙测试
5. **检查端口**：
   ```bash
   # 在手机的浏览器中访问
   http://<电脑IP>:8000/docs
   ```
6. **检查 Android 明文 HTTP**：如果是 release 包，需要配置 `network_security_config.xml`

#### 问题：图片无法加载（MinIO）

**原因：** MinIO 服务地址配置错误或未启动。

**解决：**
1. 确认 MinIO 服务已启动：`docker-compose up -d minio`
2. 确认 `api_config.dart` 中 MinIO URL 配置正确
3. 确认 MinIO 控制台可访问：`http://<IP>:9001`

#### 问题：AI 分析超时

**原因：** AI 图像分析需要调用外部 API（OpenAI），请求时间较长。

**解决：** 本项目已将请求超时设为 120 秒（`AppConstants.requestTimeout = 120000`），一般无需修改。如果仍然超时，检查后端的 OpenAI API Key 是否有效。

---

### 7.3 构建环境问题

#### 问题：`flutter pub get` 缓慢

**解决：** 配置 Flutter 和 Dart 的国内镜像：
```bash
# Windows (PowerShell)
$env:PUB_HOSTED_URL = "https://pub.flutter-io.cn"
$env:FLUTTER_STORAGE_BASE_URL = "https://storage.flutter-io.cn"

# macOS / Linux
export PUB_HOSTED_URL=https://pub.flutter-io.cn
export FLUTTER_STORAGE_BASE_URL=https://storage.flutter-io.cn

# 建议添加到系统环境变量或 shell 配置文件中（.bashrc / .zshrc）
```

#### 问题：代理冲突导致构建失败

**症状：** 配置了代理但代理软件未运行，导致所有请求都超时。

**解决：** 如果不使用代理，**必须删除或注释** `gradle.properties` 中的全部 6 行代理配置：
```properties
# systemProp.http.proxyHost=127.0.0.1
# systemProp.http.proxyPort=7890
# systemProp.https.proxyHost=127.0.0.1
# systemProp.https.proxyPort=7890
# systemProp.socks.proxyHost=127.0.0.1
# systemProp.socks.proxyPort=7890
```

> **这是新开发者最常遇到的问题之一。** 如果代理端口不对或代理未运行，Gradle 构建会一直卡住直到超时失败。

---

### 7.4 设备相关问题

#### 问题：`flutter run` 提示 "No connected devices"

**解决：**
1. 确认 USB 连接正常，手机已授权调试
2. 安装手机品牌的 USB 驱动
3. 尝试：
   ```bash
   adb kill-server
   adb start-server
   adb devices
   ```

#### 问题：小米手机安装失败

**解决：**
1. 开启 **开发者选项 → USB 安装**
2. 关闭 **MIUI 优化**
3. 登录小米账号（部分 MIUI 版本要求）
4. 使用 `flutter run --release` 代替 debug 模式

#### 问题：华为/荣耀手机安装失败

**解决：**
1. 关闭 **纯净模式**（设置 → 安全 → 更多安全设置）
2. 或在开发者选项中允许 **安装未知来源应用**

---

## 8. 配置清单速查表

新开发者克隆项目后，按以下清单逐项配置：

### 构建环境清单

- [ ] 安装 Flutter SDK >= 3.10.0
- [ ] 安装 Android SDK（API 34+）
- [ ] 安装 NDK 27.0.12077973
- [ ] 安装 JDK 11
- [ ] `flutter doctor` 全部通过

### 文件修改清单

- [ ] **`android/local.properties`** — 修改 `sdk.dir` 和 `flutter.sdk` 为你的本地路径
- [ ] **`android/gradle.properties`** — 确认代理配置（`systemProp.*` 6 行），默认 `7890`（Clash），如使用其他代理软件需修改端口
- [ ] **`lib/core/constants/api_config.dart`** — 修改 `devLocalNetworkUrl` 和 `devLocalNetworkMinioUrl` 为你的电脑 IP
- [ ] **系统环境变量** — 设置 `PUB_HOSTED_URL` 和 `FLUTTER_STORAGE_BASE_URL`（国内镜像）

### 后端服务清单

- [ ] PostgreSQL 运行在 `localhost:5432`
- [ ] Redis 运行在 `localhost:6379`
- [ ] MinIO 运行在 `localhost:9000`
- [ ] FastAPI 后端运行在 `0.0.0.0:8000`
- [ ] LangGraph 代理运行在 `localhost:2024`
- [ ] `.env` 文件已配置 API 密钥

### 手机调试清单

- [ ] 开启开发者模式 + USB 调试
- [ ] USB 线连接并授权
- [ ] 手机和电脑在同一局域网
- [ ] 电脑防火墙放行 8000 和 9000 端口
- [ ] `flutter devices` 能看到设备

---

## 附录：版本兼容矩阵

| 组件 | 当前版本 | 备注 |
|------|---------|------|
| Flutter SDK | >= 3.10.0 stable | `flutter --version` 确认 |
| Dart SDK | >= 3.0.0 < 4.0.0 | 随 Flutter 自带 |
| Android Gradle Plugin | 8.7.3 | `settings.gradle.kts` |
| Gradle | 8.12 | `gradle-wrapper.properties` |
| Kotlin | 2.1.0 | `settings.gradle.kts` |
| Java / JDK | 11 | `app/build.gradle.kts` → `jvmTarget` |
| NDK | 27.0.12077973 | `app/build.gradle.kts` |
| compileSdk | 由 Flutter 决定 | 通常 34 或 35 |
| minSdk | 由 Flutter 决定 | 通常 21 |
| targetSdk | 由 Flutter 决定 | 通常 34 |

---

*文档创建日期: 2026-03-20*
*项目版本: 1.0.0*
