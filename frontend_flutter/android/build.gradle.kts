buildscript {
    repositories {
        maven { url = uri("https://maven.aliyun.com/repository/public/") }
        maven { url = uri("https://maven.aliyun.com/repository/gradle-plugin/") }
        google()
        mavenCentral()
    }
    dependencies {
        // 示例 classpath，如果你需要：
        // classpath("com.android.tools.build:gradle:8.7.3")
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

// 修改默认 build 目录到项目外层的 build 目录
val newBuildDir: Directory = rootProject.layout.buildDirectory.dir("../../build").get()
rootProject.layout.buildDirectory.value(newBuildDir)

subprojects {
    val newSubprojectBuildDir: Directory = newBuildDir.dir(project.name)
    project.layout.buildDirectory.value(newSubprojectBuildDir)

    project.evaluationDependsOn(":app")
}

// 自定义 clean 任务
tasks.register<Delete>("clean") {
    delete(rootProject.layout.buildDirectory)
}