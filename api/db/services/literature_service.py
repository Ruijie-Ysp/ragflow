#
#  Copyright 2024 The InfiniFlow Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
from peewee import fn

from api.db.db_models import DB, LiteratureProcess, LiteratureAgentResult
from api.db.services.common_service import CommonService
from api.utils import get_uuid, current_timestamp, datetime_format, get_format_time
from datetime import datetime


class LiteratureProcessService(CommonService):
    """文献处理服务类"""
    model = LiteratureProcess

    @classmethod
    @DB.connection_context()
    def get_list(cls, tenant_id, page_number, items_per_page, orderby="create_time",
                 desc=True, keywords="", status=None):
        """获取文献列表"""
        query = cls.model.select().where(
            cls.model.tenant_id == tenant_id,
            cls.model.status == "1"
        )

        if keywords:
            query = query.where(fn.LOWER(cls.model.name).contains(keywords.lower()))

        if status is not None:
            query = query.where(cls.model.process_status == status)

        total = query.count()

        if hasattr(cls.model, orderby):
            if desc:
                query = query.order_by(cls.model.getter_by(orderby).desc())
            else:
                query = query.order_by(cls.model.getter_by(orderby).asc())

        query = query.paginate(page_number, items_per_page)

        literatures = list(query.dicts())

        # 查询每个文献的正在处理中的智能体任务数量
        literature_ids = [lit['id'] for lit in literatures]
        if literature_ids:
            running_counts = (
                LiteratureAgentResult
                .select(LiteratureAgentResult.literature_id, fn.COUNT(LiteratureAgentResult.id).alias('count'))
                .where(
                    LiteratureAgentResult.literature_id.in_(literature_ids),
                    LiteratureAgentResult.status == "0"  # 处理中状态
                )
                .group_by(LiteratureAgentResult.literature_id)
            )
            running_map = {r.literature_id: r.count for r in running_counts}

            for lit in literatures:
                lit['running_agent_count'] = running_map.get(lit['id'], 0)

        return literatures, total

    @classmethod
    @DB.connection_context()
    def create_literature(cls, literature_id, tenant_id, created_by, name, location, size, permission="me"):
        """创建新的文献记录"""
        now = current_timestamp()
        now_date = datetime_format(datetime.now())

        cls.model.create(
            id=literature_id,
            tenant_id=tenant_id,
            created_by=created_by,
            name=name,
            location=location,
            size=size,
            permission=permission,
            process_status="0",
            status="1",
            create_time=now,
            create_date=now_date,
            update_time=now,
            update_date=now_date
        )
        return literature_id

    @classmethod
    @DB.connection_context()
    def update_process_status(cls, literature_id, process_status, process_message=None,
                              markdown_content=None, txt_content=None, process_duration=None):
        """更新处理状态"""
        data = {"process_status": process_status}
        if process_message is not None:
            data["process_message"] = process_message
        if markdown_content is not None:
            data["markdown_content"] = markdown_content
        if txt_content is not None:
            data["txt_content"] = txt_content
        if process_duration is not None:
            data["process_duration"] = process_duration
        return cls.update_by_id(literature_id, data)

    @classmethod
    @DB.connection_context()
    def begin_process(cls, literature_id, parse_method="MinerU"):
        """开始处理"""
        return cls.update_by_id(literature_id, {
            "process_status": "1",
            "process_begin_at": get_format_time(),
            "process_message": "Processing...",
            "parse_method": parse_method
        })

    @classmethod
    @DB.connection_context()
    def soft_delete(cls, literature_id):
        """软删除"""
        return cls.update_by_id(literature_id, {"status": "0"})


class LiteratureAgentResultService(CommonService):
    """智能体处理结果服务类"""
    model = LiteratureAgentResult

    @classmethod
    @DB.connection_context()
    def get_by_literature_id(cls, literature_id, page_number=1, items_per_page=20):
        """获取某文献的所有智能体处理结果"""
        query = cls.model.select().where(
            cls.model.literature_id == literature_id
        ).order_by(cls.model.create_time.desc())
        
        total = query.count()
        query = query.paginate(page_number, items_per_page)
        
        return list(query.dicts()), total

    @classmethod
    @DB.connection_context()
    def create_result(cls, literature_id, agent_id, agent_title, input_content,
                      input_source="markdown", segment_info=None):
        """创建智能体处理结果记录"""
        # 获取当前最大版本号
        max_version = cls.model.select(fn.MAX(cls.model.version)).where(
            cls.model.literature_id == literature_id,
            cls.model.agent_id == agent_id
        ).scalar() or 0

        result_id = get_uuid()
        now = current_timestamp()
        now_date = datetime_format(datetime.now())

        cls.model.create(
            id=result_id,
            literature_id=literature_id,
            agent_id=agent_id,
            agent_title=agent_title,
            version=max_version + 1,
            input_content=input_content,
            input_source=input_source,
            segment_info=segment_info,
            status="0",
            create_time=now,
            create_date=now_date,
            update_time=now,
            update_date=now_date
        )
        return result_id

    @classmethod
    @DB.connection_context()
    def update_result(cls, result_id, status, output_content=None,
                      error_message=None, process_duration=None):
        """更新处理结果"""
        data = {"status": status}
        if output_content is not None:
            data["output_content"] = output_content
        if error_message is not None:
            data["error_message"] = error_message
        if process_duration is not None:
            data["process_duration"] = process_duration
        return cls.update_by_id(result_id, data)

    @classmethod
    @DB.connection_context()
    def delete_result(cls, result_id):
        """删除智能体处理结果"""
        return cls.model.delete().where(cls.model.id == result_id).execute()

