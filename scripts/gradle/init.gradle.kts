/**
 * Gradle 全局初始化脚本 — 国内 Maven 镜像
 *
 * 安装位置: ~/.gradle/init.d/china-mirrors.init.gradle.kts
 *
 * 作用: 为所有 Gradle 项目自动注入阿里云 + 华为云 Maven 镜像仓库，
 *       即使 android/ 目录被 Flutter 重新生成，镜像配置也不会丢失。
 */

allprojects {
    buildscript {
        repositories {
            maven { url = uri("https://maven.aliyun.com/repository/public/") }
            maven { url = uri("https://maven.aliyun.com/repository/google/") }
            maven { url = uri("https://maven.aliyun.com/repository/gradle-plugin/") }
            google()
            mavenCentral()
        }
    }

    repositories {
        maven { url = uri("https://maven.aliyun.com/repository/public/") }
        maven { url = uri("https://maven.aliyun.com/repository/google/") }
        maven { url = uri("https://maven.aliyun.com/repository/gradle-plugin/") }
        maven { url = uri("https://mirrors.huaweicloud.com/repository/maven/") }
        google()
        mavenCentral()
    }
}
