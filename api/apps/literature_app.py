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

# 支持的解析方法
SUPPORTED_PARSE_METHODS = ["MinerU", "DeepDOC", "PlainText", "Table"]


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


@manager.route("/cancel/<literature_id>", methods=["POST"])  # noqa: F821
@login_required
def cancel_process(literature_id):
    """取消/重置处理中的任务"""
    try:
        e, literature = LiteratureProcessService.get_by_id(literature_id)
        if not e:
            return get_json_result(data=False, message="Literature not found", code=settings.RetCode.DATA_ERROR)

        if literature.tenant_id != current_user.id:
            return get_json_result(data=False, message="No permission", code=settings.RetCode.AUTHENTICATION_ERROR)

        # 重置为待处理状态
        LiteratureProcessService.update_by_id(literature_id, {
            "process_status": "0",  # 待处理
            "process_message": "已取消",
            "process_begin_at": None,
            "process_duration": 0
        })

        return get_json_result(data=True)
    except Exception as e:
        logging.exception("cancel_process error")
        return server_error_response(e)


def _parse_with_mineru(file_content: bytes, filename: str):
    """使用 MinerU 解析 PDF"""
    success, markdown, txt, message = mineru_client.parse_pdf(file_content, filename)
    return success, markdown, txt, message


def _parse_with_deepdoc(file_content: bytes, filename: str):
    """使用 DeepDOC 解析 PDF"""
    try:
        from deepdoc.parser import PdfParser
        from io import BytesIO

        # 创建一个继承 PdfParser 的类来支持 binary 参数
        class LiteraturePdfParser(PdfParser):
            def __call__(self, filename, binary=None, from_page=0,
                         to_page=100000, zoomin=3, callback=None):
                from timeit import default_timer as timer
                start = timer()
                if callback:
                    callback(msg="OCR started")
                self.__images__(
                    filename if not binary else binary,
                    zoomin,
                    from_page,
                    to_page,
                    callback
                )
                if callback:
                    callback(msg="OCR finished ({:.2f}s)".format(timer() - start))

                start = timer()
                self._layouts_rec(zoomin)
                if callback:
                    callback(0.67, "Layout analysis ({:.2f}s)".format(timer() - start))

                self._table_transformer_job(zoomin)
                self._text_merge()
                self._concat_downward()
                self._filter_forpages()

                from copy import deepcopy
                tbls = self._extract_table_figure(True, zoomin, False, False)
                if callback:
                    callback(0.8, "Text extraction ({:.2f}s)".format(timer() - start))

                return self._RAGFlowPdfParser__filterout_scraps(deepcopy(self.boxes), zoomin), tbls

        pdf_parser = LiteraturePdfParser()

        def callback(progress=0, msg=""):
            logging.info(f"DeepDOC progress: {progress if isinstance(progress, str) else f'{progress:.0%}'} - {msg}")

        # 调用 DeepDOC 解析器
        sections, tables = pdf_parser(
            filename,
            binary=file_content,
            from_page=0,
            to_page=100000,
            callback=callback
        )

        logging.info(f"DeepDOC parser: sections count={len(sections) if sections else 0}, tables count={len(tables) if tables else 0}")

        # 将解析结果转换为 markdown 和 txt
        markdown_parts = []
        txt_parts = []

        # 处理文本部分 - sections 是 boxes 列表，每个 box 是字典 {"text": "...", ...}
        for box in sections:
            if isinstance(box, dict):
                text = box.get("text", "")
            elif isinstance(box, (list, tuple)) and len(box) > 0:
                text = box[0] if isinstance(box[0], str) else str(box[0])
            else:
                text = str(box) if box else ""

            if text and text.strip():
                txt_parts.append(text.strip())
                markdown_parts.append(text.strip())

        # 处理表格 - 表格结果格式为 (img, html_or_rows)
        for i, table in enumerate(tables):
            table_text = ""
            logging.info(f"DeepDOC Table {i}: type={type(table).__name__}, len={len(table) if hasattr(table, '__len__') else 'N/A'}")

            if isinstance(table, tuple) and len(table) >= 2:
                # 格式: (img, html_or_rows) - 直接的表格数据
                img, rows = table[0], table[1]
                logging.info(f"DeepDOC Table {i}: img type={type(img).__name__}, rows type={type(rows).__name__}")
                if isinstance(rows, str):
                    table_text = rows
                elif isinstance(rows, list) and rows:
                    table_text = "\n".join([str(r) for r in rows if r])
            elif isinstance(table, dict):
                table_text = table.get("text", "")

            if table_text and table_text.strip():
                txt_parts.append(table_text.strip())
                markdown_parts.append(table_text.strip())

        logging.info(f"DeepDOC parser: txt_parts count={len(txt_parts)}, markdown_parts count={len(markdown_parts)}")

        markdown = "\n\n".join(markdown_parts)
        txt = "\n".join(txt_parts)

        return True, markdown, txt, "Success"
    except Exception as e:
        logging.exception("DeepDOC parsing error")
        return False, "", "", str(e)


