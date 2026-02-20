#!/usr/bin/env python3
"""
RAGFlow OpenAI 代理服务器

将 RAGFlow Agent API 转换为标准 OpenAI API 格式
使用 agent_id 作为 API Key

用法:
    python ragflow_openai_proxy.py

然后可以像使用 OpenAI API 一样使用:
    client = OpenAI(
        api_key="<agent_id>",  # 使用 agent_id 作为 API key
        base_url="http://localhost:10101/v1"
    )
"""

from flask import Flask, request, Response, jsonify, g
import requests
import json
import os
import time
import threading
from typing import Optional

app = Flask(__name__)

# RAGFlow 配置
RAGFLOW_BASE_URL = os.getenv('RAGFLOW_BASE_URL', 'http://localhost:80')
RAGFLOW_API_KEY = os.getenv('RAGFLOW_API_KEY', 'ragflow-I4Y2QzNTc4YWYxYTExZjBhYjViNjJlZD')

# 超时配置（秒）
RAGFLOW_CONNECT_TIMEOUT = float(os.getenv('RAGFLOW_CONNECT_TIMEOUT', '5'))
RAGFLOW_READ_TIMEOUT = float(os.getenv('RAGFLOW_READ_TIMEOUT', '110'))

# 简单内存级 metrics，用于 Prometheus/Grafana 监控
_metrics_lock = threading.Lock()
_http_requests_total = {}
_http_request_duration_sum = {}
_http_request_duration_count = {}
_upstream_errors_total = {}
_streaming_connections = {}
_ragflow_up = 1  # 1=上游可达, 0=不可达


def _get_agent_label() -> str:
    """获取当前请求的 agent_id，用于 Prometheus label。

    - chat_completions 中会显式设置 g.agent_id
    - 其它没有 agent 概念的接口统一记为 "unknown"
    """
    agent_id = getattr(g, "agent_id", None)
    if not agent_id:
        return "unknown"
    return str(agent_id)


def _record_http_request(path: str, method: str, status_code: int, duration: float) -> None:
    agent_label = _get_agent_label()
    key = (path, method, status_code, agent_label)
    with _metrics_lock:
        _http_requests_total[key] = _http_requests_total.get(key, 0) + 1
        _http_request_duration_sum[key] = _http_request_duration_sum.get(key, 0.0) + duration
        _http_request_duration_count[key] = _http_request_duration_count.get(key, 0) + 1


def _record_upstream_error(error_type: str, path: str) -> None:
    agent_label = _get_agent_label()
    key = (error_type, path, agent_label)
    with _metrics_lock:
        _upstream_errors_total[key] = _upstream_errors_total.get(key, 0) + 1


def _set_ragflow_up(is_up: bool) -> None:
    global _ragflow_up
    _ragflow_up = 1 if is_up else 0


def _inc_streaming(agent_id: Optional[str]) -> None:
    agent_label = agent_id or "unknown"
    with _metrics_lock:
        _streaming_connections[agent_label] = _streaming_connections.get(agent_label, 0) + 1


def _dec_streaming(agent_id: Optional[str]) -> None:
    agent_label = agent_id or "unknown"
    with _metrics_lock:
        current = _streaming_connections.get(agent_label, 0)
        if current <= 1:
            _streaming_connections.pop(agent_label, None)
        else:
            _streaming_connections[agent_label] = current - 1


@app.before_request
def _before_request():
    # 记录请求开始时间，用于耗时统计
    g._request_start_time = time.time()

    # 统一处理 CORS 预检请求，避免浏览器在 OPTIONS 阶段就报错
    if request.method == "OPTIONS":
        # 让 Flask 生成一个默认的 200/204 响应
        resp = app.make_default_options_response()
        return resp


