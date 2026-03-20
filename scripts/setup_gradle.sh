#!/usr/bin/env bash
# ============================================================
# DietAI Gradle 环境一键配置脚本
#
# 功能:
#   1. 将国内 Maven 镜像脚本安装到 ~/.gradle/init.d/
#   2. 将 JVM 内存 + 代理配置合并到 ~/.gradle/gradle.properties
#
# 这些全局配置不依赖项目的 android/ 目录，
# 即使 Flutter 重建 android/ 文件夹，配置也会自动生效。
#
# 用法:
#   bash scripts/setup_gradle.sh          # 安装全部
#   bash scripts/setup_gradle.sh --no-proxy  # 安装但不配置代理
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GRADLE_HOME="${HOME}/.gradle"
INIT_DIR="${GRADLE_HOME}/init.d"
GLOBAL_PROPS="${GRADLE_HOME}/gradle.properties"

NO_PROXY=false
if [[ "${1:-}" == "--no-proxy" ]]; then
    NO_PROXY=true
fi

echo "========================================"
echo "  DietAI Gradle 环境配置"
echo "========================================"
echo ""

# --- 1. 安装 Maven 镜像初始化脚本 ---
echo "[1/2] 安装国内 Maven 镜像..."
mkdir -p "${INIT_DIR}"
cp "${SCRIPT_DIR}/gradle/init.gradle.kts" "${INIT_DIR}/china-mirrors.init.gradle.kts"
echo "  ✓ 已安装到: ${INIT_DIR}/china-mirrors.init.gradle.kts"
echo ""

# --- 2. 配置 gradle.properties ---
echo "[2/2] 配置 JVM 内存和网络代理..."

# 备份已有配置
if [[ -f "${GLOBAL_PROPS}" ]]; then
    cp "${GLOBAL_PROPS}" "${GLOBAL_PROPS}.bak.$(date +%Y%m%d%H%M%S)"
    echo "  ✓ 已备份原配置"
fi

if [[ "${NO_PROXY}" == true ]]; then
    # 只写 JVM 参数，不写代理
    cat > "${GLOBAL_PROPS}" << 'PROPS'
# DietAI Gradle 全局配置 (无代理模式)
org.gradle.jvmargs=-Xmx8G -XX:MaxMetaspaceSize=4G -XX:ReservedCodeCacheSize=512m -XX:+HeapDumpOnOutOfMemoryError
PROPS
    echo "  ✓ 已配置 JVM 参数 (无代理)"
else
    cp "${SCRIPT_DIR}/gradle/gradle.properties" "${GLOBAL_PROPS}"
    echo "  ✓ 已配置 JVM 参数 + 代理 (端口 7890)"
    echo ""
    echo "  ⚠ 代理端口默认为 7890 (Clash)，如需修改请编辑:"
    echo "    ${GLOBAL_PROPS}"
fi

echo ""
echo "========================================"
echo "  配置完成！"
echo "========================================"
echo ""
echo "已安装的全局配置:"
echo "  • Maven 镜像: ${INIT_DIR}/china-mirrors.init.gradle.kts"
echo "  • JVM/代理:   ${GLOBAL_PROPS}"
echo ""
echo "这些配置会自动应用到本机所有 Gradle 项目，"
echo "即使 Flutter 重建 android/ 目录也不受影响。"
