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

from flask import Flask, request, Response, jsonify
import requests
import json
import os
from typing import Optional

app = Flask(__name__)

# RAGFlow 配置
RAGFLOW_BASE_URL = os.getenv('RAGFLOW_BASE_URL', 'http://localhost:80')
RAGFLOW_API_KEY = os.getenv('RAGFLOW_API_KEY', 'ragflow-RkZTliMTlhYTMyMzExZjA4N2MxMzZkYj')

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
    
    try:
        response = requests.post(
            url,
            json=data,
            headers=headers,
            stream=stream,
            timeout=300
        )
        
        return response
    except Exception as e:
        print(f"❌ 代理请求失败: {e}")
        return None

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
    ragflow_response = proxy_to_ragflow(agent_id, data, stream)
    
    if not ragflow_response:
        return jsonify({
            'error': {
                'message': 'Failed to connect to RAGFlow',
                'type': 'server_error'
            }
        }), 500
    
    # 5. 返回响应
    if stream:
        # 流式响应
        def generate():
            try:
                for line in ragflow_response.iter_lines():
                    if line:
                        yield line + b'\n'
            except Exception as e:
                print(f"❌ 流式响应错误: {e}")
                error_data = {
                    'error': {
                        'message': str(e),
                        'type': 'server_error'
                    }
                }
                yield f"data: {json.dumps(error_data)}\n\n".encode()
        
        return Response(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )
    else:
        # 非流式响应
        try:
            return Response(
                ragflow_response.content,
                status=ragflow_response.status_code,
                mimetype='application/json'
            )
        except Exception as e:
            print(f"❌ 非流式响应错误: {e}")
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
        
        agents = response.json().get('data', [])
        
        # 转换为 OpenAI models 格式
        models = []
        for agent in agents:
            agent_title = agent.get('title', 'Untitled Agent')
            agent_desc = agent.get('description', '')
            agent_id = agent['id']

            # 构建更友好的模型信息
            # 使用 agent_title 作为 id，这样前端会显示友好的名称
            # 同时保留原始 agent_id 在 agent_id 字段中
            models.append({
                'id': agent_title,  # 使用友好的名称作为 model id
                'object': 'model',
                'created': agent.get('create_time', 0),
                'owned_by': 'ragflow',
                'permission': [],
                'root': agent_title,
                'parent': None,
                # 扩展字段：提供完整信息
                'name': agent_title,  # Agent 名称
                'title': agent_title,  # 别名
                'description': agent_desc,  # Agent 描述
                'agent_id': agent_id,  # 原始 agent_id，用于 API 调用
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

        # 查找指定的 Agent (支持通过 title 或 agent_id 查找)
        agent = next((a for a in agents if a['id'] == model_id or a.get('title') == model_id), None)

        if not agent:
            return jsonify({
                'error': {
                    'message': f'Model {model_id} not found',
                    'type': 'invalid_request_error'
                }
            }), 404

        agent_title = agent.get('title', 'Untitled Agent')
        agent_desc = agent.get('description', '')
        agent_id = agent['id']

        return jsonify({
            'id': agent_title,  # 使用友好的名称
            'object': 'model',
            'created': agent.get('create_time', 0),
            'owned_by': 'ragflow',
            'permission': [],
            'root': agent_title,
            'parent': None,
            # 扩展字段：提供完整信息
            'name': agent_title,
            'title': agent_title,
            'description': agent_desc,
            'agent_id': agent_id,  # 原始 agent_id
        })
        
    except Exception as e:
        print(f"❌ 获取模型信息失败: {e}")
        return jsonify({
            'error': {
                'message': str(e),
                'type': 'server_error'
            }
        }), 500

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