@app.after_request
def _after_request(response):
    try:
        start = getattr(g, "_request_start_time", None)
        if start is not None:
            duration = max(time.time() - start, 0.0)
            _record_http_request(request.path, request.method, response.status_code, duration)
    except Exception as e:
        # 避免 metrics 采集影响正常请求
        print(f"⚠️ metrics 记录失败: {e}")

    # 统一添加 CORS 头，方便在浏览器里通过其他系统调用本代理
    # （例如大模型调度/管理平台在前端用 fetch 直接访问 /v1/models）
    origin = request.headers.get("Origin", "*") or "*"
    response.headers.setdefault("Access-Control-Allow-Origin", origin)
    response.headers.setdefault("Vary", "Origin")
    response.headers.setdefault("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    response.headers.setdefault(
        "Access-Control-Allow-Headers", "Authorization, Content-Type, Accept"
    )
    response.headers.setdefault("Access-Control-Expose-Headers", "Content-Type")

    return response


def extract_agent_id_from_auth(auth_header: Optional[str]) -> Optional[str]:
    """从 Authorization header 中提取 agent_id"""
    if not auth_header:
        return None

    # 支持 "Bearer <agent_id>" 格式
    if auth_header.startswith('Bearer '):
        return auth_header[7:]

    return auth_header