def _parse_with_plaintext(file_content: bytes, filename: str):
    """使用 PlainText 解析 PDF（纯文本提取）"""
    try:
        from deepdoc.parser.pdf_parser import PlainParser

        plain_parser = PlainParser()
        lines, _ = plain_parser(file_content)

        txt_parts = [line for line, _ in lines if line]
        txt = "\n".join(txt_parts)
        markdown = txt  # PlainText 模式下 markdown 和 txt 相同

        return True, markdown, txt, "Success"
    except Exception as e:
        logging.exception("PlainText parsing error")
        return False, "", "", str(e)


def _parse_with_table(file_content: bytes, filename: str):
    """使用 Table 解析器解析 PDF（针对表格优化）"""
    try:
        from deepdoc.parser import PdfParser
        from io import BytesIO

        # 创建一个继承 PdfParser 的类来支持 binary 参数，专注于表格提取
        class TablePdfParser(PdfParser):
            def __call__(self, filename, binary=None, from_page=0,
                         to_page=100000, zoomin=3, callback=None):
                from timeit import default_timer as timer
                start = timer()
                if callback:
                    callback(msg="OCR started")
                self.__images__(
                    filename if not binary else binary,
                    zoomin,
                    from_page,
                    to_page,
                    callback
                )
                if callback:
                    callback(msg="OCR finished ({:.2f}s)".format(timer() - start))

                start = timer()
                self._layouts_rec(zoomin)
                if callback:
                    callback(0.67, "Layout analysis ({:.2f}s)".format(timer() - start))

                self._table_transformer_job(zoomin)
                self._text_merge()
                self._concat_downward()
                self._filter_forpages()

                from copy import deepcopy
                # 使用 return_html=True 来获取更好的表格格式
                tbls = self._extract_table_figure(True, zoomin, True, False)
                if callback:
                    callback(0.8, "Text extraction ({:.2f}s)".format(timer() - start))

                return self._RAGFlowPdfParser__filterout_scraps(deepcopy(self.boxes), zoomin), tbls

        pdf_parser = TablePdfParser()

        def callback(progress=0, msg=""):
            logging.info(f"Table parser progress: {progress if isinstance(progress, str) else f'{progress:.0%}'} - {msg}")

        # 调用解析器
        sections, tables = pdf_parser(
            filename,
            binary=file_content,
            from_page=0,
            to_page=100000,
            callback=callback
        )

        logging.info(f"Table parser: sections count={len(sections) if sections else 0}, tables count={len(tables) if tables else 0}")

        markdown_parts = []
        txt_parts = []

        # 处理文本部分 - sections 是 boxes 列表，每个 box 是字典 {"text": "...", ...}
        for box in sections:
            if isinstance(box, dict):
                text = box.get("text", "")
            elif isinstance(box, (list, tuple)) and len(box) > 0:
                text = box[0] if isinstance(box[0], str) else str(box[0])
            else:
                text = str(box) if box else ""

            if text and text.strip():
                txt_parts.append(text.strip())
                markdown_parts.append(text.strip())

        # 处理表格 - 表格结果格式为 (img, html_or_rows) 或 ((img, html_or_rows), positions)
        for i, table in enumerate(tables):
            table_text = ""
            logging.info(f"Table {i}: type={type(table).__name__}, len={len(table) if hasattr(table, '__len__') else 'N/A'}")

            if isinstance(table, tuple) and len(table) >= 2:
                # 格式: (img, html_or_rows) - 直接的表格数据
                img, rows = table[0], table[1]
                logging.info(f"Table {i}: img type={type(img).__name__}, rows type={type(rows).__name__}")
                if isinstance(rows, str):
                    table_text = rows
                elif isinstance(rows, list) and rows:
                    # rows 可能是 [[row1_data], [row2_data], ...] 格式
                    table_text = "\n".join([str(r) for r in rows if r])
            elif isinstance(table, dict):
                table_text = table.get("text", "")

            if table_text and table_text.strip():
                txt_parts.append(table_text.strip())
                markdown_parts.append(table_text.strip())

        logging.info(f"Table parser: txt_parts count={len(txt_parts)}, markdown_parts count={len(markdown_parts)}")

        markdown = "\n\n".join(markdown_parts)
        txt = "\n".join(txt_parts)

        return True, markdown, txt, "Success"
    except Exception as e:
        logging.exception("Table parsing error")
        return False, "", "", str(e)


