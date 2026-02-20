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
import os
import logging
import requests
from typing import Tuple, Optional, Any, Union


class MineruClient:
    """MinerU HTTP 客户端 - 用于调用远程 MinerU 服务解析 PDF 文件"""
    
    def __init__(self):
        self.base_url = os.environ.get("LOCAL_MINERU_BASE_URL", "http://localhost")
        self.port = int(os.environ.get("LOCAL_MINERU_PORT", "8000"))
        self.endpoint = os.environ.get("LOCAL_MINERU_ENDPOINT", "/file_parse")
        self.timeout = int(os.environ.get("LOCAL_MINERU_TIMEOUT", "300000")) / 1000  # 转换为秒
        
    @property
    def api_url(self) -> str:
        """获取完整的 API URL"""
        return f"{self.base_url}:{self.port}{self.endpoint}"
    
    def parse_pdf(self, file_content: bytes, filename: str) -> Tuple[bool, Optional[str], Optional[str], str]:
        """
        解析 PDF 文件
        
        Args:
            file_content: PDF 文件的二进制内容
            filename: 文件名
            
        Returns:
            Tuple[success, markdown_content, txt_content, message]
        """
        try:
            files = {
                'files': (filename, file_content, 'application/pdf')
            }
            data = {
                'return_md': 'true',
                'return_content_list': 'true'
            }
            
            logging.info(f"Calling MinerU API: {self.api_url}")
            
            response = requests.post(
                self.api_url,
                files=files,
                data=data,
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                error_msg = f"MinerU API error: HTTP {response.status_code} - {response.text}"
                logging.error(error_msg)
                return False, None, None, error_msg
            
            result = response.json()
            
            # 解析响应
            markdown_content, txt_content = self._extract_content(result)
            
            if markdown_content or txt_content:
                return True, markdown_content, txt_content, "Success"
            else:
                return False, None, None, "No content extracted from MinerU response"
                
        except requests.Timeout:
            error_msg = f"MinerU API timeout after {self.timeout} seconds"
            logging.error(error_msg)
            return False, None, None, error_msg
        except requests.RequestException as e:
            error_msg = f"MinerU API request error: {str(e)}"
            logging.error(error_msg)
            return False, None, None, error_msg
        except Exception as e:
            error_msg = f"MinerU parsing error: {str(e)}"
            logging.exception(error_msg)
            return False, None, None, error_msg
    
    def _extract_content(self, result: Union[dict, list, Any]) -> Tuple[Optional[str], Optional[str]]:
        """
        从 MinerU 响应中提取 Markdown 和 TXT 内容

        MinerU 响应格式 (新版):
        {
            "backend": "pipeline",
            "version": "2.1.10",
            "results": {
                "文件名": {
                    "md_content": "...",
                    "txt_content": "...",
                    "content_list": [...]
                }
            }
        }

        或旧版格式:
        [{"result": {"md": "...", "content_list": [...]}}]
        """
        markdown_content = None
        txt_content = None

        if not result:
            return None, None

        # 处理新版 dict 格式
        if isinstance(result, dict):
            # 检查是否有 results 字段 (新版格式)
            if "results" in result:
                results = result.get("results", {})
                for file_name, file_result in results.items():
                    if isinstance(file_result, dict):
                        # 提取 md_content
                        if "md_content" in file_result:
                            markdown_content = file_result["md_content"]
                        elif "md" in file_result:
                            markdown_content = file_result["md"]

                        # 提取 txt_content
                        if "txt_content" in file_result:
                            txt_content = file_result["txt_content"]

                        # 从 content_list 提取纯文本
                        if not txt_content and "content_list" in file_result:
                            txt_parts = []
                            for content_item in file_result.get("content_list", []):
                                if isinstance(content_item, dict):
                                    text = content_item.get("text", "")
                                    if text:
                                        txt_parts.append(text)
                                elif isinstance(content_item, str):
                                    txt_parts.append(content_item)
                            if txt_parts:
                                txt_content = "\n".join(txt_parts)

                        # 如果已经提取到内容，跳出循环
                        if markdown_content or txt_content:
                            break
            else:
                # 可能是单个结果的 dict
                if "md_content" in result:
                    markdown_content = result["md_content"]
                elif "md" in result:
                    markdown_content = result["md"]
                if "txt_content" in result:
                    txt_content = result["txt_content"]

        # 处理旧版 list 格式
        elif isinstance(result, list):
            for item in result:
                if not isinstance(item, dict):
                    continue

                res = item.get("result", {})

                # 提取 Markdown
                if "md" in res:
                    markdown_content = res["md"]
                elif "md_content" in res:
                    markdown_content = res["md_content"]

                # 提取纯文本 - 从 content_list 中组合
                if "content_list" in res:
                    txt_parts = []
                    for content_item in res.get("content_list", []):
                        if isinstance(content_item, dict):
                            text = content_item.get("text", "")
                            if text:
                                txt_parts.append(text)
                        elif isinstance(content_item, str):
                            txt_parts.append(content_item)
                    if txt_parts:
                        txt_content = "\n".join(txt_parts)

                if markdown_content or txt_content:
                    break

        # 如果没有 txt_content，从 markdown 生成纯文本
        if not txt_content and markdown_content:
            txt_content = self._markdown_to_text(markdown_content)

        return markdown_content, txt_content
    
    def _markdown_to_text(self, markdown: str) -> str:
        """简单的 Markdown 转纯文本"""
        import re
        # 移除图片
        text = re.sub(r'!\[.*?\]\(.*?\)', '', markdown)
        # 移除链接但保留文本
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        # 移除标题标记
        text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
        # 移除粗体/斜体
        text = re.sub(r'\*+([^*]+)\*+', r'\1', text)
        text = re.sub(r'_+([^_]+)_+', r'\1', text)
        # 移除代码块标记
        text = re.sub(r'```[^`]*```', '', text, flags=re.DOTALL)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        # 移除多余空行
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()
    
    def health_check(self) -> Tuple[bool, str]:
        """检查 MinerU 服务是否可用"""
        try:
            # 尝试访问服务
            response = requests.get(
                f"{self.base_url}:{self.port}/",
                timeout=10
            )
            return True, f"MinerU service is available (HTTP {response.status_code})"
        except Exception as e:
            return False, f"MinerU service unavailable: {str(e)}"


# 单例实例
mineru_client = MineruClient()