def proxy_to_ragflow(agent_id: str, data: dict, stream: bool = False):
    """代理请求到 RAGFlow"""
    url = f"{RAGFLOW_BASE_URL}/api/v1/agents_openai/{agent_id}/chat/completions"

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {RAGFLOW_API_KEY}'
    }

    # 使用连接/读取超时拆分配置，避免单个请求长时间占用 worker
    response = requests.post(
        url,
        json=data,
        headers=headers,
        stream=stream,
        timeout=(RAGFLOW_CONNECT_TIMEOUT, RAGFLOW_READ_TIMEOUT),
    )
    return response

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """OpenAI Chat Completions API 兼容端点"""

    # 1. 从 Authorization header 中提取 agent_id
    auth_header = request.headers.get('Authorization')
    agent_id = extract_agent_id_from_auth(auth_header)

    if not agent_id:
        return jsonify({
            'error': {
                'message': 'Missing or invalid Authorization header. Use agent_id as API key.',
                'type': 'invalid_request_error',
                'code': 'invalid_api_key'
            }
        }), 401

    # 将 agent_id 挂到 Flask g 上，便于 metrics 打标签
    g.agent_id = agent_id

    # 2. 获取请求数据
    data = request.get_json()
    if not data:
        return jsonify({
            'error': {
                'message': 'Invalid JSON in request body',
                'type': 'invalid_request_error'
            }
        }), 400

    # 3. 检查是否是流式请求
    stream = data.get('stream', False)

    print(f"📨 收到请求: agent_id={agent_id}, stream={stream}")

    # 4. 代理到 RAGFlow
    try:
        ragflow_response = proxy_to_ragflow(agent_id, data, stream)
        # 只要 HTTP 层面连通，就认为 RAGFlow 处于可达状态
        _set_ragflow_up(True)
    except requests.exceptions.Timeout as e:
        _set_ragflow_up(False)
        _record_upstream_error('timeout', request.path)
        print(f"❌ 代理请求超时: {e}")
        return jsonify({
            'error': {
                'message': 'Upstream RAGFlow request timed out',
                'type': 'server_error',
                'code': 'ragflow_timeout'
            }
        }), 504
    except requests.exceptions.ConnectionError as e:
        _set_ragflow_up(False)
        _record_upstream_error('connection_error', request.path)
        print(f"❌ 无法连接到 RAGFlow: {e}")
        return jsonify({
            'error': {
                'message': 'Failed to connect to RAGFlow',
                'type': 'server_error',
                'code': 'ragflow_connection_error'
            }
        }), 502
    except requests.exceptions.RequestException as e:
        _set_ragflow_up(False)
        _record_upstream_error('request_exception', request.path)
        print(f"❌ RAGFlow 请求异常: {e}")
        return jsonify({
            'error': {
                'message': 'Error occurred while calling RAGFlow',
                'type': 'server_error'
            }
        }), 502
    except Exception as e:
        _set_ragflow_up(False)
        _record_upstream_error('unknown', request.path)
        print(f"❌ 未知错误: {e}")
        return jsonify({
            'error': {
                'message': 'Unexpected error occurred while calling RAGFlow',
                'type': 'server_error'
            }
        }), 500

    # 5. 返回响应
    if stream:
        # 流式响应
        _inc_streaming(agent_id)

        def generate():
            try:
                line_count = 0
                for line in ragflow_response.iter_lines():
                    if line:
                        line_count += 1
                        line_str = line.decode('utf-8')
                        # 打印前100字符用于调试
                        print(f"📨 流式响应 #{line_count}: {line_str[:100]}...")
                        yield line + b'\n'
                print(f"✅ 流式响应完成，共 {line_count} 行")
            except Exception as e:
                print(f"❌ 流式响应错误: {e}")
                import traceback
                traceback.print_exc()
                error_data = {
                    'error': {
                        'message': str(e),
                        'type': 'server_error'
                    }
                }
                yield f"data: {json.dumps(error_data)}\n\n".encode()
            finally:
                _dec_streaming(agent_id)

        return Response(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Content-Type': 'text/event-stream; charset=utf-8',
                'Connection': 'keep-alive'
            }
        )
    else:
        # 非流式响应
        try:
            # 检查响应状态
            print(f"📥 RAGFlow 响应状态码: {ragflow_response.status_code}")
            print(f"📥 RAGFlow 响应头: {dict(ragflow_response.headers)}")

            if ragflow_response.status_code != 200:
                print(f"❌ RAGFlow 返回错误状态码: {ragflow_response.status_code}")
                print(f"❌ 响应内容: {ragflow_response.text}")
                return Response(
                    ragflow_response.content,
                    status=ragflow_response.status_code,
                    mimetype='application/json'
                )

            # 解析并验证响应
            try:
                response_data = ragflow_response.json()
                print(f"✅ RAGFlow 响应数据结构:")
                print(json.dumps(response_data, indent=2, ensure_ascii=False))

                # 检查 RAGFlow 的错误响应格式
                # RAGFlow 在错误时返回 {"code": xxx, "message": "..."}
                if 'code' in response_data and 'message' in response_data and 'choices' not in response_data:
                    error_code = response_data.get('code')
                    error_message = response_data.get('message', 'Unknown error')
                    print(f"❌ RAGFlow 返回错误: code={error_code}, message={error_message}")
                    _record_upstream_error(f'ragflow_code_{error_code}', request.path)

                    # 根据错误代码返回适当的 HTTP 状态码
                    http_status = 400  # 默认 Bad Request
                    if error_code == 102:  # "You don't own the agent"
                        http_status = 403  # Forbidden
                    elif error_code == 109:  # "Authentication error"
                        http_status = 401  # Unauthorized
                    elif error_code >= 500:
                        http_status = 500  # Internal Server Error

                    # 返回标准 OpenAI 错误格式
                    return jsonify({
                        'error': {
                            'message': error_message,
                            'type': 'invalid_request_error',
                            'code': error_code
                        }
                    }), http_status

                # 检查是否有 choices 和 content
                if 'choices' in response_data and len(response_data['choices']) > 0:
                    message = response_data['choices'][0].get('message', {})
                    content = message.get('content', '')
                    print(f"✅ 提取的内容长度: {len(content)} 字符")
                    if content:
                        print(f"✅ 内容预览: {content[:100]}...")
                    else:
                        print(f"⚠️  警告: content 为空字符串")
                else:
                    print(f"⚠️  警告: 响应中没有 choices 字段或 choices 为空")
                    # 如果没有 choices 字段，可能是格式错误
                    if 'choices' not in response_data:
                        print(f"❌ 响应格式异常，缺少 choices 字段")
                        return jsonify({
                            'error': {
                                'message': 'Invalid response format from RAGFlow',
                                'type': 'server_error'
                            }
                        }), 500

            except json.JSONDecodeError as e:
                print(f"❌ 无法解析 JSON: {e}")
                print(f"原始响应: {ragflow_response.text}")

            # 返回响应，添加完整的响应头
            return Response(
                ragflow_response.content,
                status=ragflow_response.status_code,
                mimetype='application/json',
                headers={
                    'Content-Type': 'application/json; charset=utf-8',
                    'Cache-Control': 'no-cache'
                }
            )
        except Exception as e:
            print(f"❌ 非流式响应错误: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'error': {
                    'message': str(e),
                    'type': 'server_error'
                }
            }), 500

