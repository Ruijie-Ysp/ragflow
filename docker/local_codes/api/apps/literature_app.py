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
import time
import logging
from flask import request
from flask_login import current_user, login_required

from api import settings
from api.constants import FILE_NAME_LEN_LIMIT
from api.db.services.literature_service import LiteratureProcessService, LiteratureAgentResultService
from api.utils import get_uuid
from api.utils.api_utils import get_json_result, server_error_response, validate_request
from api.utils.mineru_client import mineru_client
from rag.utils.storage_factory import STORAGE_IMPL


@manager.route("/list", methods=["GET"])  # noqa: F821
@login_required
def list_literatures():
    """获取文献列表"""
    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 20))
        keywords = request.args.get("keywords", "")
        orderby = request.args.get("orderby", "create_time")
        desc = request.args.get("desc", "true").lower() == "true"
        status = request.args.get("status", None)
        
        literatures, total = LiteratureProcessService.get_list(
            tenant_id=current_user.id,
            page_number=page,
            items_per_page=page_size,
            orderby=orderby,
            desc=desc,
            keywords=keywords,
            status=status
        )
        
        return get_json_result(data={"list": literatures, "total": total})
    except Exception as e:
        logging.exception("list_literatures error")
        return server_error_response(e)


@manager.route("/upload", methods=["POST"])  # noqa: F821
@login_required
def upload_literature():
    """上传文献文件"""
    try:
        if "file" not in request.files:
            return get_json_result(data=False, message="No file part!", code=settings.RetCode.ARGUMENT_ERROR)
        
        file_obj = request.files["file"]
        if file_obj.filename == "":
            return get_json_result(data=False, message="No file selected!", code=settings.RetCode.ARGUMENT_ERROR)
        
        filename = file_obj.filename
        if len(filename.encode("utf-8")) > FILE_NAME_LEN_LIMIT:
            return get_json_result(data=False, message=f"File name must be {FILE_NAME_LEN_LIMIT} bytes or less.", 
                                   code=settings.RetCode.ARGUMENT_ERROR)
        
        if not filename.lower().endswith(".pdf"):
            return get_json_result(data=False, message="Only PDF files are supported!", 
                                   code=settings.RetCode.ARGUMENT_ERROR)
        
        permission = request.form.get("permission", "me")
        
        # 读取文件内容
        file_content = file_obj.read()
        file_size = len(file_content)
        
        # 存储到 MinIO (使用用户专属bucket)
        literature_id = get_uuid()
        bucket = f"{current_user.id}-literature"
        location = f"{literature_id}/{filename}"
        STORAGE_IMPL.put(bucket, location, file_content)

        # 创建数据库记录
        LiteratureProcessService.create_literature(
            literature_id=literature_id,
            tenant_id=current_user.id,
            created_by=current_user.id,
            name=filename,
            location=location,
            size=file_size,
            permission=permission
        )

        # 获取创建的记录
        e, literature = LiteratureProcessService.get_by_id(literature_id)

        return get_json_result(data=literature.to_dict() if e else {"id": literature_id, "name": filename})
    except Exception as e:
        logging.exception("upload_literature error")
        return server_error_response(e)


@manager.route("/<literature_id>", methods=["GET"])  # noqa: F821
@login_required
def get_literature(literature_id):
    """获取文献详情"""
    try:
        e, literature = LiteratureProcessService.get_by_id(literature_id)
        if not e:
            return get_json_result(data=False, message="Literature not found", code=settings.RetCode.DATA_ERROR)
        
        return get_json_result(data=literature.to_dict())
    except Exception as e:
        logging.exception("get_literature error")
        return server_error_response(e)


@manager.route("/<literature_id>", methods=["DELETE"])  # noqa: F821
@login_required
def delete_literature(literature_id):
    """删除文献"""
    try:
        e, literature = LiteratureProcessService.get_by_id(literature_id)
        if not e:
            return get_json_result(data=False, message="Literature not found", code=settings.RetCode.DATA_ERROR)
        
        if literature.tenant_id != current_user.id:
            return get_json_result(data=False, message="No permission", code=settings.RetCode.AUTHENTICATION_ERROR)
        
        LiteratureProcessService.soft_delete(literature_id)
        return get_json_result(data=True)
    except Exception as e:
        logging.exception("delete_literature error")
        return server_error_response(e)


