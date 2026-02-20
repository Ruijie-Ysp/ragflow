#!/usr/bin/env python3
"""
直接测试 RAGFlow Agent API 的返回格式
"""

import requests
import json
import sys
import os

# RAGFlow 配置
RAGFLOW_BASE_URL = os.getenv('RAGFLOW_BASE_URL', 'http://localhost:80')
RAGFLOW_API_KEY = os.getenv('RAGFLOW_API_KEY', 'ragflow-I4Y2QzNTc4YWYxYTExZjBhYjViNjJlZD')

def test_ragflow_agent_api(agent_id, stream=False):
    """直接测试 RAGFlow Agent API"""
    print(f"\n{'='*80}")
    print(f"测试 RAGFlow Agent API (stream={stream})")
    print(f"{'='*80}")
    
    url = f"{RAGFLOW_BASE_URL}/api/v1/agents_openai/{agent_id}/chat/completions"
    headers = {
        "Authorization": f"Bearer {RAGFLOW_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "any-model",  # RAGFlow 会忽略这个字段
        "messages": [
            {"role": "user", "content": "你好，请介绍一下自己"}
        ],
        "stream": stream,
        "temperature": 0.7
    }
    
    print(f"\n📤 请求 URL: {url}")
    print(f"📤 请求头: {json.dumps(headers, indent=2, ensure_ascii=False)}")
    print(f"📤 请求体: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(url, headers=headers, json=data, stream=stream, timeout=60)
        
        print(f"\n📥 响应状态码: {response.status_code}")
        print(f"📥 响应头:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        
        if stream:
            print(f"\n📥 流式响应内容:")
            print("-" * 80)
            line_count = 0
            content_pieces = []
            
            for line in response.iter_lines():
                if line:
                    line_count += 1
                    line_str = line.decode('utf-8')
                    print(f"[{line_count:03d}] {line_str}")
                    
                    # 解析并提取内容
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]
                        if data_str.strip() != '[DONE]':
                            try:
                                data_obj = json.loads(data_str)
                                # 提取 delta.content
                                if 'choices' in data_obj and len(data_obj['choices']) > 0:
                                    delta = data_obj['choices'][0].get('delta', {})
                                    content = delta.get('content', '')
                                    if content:
                                        content_pieces.append(content)
                                        print(f"      ↳ 内容片段: {content}")
                            except json.JSONDecodeError as e:
                                print(f"      ↳ JSON 解析失败: {e}")
            
            print("-" * 80)
            print(f"\n✅ 流式响应完成，共 {line_count} 行")
            if content_pieces:
                full_content = ''.join(content_pieces)
                print(f"✅ 完整内容: {full_content}")
            else:
                print(f"⚠️  警告: 没有提取到任何内容")
                
        else:
            print(f"\n📥 非流式响应内容:")
            print("-" * 80)
            
            # 打印原始响应
            print("原始响应文本:")
            print(response.text)
            print()
            
            try:
                response_json = response.json()
                print("解析后的 JSON:")
                print(json.dumps(response_json, indent=2, ensure_ascii=False))
                
                # 提取关键信息
                print("\n" + "="*80)
                print("关键信息提取:")
                print("="*80)
                
                if 'id' in response_json:
                    print(f"✅ ID: {response_json['id']}")
                
                if 'object' in response_json:
                    print(f"✅ Object: {response_json['object']}")
                
                if 'model' in response_json:
                    print(f"✅ Model: {response_json['model']}")
                
                if 'choices' in response_json:
                    print(f"✅ Choices 数量: {len(response_json['choices'])}")
                    
                    if len(response_json['choices']) > 0:
                        choice = response_json['choices'][0]
                        print(f"  - Index: {choice.get('index', 'N/A')}")
                        print(f"  - Finish Reason: {choice.get('finish_reason', 'N/A')}")
                        
                        if 'message' in choice:
                            message = choice['message']
                            print(f"  - Message Role: {message.get('role', 'N/A')}")
                            content = message.get('content', '')
                            print(f"  - Content 长度: {len(content)} 字符")
                            if content:
                                print(f"  - Content 预览: {content[:200]}...")
                            else:
                                print(f"  ⚠️  Content 为空！")
                        else:
                            print(f"  ⚠️  没有 message 字段")
                else:
                    print(f"⚠️  没有 choices 字段")
                
                if 'usage' in response_json:
                    usage = response_json['usage']
                    print(f"✅ Token 使用:")
                    print(f"  - Prompt Tokens: {usage.get('prompt_tokens', 'N/A')}")
                    print(f"  - Completion Tokens: {usage.get('completion_tokens', 'N/A')}")
                    print(f"  - Total Tokens: {usage.get('total_tokens', 'N/A')}")
                
            except json.JSONDecodeError as e:
                print(f"❌ 解析 JSON 失败: {e}")
            
            print("-" * 80)
            
        return response
        
    except Exception as e:
        print(f"\n❌ 请求失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def list_agents():
    """列出所有可用的 Agent"""
    print(f"\n{'='*80}")
    print("获取 Agent 列表")
    print(f"{'='*80}")
    
    url = f"{RAGFLOW_BASE_URL}/api/v1/agents"
    headers = {
        "Authorization": f"Bearer {RAGFLOW_API_KEY}"
    }
    
    print(f"\n📤 请求 URL: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        print(f"📥 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            agents = data.get('data', [])
            
            print(f"\n✅ 找到 {len(agents)} 个 Agent:")
            print("-" * 80)
            
            for i, agent in enumerate(agents, 1):
                print(f"\n{i}. {agent.get('title', 'Untitled')}")
                print(f"   ID: {agent.get('id')}")
                print(f"   描述: {agent.get('description', 'N/A')}")
                print(f"   创建时间: {agent.get('create_time', 'N/A')}")
            
            print("-" * 80)
            return agents
        else:
            print(f"❌ 获取 Agent 列表失败: {response.status_code}")
            print(f"响应: {response.text}")
            return []
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        import traceback
        traceback.print_exc()
        return []


def main():
    """主函数"""
    print("\n" + "="*80)
    print("RAGFlow Agent API 直接测试工具")
    print("="*80)
    
    # 首先列出所有 Agent
    agents = list_agents()
    
    # 获取要测试的 agent_id
    if len(sys.argv) > 1:
        agent_id = sys.argv[1]
    elif agents:
        print(f"\n请选择要测试的 Agent ID，或按 Ctrl+C 退出")
        agent_id = input("Agent ID: ").strip()
        if not agent_id:
            print("未提供 Agent ID，退出")
            return
    else:
        print("\n❌ 没有可用的 Agent，请先创建 Agent")
        return
    
    print(f"\n使用 Agent ID: {agent_id}")
    
    # 测试非流式
    print("\n\n" + "#"*80)
    print("# 测试 1: 非流式响应")
    print("#"*80)
    test_ragflow_agent_api(agent_id, stream=False)
    
    # 测试流式
    print("\n\n" + "#"*80)
    print("# 测试 2: 流式响应")
    print("#"*80)
    test_ragflow_agent_api(agent_id, stream=True)


if __name__ == "__main__":
    main()