@app.route('/v1/models', methods=['GET'])
def list_models():
    """列出可用的模型 (实际上是 Agent 列表)"""

    try:
        # 获取所有 Agent
        url = f"{RAGFLOW_BASE_URL}/api/v1/agents"
        headers = {
            'Authorization': f'Bearer {RAGFLOW_API_KEY}'
        }

        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code != 200:
            return jsonify({
                'error': {
                    'message': 'Failed to fetch agents from RAGFlow',
                    'type': 'server_error'
                }
            }), 500

        data = response.json()
        agents = data.get('data') if isinstance(data, dict) else []
        # 如果后端返回的 data 不是列表（例如为布尔值/字典），避免在 for 中直接迭代报错
        if not isinstance(agents, list):
            print(f"⚠️ /api/v1/agents 返回的 data 不是列表, 实际类型: {type(agents)}，将其视为 [] 处理")
            agents = []

        # 转换为 OpenAI models 格式
        models = []
        for agent in agents:
            agent_title = agent.get('title', 'Untitled Agent')
            agent_desc = agent.get('description', '')

            # 构建更友好的模型信息
            # 注意：OpenAI 标准格式中 id 应该保持简洁，但我们在额外字段中提供完整信息
            models.append({
                'id': agent['id'],  # 保持原始 agent_id，用于 API 调用
                'object': 'model',
                'created': agent.get('create_time', 0),
                'owned_by': 'ragflow',
                'permission': [],
                'root': agent['id'],
                'parent': None,
                # 扩展字段：提供更友好的信息
                'name': agent_title,  # Agent 名称
                'title': agent_title,  # 别名，更明确
                'description': agent_desc,  # Agent 描述
                'agent_id': agent['id'],  # 明确标注这是 agent_id
            })

        return jsonify({
            'object': 'list',
            'data': models
        })

    except Exception as e:
        print(f"❌ 获取模型列表失败: {e}")
        return jsonify({
            'error': {
                'message': str(e),
                'type': 'server_error'
            }
        }), 500



# 兼容部分客户端只调用 `/models`（Base URL 已包含 /v1）的情况
@app.route('/models', methods=['GET'])
def list_models_root():
    """Alias for /v1/models, 用于兼容不同的 OpenAI Base URL 写法"""
    return list_models()

@app.route('/v1/models/<model_id>', methods=['GET'])
def get_model(model_id):
    """获取特定模型信息 (实际上是 Agent 信息)"""

    try:
        # 获取所有 Agent
        url = f"{RAGFLOW_BASE_URL}/api/v1/agents"
        headers = {
            'Authorization': f'Bearer {RAGFLOW_API_KEY}'
        }

        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code != 200:
            return jsonify({
                'error': {
                    'message': 'Failed to fetch agent from RAGFlow',
                    'type': 'server_error'
                }
            }), 500

        agents = response.json().get('data', [])

        # 查找指定的 Agent
        agent = next((a for a in agents if a['id'] == model_id), None)

        if not agent:
            return jsonify({
                'error': {
                    'message': f'Model {model_id} not found',
                    'type': 'invalid_request_error'
                }
            }), 404

        agent_title = agent.get('title', 'Untitled Agent')
        agent_desc = agent.get('description', '')

        return jsonify({
            'id': agent['id'],
            'object': 'model',
            'created': agent.get('create_time', 0),
            'owned_by': 'ragflow',
            'permission': [],
            'root': agent['id'],
            'parent': None,
            # 扩展字段：提供更友好的信息
            'name': agent_title,
            'title': agent_title,
            'description': agent_desc,
            'agent_id': agent['id'],
        })

    except Exception as e:
        print(f"❌ 获取模型信息失败: {e}")
        return jsonify({
            'error': {
                'message': str(e),
                'type': 'server_error'
            }
        }), 500