@manager.route("/<literature_id>/process", methods=["POST"])  # noqa: F821
@login_required
def process_literature(literature_id):
    """使用 MinerU 处理文献"""
    try:
        e, literature = LiteratureProcessService.get_by_id(literature_id)
        if not e:
            return get_json_result(data=False, message="Literature not found", code=settings.RetCode.DATA_ERROR)
        
        if literature.tenant_id != current_user.id:
            return get_json_result(data=False, message="No permission", code=settings.RetCode.AUTHENTICATION_ERROR)
        
        if literature.process_status == "1":
            return get_json_result(data=False, message="Already processing", code=settings.RetCode.ARGUMENT_ERROR)
        
        # 标记开始处理
        LiteratureProcessService.begin_process(literature_id)

        start_time = time.time()

        # 从 MinIO 获取文件
        bucket = f"{literature.tenant_id}-literature"
        file_content = STORAGE_IMPL.get(bucket, literature.location)
        
        # 调用 MinerU
        success, markdown, txt, message = mineru_client.parse_pdf(file_content, literature.name)
        
        duration = time.time() - start_time
        
        if success:
            LiteratureProcessService.update_process_status(
                literature_id=literature_id,
                process_status="2",
                process_message="Success",
                markdown_content=markdown,
                txt_content=txt,
                process_duration=duration
            )
        else:
            LiteratureProcessService.update_process_status(
                literature_id=literature_id,
                process_status="3",
                process_message=message,
                process_duration=duration
            )
        
        # 返回更新后的记录
        e, literature = LiteratureProcessService.get_by_id(literature_id)
        return get_json_result(data=literature.to_dict() if e else {"id": literature_id, "success": success})
    except Exception as e:
        logging.exception("process_literature error")
        LiteratureProcessService.update_process_status(
            literature_id=literature_id,
            process_status="3",
            process_message=str(e)
        )
        return server_error_response(e)


@manager.route("/<literature_id>/file", methods=["GET"])  # noqa: F821
@login_required
def get_literature_file(literature_id):
    """获取文献原始文件"""
    from flask import send_file
    from io import BytesIO
    try:
        e, literature = LiteratureProcessService.get_by_id(literature_id)
        if not e:
            return get_json_result(data=False, message="Literature not found", code=settings.RetCode.DATA_ERROR)

        bucket = f"{literature.tenant_id}-literature"
        file_content = STORAGE_IMPL.get(bucket, literature.location)
        return send_file(
            BytesIO(file_content),
            mimetype='application/pdf',
            as_attachment=False,
            download_name=literature.name
        )
    except Exception as e:
        logging.exception("get_literature_file error")
        return server_error_response(e)


@manager.route("/<literature_id>/agent_results", methods=["GET"])  # noqa: F821
@login_required
def list_agent_results(literature_id):
    """获取智能体处理结果列表"""
    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 20))

        results, total = LiteratureAgentResultService.get_by_literature_id(
            literature_id=literature_id,
            page_number=page,
            items_per_page=page_size
        )

        return get_json_result(data={"list": results, "total": total})
    except Exception as e:
        logging.exception("list_agent_results error")
        return server_error_response(e)


