#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理RAGFlow任务队列的脚本

该脚本用于清理Redis中的任务队列,包括:
1. 清理Redis Stream队列中的所有任务
2. 清理数据库中的任务记录
3. 清理任务取消标记
4. 重置文档处理状态

使用方法:
    python scripts/clear_task_queue.py [选项]

选项:
    --queue-only        只清理Redis队列,不清理数据库
    --db-only          只清理数据库任务记录,不清理Redis队列
    --doc-id DOC_ID    只清理指定文档的任务
    --all              清理所有任务(默认)
    --dry-run          预览将要清理的内容,不实际执行
"""

import sys
import os
import logging
import argparse

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from rag.utils.redis_conn import REDIS_CONN
from rag.settings import get_svr_queue_names, SVR_CONSUMER_GROUP_NAME
from api.db.services.task_service import TaskService
from api.db.services.document_service import DocumentService
from api.db.db_models import Task

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TaskQueueCleaner:
    """任务队列清理器"""
    
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.redis = REDIS_CONN.REDIS
        self.queue_names = get_svr_queue_names()
        
    def clear_redis_queues(self, doc_id=None):
        """
        清理Redis队列
        
        Args:
            doc_id: 如果指定,只清理该文档的任务;否则清理所有任务
        """
        logger.info("=" * 60)
        logger.info("开始清理Redis任务队列")
        logger.info("=" * 60)
        
        total_cleared = 0
        
        for queue_name in self.queue_names:
            logger.info(f"\n处理队列: {queue_name}")
            
            try:
                # 获取队列长度
                queue_length = self.redis.xlen(queue_name)
                logger.info(f"  队列长度: {queue_length}")
                
                if queue_length == 0:
                    logger.info(f"  队列为空,跳过")
                    continue
                
                if doc_id:
                    # 只清理指定文档的任务
                    cleared = self._clear_queue_by_doc_id(queue_name, doc_id)
                    total_cleared += cleared
                else:
                    # 清理整个队列
                    if self.dry_run:
                        logger.info(f"  [预览模式] 将删除 {queue_length} 个任务")
                    else:
                        # 删除整个stream
                        self.redis.delete(queue_name)
                        logger.info(f"  ✓ 已删除队列 {queue_name} (共 {queue_length} 个任务)")
                        total_cleared += queue_length
                        
                        # 重新创建consumer group
                        try:
                            self.redis.xgroup_create(queue_name, SVR_CONSUMER_GROUP_NAME, id="0", mkstream=True)
                            logger.info(f"  ✓ 已重新创建consumer group")
                        except Exception as e:
                            if "BUSYGROUP" not in str(e):
                                logger.warning(f"  重新创建consumer group失败: {e}")
                
            except Exception as e:
                logger.error(f"  ✗ 清理队列 {queue_name} 失败: {e}")
                
        logger.info(f"\n总计清理Redis任务: {total_cleared} 个")
        return total_cleared
    
    def _clear_queue_by_doc_id(self, queue_name, doc_id):
        """清理指定文档的任务"""
        cleared = 0
        
        try:
            # 读取所有消息
            messages = self.redis.xrange(queue_name, '-', '+')
            
            for msg_id, msg_data in messages:
                try:
                    import json
                    task_data = json.loads(msg_data.get('message', '{}'))
                    
                    if task_data.get('doc_id') == doc_id:
                        if self.dry_run:
                            logger.info(f"  [预览模式] 将删除任务: {msg_id} (doc_id: {doc_id})")
                        else:
                            self.redis.xdel(queue_name, msg_id)
                            logger.info(f"  ✓ 已删除任务: {msg_id}")
                        cleared += 1
                        
                except Exception as e:
                    logger.warning(f"  处理消息 {msg_id} 失败: {e}")
                    
        except Exception as e:
            logger.error(f"  读取队列消息失败: {e}")
            
        return cleared
    
    def clear_cancel_flags(self, doc_id=None):
        """
        清理任务取消标记
        
        Args:
            doc_id: 如果指定,只清理该文档的任务标记
        """
        logger.info("\n" + "=" * 60)
        logger.info("开始清理任务取消标记")
        logger.info("=" * 60)
        
        cleared = 0
        
        try:
            if doc_id:
                # 获取指定文档的所有任务
                tasks = TaskService.query(doc_id=doc_id)
                for task in tasks:
                    cancel_key = f"{task.id}-cancel"
                    if self.redis.exists(cancel_key):
                        if self.dry_run:
                            logger.info(f"  [预览模式] 将删除取消标记: {cancel_key}")
                        else:
                            self.redis.delete(cancel_key)
                            logger.info(f"  ✓ 已删除取消标记: {cancel_key}")
                        cleared += 1
            else:
                # 扫描所有取消标记
                cursor = 0
                while True:
                    cursor, keys = self.redis.scan(cursor, match="*-cancel", count=100)
                    
                    for key in keys:
                        if self.dry_run:
                            logger.info(f"  [预览模式] 将删除取消标记: {key}")
                        else:
                            self.redis.delete(key)
                            logger.info(f"  ✓ 已删除取消标记: {key}")
                        cleared += 1
                    
                    if cursor == 0:
                        break
                        
        except Exception as e:
            logger.error(f"  ✗ 清理取消标记失败: {e}")
            
        logger.info(f"\n总计清理取消标记: {cleared} 个")
        return cleared
    
    def clear_database_tasks(self, doc_id=None):
        """
        清理数据库中的任务记录
        
        Args:
            doc_id: 如果指定,只清理该文档的任务
        """
        logger.info("\n" + "=" * 60)
        logger.info("开始清理数据库任务记录")
        logger.info("=" * 60)
        
        try:
            if doc_id:
                # 清理指定文档的任务
                tasks = TaskService.query(doc_id=doc_id)
                task_count = len(list(tasks))
                
                if self.dry_run:
                    logger.info(f"  [预览模式] 将删除 {task_count} 个任务记录 (doc_id: {doc_id})")
                else:
                    TaskService.filter_delete([Task.doc_id == doc_id])
                    logger.info(f"  ✓ 已删除 {task_count} 个任务记录 (doc_id: {doc_id})")
                    
                    # 重置文档状态
                    DocumentService.update_by_id(doc_id, {
                        "progress": 0,
                        "progress_msg": "",
                        "run": "0"
                    })
                    logger.info(f"  ✓ 已重置文档状态")
                    
                return task_count
            else:
                # 清理所有任务
                all_tasks = list(Task.select())
                task_count = len(all_tasks)
                
                if self.dry_run:
                    logger.info(f"  [预览模式] 将删除 {task_count} 个任务记录")
                else:
                    Task.delete().execute()
                    logger.info(f"  ✓ 已删除 {task_count} 个任务记录")
                    
                    # 重置所有文档状态
                    from api.db.db_models import Document
                    Document.update(progress=0, progress_msg="", run="0").execute()
                    logger.info(f"  ✓ 已重置所有文档状态")
                    
                return task_count
                
        except Exception as e:
            logger.error(f"  ✗ 清理数据库任务失败: {e}")
            return 0


def main():
    parser = argparse.ArgumentParser(
        description='清理RAGFlow任务队列',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 清理所有任务(Redis队列 + 数据库)
  python scripts/clear_task_queue.py --all
  
  # 只清理Redis队列
  python scripts/clear_task_queue.py --queue-only
  
  # 只清理数据库任务记录
  python scripts/clear_task_queue.py --db-only
  
  # 清理指定文档的任务
  python scripts/clear_task_queue.py --doc-id abc123
  
  # 预览模式(不实际执行)
  python scripts/clear_task_queue.py --all --dry-run
        """
    )
    
    parser.add_argument('--queue-only', action='store_true',
                        help='只清理Redis队列,不清理数据库')
    parser.add_argument('--db-only', action='store_true',
                        help='只清理数据库任务记录,不清理Redis队列')
    parser.add_argument('--doc-id', type=str,
                        help='只清理指定文档的任务')
    parser.add_argument('--all', action='store_true',
                        help='清理所有任务(默认)')
    parser.add_argument('--dry-run', action='store_true',
                        help='预览模式,不实际执行清理操作')
    
    args = parser.parse_args()
    
    # 默认清理所有
    if not args.queue_only and not args.db_only:
        args.all = True
    
    if args.dry_run:
        logger.warning("\n" + "!" * 60)
        logger.warning("预览模式 - 不会实际执行清理操作")
        logger.warning("!" * 60 + "\n")
    
    cleaner = TaskQueueCleaner(dry_run=args.dry_run)
    
    try:
        # 清理Redis队列
        if args.all or args.queue_only:
            cleaner.clear_redis_queues(doc_id=args.doc_id)
            cleaner.clear_cancel_flags(doc_id=args.doc_id)
        
        # 清理数据库
        if args.all or args.db_only:
            cleaner.clear_database_tasks(doc_id=args.doc_id)
        
        logger.info("\n" + "=" * 60)
        logger.info("✓ 清理完成!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"\n✗ 清理失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