@app.route('/metrics', methods=['GET'])
def metrics():
    """Prometheus metrics endpoint for ragflow-proxy"""
    lines = []

    with _metrics_lock:
        # HTTP 请求计数
        lines.append('# HELP ragflow_proxy_http_requests_total Total HTTP requests processed by ragflow-proxy')
        lines.append('# TYPE ragflow_proxy_http_requests_total counter')
        for (path, method, status, agent_id), value in _http_requests_total.items():
            lines.append(
                f'ragflow_proxy_http_requests_total{{path="{path}",method="{method}",status="{status}",agent_id="{agent_id}"}} {value}'
            )

        # 请求耗时统计
        lines.append('# HELP ragflow_proxy_http_request_duration_seconds_sum Total time spent processing requests')
        lines.append('# TYPE ragflow_proxy_http_request_duration_seconds_sum counter')
        for (path, method, status, agent_id), value in _http_request_duration_sum.items():
            lines.append(
                f'ragflow_proxy_http_request_duration_seconds_sum{{path="{path}",method="{method}",status="{status}",agent_id="{agent_id}"}} {value}'
            )

        lines.append('# HELP ragflow_proxy_http_request_duration_seconds_count Number of requests included in duration metrics')
        lines.append('# TYPE ragflow_proxy_http_request_duration_seconds_count counter')
        for (path, method, status, agent_id), value in _http_request_duration_count.items():
            lines.append(
                f'ragflow_proxy_http_request_duration_seconds_count{{path="{path}",method="{method}",status="{status}",agent_id="{agent_id}"}} {value}'
            )

        # upstream 错误统计
        lines.append('# HELP ragflow_proxy_upstream_errors_total Total upstream errors by type, path and agent_id')
        lines.append('# TYPE ragflow_proxy_upstream_errors_total counter')
        for (error_type, path, agent_id), value in _upstream_errors_total.items():
            lines.append(
                f'ragflow_proxy_upstream_errors_total{{error_type="{error_type}",path="{path}",agent_id="{agent_id}"}} {value}'
            )

        # 当前活跃流式连接数（按 agent_id）
        lines.append('# HELP ragflow_proxy_streaming_connections Number of active streaming chat completions connections per agent')
        lines.append('# TYPE ragflow_proxy_streaming_connections gauge')
        for agent_id, value in _streaming_connections.items():
            lines.append(
                f'ragflow_proxy_streaming_connections{{agent_id="{agent_id}"}} {value}'
            )

        # 上游 RAGFlow 可用性
        lines.append('# HELP ragflow_proxy_ragflow_up Whether ragflow-proxy can reach the upstream RAGFlow service (1=up, 0=down)')
        lines.append('# TYPE ragflow_proxy_ragflow_up gauge')
        lines.append(f'ragflow_proxy_ragflow_up {_ragflow_up}')

    text = '\n'.join(lines) + '\n'
    return Response(text, mimetype='text/plain; version=0.0.4; charset=utf-8')


@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'ragflow_base_url': RAGFLOW_BASE_URL
    })

@app.route('/', methods=['GET'])
def index():
    """首页"""
    return jsonify({
        'message': 'RAGFlow OpenAI Proxy Server',
        'version': '1.0.0',
        'endpoints': {
            'chat_completions': '/v1/chat/completions',
            'list_models': '/v1/models',
            'get_model': '/v1/models/<model_id>',
            'health': '/health'
        },
        'usage': {
            'description': 'Use agent_id as API key',
            'example': {
                'api_key': '<your_agent_id>',
                'base_url': 'http://localhost:10101/v1'
            }
        }
    })

if __name__ == '__main__':
    print("🚀 RAGFlow OpenAI 代理服务器启动中...")
    print(f"📍 RAGFlow 地址: {RAGFLOW_BASE_URL}")
    print(f"🔑 RAGFlow API Key: {RAGFLOW_API_KEY[:20]}...")
    print(f"🌐 代理服务器地址: http://localhost:10101")
    print(f"📝 使用方法: 将 agent_id 作为 API key")
    print()

    app.run(
        host='0.0.0.0',
        port=10101,
        debug=True
    )