@manager.route("/<literature_id>/process", methods=["POST"])  # noqa: F821
@login_required
def process_literature(literature_id):
    """处理文献，支持多种解析方法"""
    try:
        e, literature = LiteratureProcessService.get_by_id(literature_id)
        if not e:
            return get_json_result(data=False, message="Literature not found", code=settings.RetCode.DATA_ERROR)

        if literature.tenant_id != current_user.id:
            return get_json_result(data=False, message="No permission", code=settings.RetCode.AUTHENTICATION_ERROR)

        if literature.process_status == "1":
            return get_json_result(data=False, message="Already processing", code=settings.RetCode.ARGUMENT_ERROR)

        # 获取解析方法参数，默认使用 MinerU
        req_data = request.get_json() or {}
        parse_method = req_data.get("parse_method", "MinerU")

        # 验证解析方法
        if parse_method not in SUPPORTED_PARSE_METHODS:
            return get_json_result(
                data=False,
                message=f"Unsupported parse method: {parse_method}. Supported: {SUPPORTED_PARSE_METHODS}",
                code=settings.RetCode.ARGUMENT_ERROR
            )

        # 标记开始处理，并记录解析方法
        LiteratureProcessService.begin_process(literature_id, parse_method=parse_method)

        start_time = time.time()

        # 从 MinIO 获取文件
        bucket = f"{literature.tenant_id}-literature"
        file_content = STORAGE_IMPL.get(bucket, literature.location)

        # 根据解析方法调用不同的解析器
        if parse_method == "MinerU":
            success, markdown, txt, message = _parse_with_mineru(file_content, literature.name)
        elif parse_method == "DeepDOC":
            success, markdown, txt, message = _parse_with_deepdoc(file_content, literature.name)
        elif parse_method == "PlainText":
            success, markdown, txt, message = _parse_with_plaintext(file_content, literature.name)
        elif parse_method == "Table":
            success, markdown, txt, message = _parse_with_table(file_content, literature.name)
        else:
            success, markdown, txt, message = False, "", "", f"Unknown parse method: {parse_method}"

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


def _smart_split_content(content: str, max_chars: int = 12000) -> list:
    """
    智能分段：按段落分割内容，保持段落完整性
    返回分段列表，每段不超过 max_chars 字符
    """
    if len(content) <= max_chars:
        return [content]

    segments = []
    current_segment = ""

    # 按段落分割（双换行或单换行）
    paragraphs = content.split('\n\n')
    if len(paragraphs) == 1:
        # 如果没有双换行，尝试单换行
        paragraphs = content.split('\n')

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # 如果当前段落本身超过限制，需要进一步分割
        if len(para) > max_chars:
            # 先保存当前积累的内容
            if current_segment:
                segments.append(current_segment.strip())
                current_segment = ""

            # 按句子分割长段落
            sentences = para.replace('。', '。\n').replace('！', '！\n').replace('？', '？\n').split('\n')
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                if len(current_segment) + len(sentence) + 1 <= max_chars:
                    current_segment += sentence + " "
                else:
                    if current_segment:
                        segments.append(current_segment.strip())
                    current_segment = sentence + " "
        elif len(current_segment) + len(para) + 2 <= max_chars:
            current_segment += para + "\n\n"
        else:
            # 当前段落加入会超限，保存当前段落并开始新段落
            if current_segment:
                segments.append(current_segment.strip())
            current_segment = para + "\n\n"

    # 添加最后一个段落
    if current_segment.strip():
        segments.append(current_segment.strip())

    return segments if segments else [content[:max_chars]]


def _run_agent_on_content(canvas, content: str, user_id: str) -> str:
    """
    在单个内容片段上运行智能体，返回输出内容
    """
    canvas.reset()
    output_content = ""
    workflow_output = None

    for ans in canvas.run(query=content, user_id=user_id):
        event_type = ans.get("event", "")
        data = ans.get("data", {})

        if event_type == "message":
            msg_content = data.get("content", "")
            if msg_content:
                output_content += msg_content
        elif event_type == "node_finished":
            outputs = data.get("outputs", {})
            if outputs and isinstance(outputs, dict):
                node_content = outputs.get("content", "")
                if node_content and isinstance(node_content, str):
                    workflow_output = node_content
        elif event_type == "workflow_finished":
            outputs = data.get("outputs", {})
            if outputs and isinstance(outputs, dict):
                final_content = outputs.get("content", "")
                if final_content and isinstance(final_content, str):
                    workflow_output = final_content

    if not output_content and workflow_output:
        output_content = workflow_output

    return output_content