@manager.route("/<literature_id>/run_agent", methods=["POST"])  # noqa: F821
@login_required
@validate_request("agent_id")
def run_agent(literature_id):
    """使用智能体处理文献"""
    import json
    from agent.canvas import Canvas
    from api.db.services.canvas_service import UserCanvasService
    try:
        e, literature = LiteratureProcessService.get_by_id(literature_id)
        if not e:
            return get_json_result(data=False, message="Literature not found", code=settings.RetCode.DATA_ERROR)

        if not literature.markdown_content:
            return get_json_result(data=False, message="No Markdown content available. Please process with MinerU first.",
                                   code=settings.RetCode.ARGUMENT_ERROR)

        agent_id = request.json.get("agent_id")
        agent_title = request.json.get("agent_title", "")

        # 使用 markdown 内容作为输入
        input_content = literature.markdown_content

        # 获取智能体 DSL
        e, cvs = UserCanvasService.get_by_id(agent_id)
        if not e:
            return get_json_result(data=False, message="Agent not found", code=settings.RetCode.DATA_ERROR)

        # 创建结果记录
        result_id = LiteratureAgentResultService.create_result(
            literature_id=literature_id,
            agent_id=agent_id,
            agent_title=agent_title,
            input_content=input_content
        )

        start_time = time.time()

        try:
            # 调用智能体
            dsl = cvs.dsl if isinstance(cvs.dsl, str) else json.dumps(cvs.dsl, ensure_ascii=False)
            canvas = Canvas(dsl, current_user.id, agent_id)
            canvas.reset()
            output_content = ""
            workflow_output = None

            for ans in canvas.run(query=input_content, user_id=current_user.id):
                event_type = ans.get("event", "")
                data = ans.get("data", {})

                logging.debug(f"Agent event: {event_type}, data: {data}")

                if event_type == "message":
                    # 收集 Message 组件的输出
                    content = data.get("content", "")
                    if content:
                        output_content += content
                elif event_type == "node_finished":
                    # 收集节点完成时的输出（作为备选）
                    outputs = data.get("outputs", {})
                    if outputs and isinstance(outputs, dict):
                        node_content = outputs.get("content", "")
                        if node_content and isinstance(node_content, str):
                            workflow_output = node_content
                elif event_type == "workflow_finished":
                    # 收集工作流完成时的最终输出
                    outputs = data.get("outputs", {})
                    if outputs and isinstance(outputs, dict):
                        final_content = outputs.get("content", "")
                        if final_content and isinstance(final_content, str):
                            workflow_output = final_content

            # 如果没有 message 输出，使用工作流的最终输出
            if not output_content and workflow_output:
                output_content = workflow_output
                logging.info(f"Using workflow output as fallback: {output_content[:200]}...")

            duration = time.time() - start_time

            LiteratureAgentResultService.update_result(
                result_id=result_id,
                status="1",
                output_content=output_content,
                process_duration=duration
            )
        except Exception as agent_error:
            duration = time.time() - start_time
            LiteratureAgentResultService.update_result(
                result_id=result_id,
                status="2",
                error_message=str(agent_error),
                process_duration=duration
            )
            raise agent_error

        # 返回结果
        e, result = LiteratureAgentResultService.get_by_id(result_id)
        return get_json_result(data=result.to_dict() if e else {"id": result_id})
    except Exception as e:
        logging.exception("run_agent error")
        return server_error_response(e)


@manager.route("/agent_result/<result_id>", methods=["GET"])  # noqa: F821
@login_required
def get_agent_result(result_id):
    """获取智能体处理结果详情"""
    try:
        e, result = LiteratureAgentResultService.get_by_id(result_id)
        if not e:
            return get_json_result(data=False, message="Result not found", code=settings.RetCode.DATA_ERROR)

        return get_json_result(data=result.to_dict())
    except Exception as e:
        logging.exception("get_agent_result error")
        return server_error_response(e)


@manager.route("/agent_result/<result_id>", methods=["DELETE"])  # noqa: F821
@login_required
def delete_agent_result(result_id):
    """删除智能体处理结果"""
    try:
        e, result = LiteratureAgentResultService.get_by_id(result_id)
        if not e:
            return get_json_result(data=False, message="Result not found", code=settings.RetCode.DATA_ERROR)

        # 获取关联的文献来验证权限
        e2, literature = LiteratureProcessService.get_by_id(result.literature_id)
        if not e2 or literature.tenant_id != current_user.id:
            return get_json_result(data=False, message="No permission", code=settings.RetCode.AUTHENTICATION_ERROR)

        LiteratureAgentResultService.delete_result(result_id)
        return get_json_result(data=True)
    except Exception as e:
        logging.exception("delete_agent_result error")
        return server_error_response(e)


@manager.route("/mineru/health", methods=["GET"])  # noqa: F821
@login_required
def mineru_health():
    """检查 MinerU 服务状态"""
    try:
        available, message = mineru_client.health_check()
        return get_json_result(data={"available": available, "message": message})
    except Exception as e:
        logging.exception("mineru_health error")
        return server_error_response(e)

