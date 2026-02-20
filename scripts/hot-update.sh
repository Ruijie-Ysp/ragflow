#!/bin/bash
# RAGFlow 热更新脚本 - 将本地代码更新到运行中的容器

set -e

CONTAINER_NAME="ragflow-server"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "======================================"
echo "RAGFlow 热更新脚本"
echo "项目目录: $PROJECT_DIR"
echo "容器名称: $CONTAINER_NAME"
echo "======================================"

# 检查容器是否运行
if ! docker ps | grep -q $CONTAINER_NAME; then
    echo "错误: 容器 $CONTAINER_NAME 未运行"
    exit 1
fi

# 更新后端文件
update_backend() {
    echo ""
    echo ">>> 更新后端 Python 文件..."
    
    # 复制 API 文件
    docker cp "$PROJECT_DIR/api/apps/literature_app.py" $CONTAINER_NAME:/ragflow/api/apps/
    echo "  ✓ literature_app.py"
    
    # 复制 Service 文件
    docker cp "$PROJECT_DIR/api/db/services/literature_service.py" $CONTAINER_NAME:/ragflow/api/db/services/
    echo "  ✓ literature_service.py"
    
    # 复制 MinerU 客户端
    docker cp "$PROJECT_DIR/api/utils/mineru_client.py" $CONTAINER_NAME:/ragflow/api/utils/
    echo "  ✓ mineru_client.py"
    
    # 复制数据库模型
    docker cp "$PROJECT_DIR/api/db/db_models.py" $CONTAINER_NAME:/ragflow/api/db/
    echo "  ✓ db_models.py"
    
    echo ">>> 后端文件更新完成"
}

# 更新前端文件
update_frontend() {
    echo ""
    echo ">>> 编译前端..."
    cd "$PROJECT_DIR/web"
    npm run build
    
    echo ">>> 复制前端文件到容器..."
    docker cp dist/. $CONTAINER_NAME:/ragflow/web/dist/
    echo "  ✓ web/dist/"
    
    echo ">>> 重载 nginx..."
    docker exec $CONTAINER_NAME nginx -s reload
    echo ">>> 前端更新完成"
}

# 重启后端服务
restart_backend() {
    echo ""
    echo ">>> 重启后端服务..."
    docker exec $CONTAINER_NAME pkill -f ragflow_server.py || true
    sleep 2
    echo ">>> 后端服务已重启（自动恢复中...）"
}

# 主逻辑
case "${1:-all}" in
    backend)
        update_backend
        restart_backend
        ;;
    frontend)
        update_frontend
        ;;
    all)
        update_backend
        update_frontend
        restart_backend
        ;;
    *)
        echo "用法: $0 [backend|frontend|all]"
        echo "  backend  - 只更新后端 Python 文件"
        echo "  frontend - 只更新前端（需要编译）"
        echo "  all      - 更新所有（默认）"
        exit 1
        ;;
esac

echo ""
echo "======================================"
echo "热更新完成！"
echo "查看日志: docker logs -f $CONTAINER_NAME"
echo "======================================"