@manager.route("/<literature_id>/run_agent", methods=["POST"])  # noqa: F821
@login_required
@validate_request("agent_id")
def run_agent(literature_id):
    """
    使用智能体处理文献
    支持入参选择: input_source = "markdown" | "result:{result_id}"
    支持智能分段处理长内容
    """
    import json
    from agent.canvas import Canvas
    from api.db.services.canvas_service import UserCanvasService
    try:
        e, literature = LiteratureProcessService.get_by_id(literature_id)
        if not e:
            return get_json_result(data=False, message="Literature not found", code=settings.RetCode.DATA_ERROR)

        agent_id = request.json.get("agent_id")
        agent_title = request.json.get("agent_title", "")
        input_source = request.json.get("input_source", "markdown")  # 默认使用 markdown
        max_segment_chars = request.json.get("max_segment_chars", 12000)  # 分段大小，默认12000字符

        # 验证分段大小范围
        try:
            max_segment_chars = int(max_segment_chars)
            if max_segment_chars < 1000:
                max_segment_chars = 1000
            elif max_segment_chars > 500000:
                max_segment_chars = 500000
        except (TypeError, ValueError):
            max_segment_chars = 12000

        # 根据 input_source 获取输入内容
        if input_source == "markdown":
            if not literature.markdown_content:
                return get_json_result(data=False, message="No Markdown content available. Please process first.",
                                       code=settings.RetCode.ARGUMENT_ERROR)
            raw_content = literature.markdown_content
            source_label = "原始Markdown"
        elif input_source.startswith("result:"):
            # 使用某个智能体结果的输出作为输入
            result_id = input_source.split(":", 1)[1]
            e, source_result = LiteratureAgentResultService.get_by_id(result_id)
            if not e:
                return get_json_result(data=False, message="Source result not found", code=settings.RetCode.DATA_ERROR)
            if not source_result.output_content:
                return get_json_result(data=False, message="Source result has no output content",
                                       code=settings.RetCode.ARGUMENT_ERROR)
            raw_content = source_result.output_content
            source_label = f"智能体结果:{source_result.agent_title or result_id}"
        else:
            return get_json_result(data=False, message="Invalid input_source", code=settings.RetCode.ARGUMENT_ERROR)

        # 智能分段处理
        segments = _smart_split_content(raw_content, max_segment_chars)
        segment_count = len(segments)

        logging.info(f"Content length: {len(raw_content)}, max_segment_chars: {max_segment_chars}, split into {segment_count} segments")

        # 获取智能体 DSL
        e, cvs = UserCanvasService.get_by_id(agent_id)
        if not e:
            return get_json_result(data=False, message="Agent not found", code=settings.RetCode.DATA_ERROR)

        # 构建分段信息
        segment_info = {
            "total_chars": len(raw_content),
            "segment_count": segment_count,
            "max_segment_chars": max_segment_chars,
            "source": input_source,
            "source_label": source_label
        }

        # 创建结果记录（存储完整输入内容）
        result_id = LiteratureAgentResultService.create_result(
            literature_id=literature_id,
            agent_id=agent_id,
            agent_title=agent_title,
            input_content=raw_content,
            input_source=input_source,
            segment_info=json.dumps(segment_info, ensure_ascii=False)
        )

        start_time = time.time()

        try:
            # 调用智能体 - 分段处理
            dsl = cvs.dsl if isinstance(cvs.dsl, str) else json.dumps(cvs.dsl, ensure_ascii=False)
            canvas = Canvas(dsl, current_user.id, agent_id)

            all_outputs = []
            has_error = False
            error_message = ""

            for i, segment in enumerate(segments):
                logging.info(f"Processing segment {i+1}/{segment_count}, length={len(segment)}")
                try:
                    segment_output = _run_agent_on_content(canvas, segment, current_user.id)
                    if segment_output:
                        all_outputs.append(segment_output.strip())

                    # 检查 canvas 是否有运行时错误
                    if canvas.error:
                        logging.error(f"Segment {i+1} error: {canvas.error}")
                        has_error = True
                        error_message = f"第{i+1}段处理出错: {canvas.error}"
                        break
                except Exception as seg_error:
                    logging.exception(f"Segment {i+1} exception")
                    has_error = True
                    error_message = f"第{i+1}段处理异常: {str(seg_error)}"
                    break

            # 合并所有输出 - 直接拼接，不添加分隔符
            output_content = "\n\n".join(all_outputs) if all_outputs else ""

            duration = time.time() - start_time

            if has_error:
                LiteratureAgentResultService.update_result(
                    result_id=result_id,
                    status="2",
                    error_message=error_message,
                    output_content=output_content if output_content else None,  # 保存部分结果
                    process_duration=duration
                )
            else:
                LiteratureAgentResultService.update_result(
                    result_id=result_id,
                    status="1",
                    output_content=output_content,
                    process_duration=duration
                )
                logging.info(f"Agent completed: {segment_count} segments, output={len(output_content)} chars, duration={duration:.2f}s")

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

