#!/bin/bash
# 测试任务队列清理脚本

echo "=========================================="
echo "测试任务队列清理脚本"
echo "=========================================="
echo ""

# 检查Python环境
echo "1. 检查Python环境..."
python --version
if [ $? -ne 0 ]; then
    echo "❌ Python未安装或不在PATH中"
    exit 1
fi
echo "✓ Python环境正常"
echo ""

# 检查脚本是否存在
echo "2. 检查脚本文件..."
if [ ! -f "scripts/clear_task_queue.py" ]; then
    echo "❌ 脚本文件不存在: scripts/clear_task_queue.py"
    exit 1
fi
echo "✓ 脚本文件存在"
echo ""

# 测试帮助信息
echo "3. 测试帮助信息..."
python scripts/clear_task_queue.py --help
if [ $? -ne 0 ]; then
    echo "❌ 脚本执行失败"
    exit 1
fi
echo "✓ 帮助信息正常"
echo ""

# 测试预览模式
echo "4. 测试预览模式..."
python scripts/clear_task_queue.py --all --dry-run
if [ $? -ne 0 ]; then
    echo "❌ 预览模式执行失败"
    exit 1
fi
echo "✓ 预览模式正常"
echo ""

echo "=========================================="
echo "✓ 所有测试通过!"
echo "=========================================="
echo ""
echo "提示: 可以使用以下命令清理任务队列:"
echo "  python scripts/clear_task_queue.py --all"

