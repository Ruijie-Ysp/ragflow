#!/usr/bin/env python3
"""
测试标准 OpenAI 接口和 RAGFlow 代理接口的返回差异
"""

import requests
import json
import sys

# 配置
BASE_URL = "http://10.0.154.103:8080/v1"
MODEL_NAME = "qwen3-32b"
AUTH_KEY = "gpustack_789d4d1cb010c27f_ac63b59a0ef8b495e1f0181356c05464"

# 代理配置（需要根据实际情况修改）
PROXY_URL = "http://localhost:10101/v1"
AGENT_ID = "your_agent_id_here"  # 需要替换为实际的 agent_id

def test_standard_openai(stream=False):
    """测试标准 OpenAI 接口"""
    print(f"\n{'='*60}")
    print(f"测试标准 OpenAI 接口 (stream={stream})")
    print(f"{'='*60}")
    
    url = f"{BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {AUTH_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": MODEL_NAME,
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
        response = requests.post(url, headers=headers, json=data, stream=stream, timeout=30)
        
        print(f"\n📥 响应状态码: {response.status_code}")
        print(f"📥 响应头: {dict(response.headers)}")
        
        if stream:
            print(f"\n📥 流式响应内容:")
            print("-" * 60)
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    print(line_str)
                    
                    # 解析并美化显示
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]
                        if data_str.strip() != '[DONE]':
                            try:
                                data_obj = json.loads(data_str)
                                print(f"  ↳ 解析: {json.dumps(data_obj, indent=4, ensure_ascii=False)}")
                            except:
                                pass
            print("-" * 60)
        else:
            print(f"\n📥 非流式响应内容:")
            print("-" * 60)
            try:
                response_json = response.json()
                print(json.dumps(response_json, indent=2, ensure_ascii=False))
                
                # 提取关键信息
                if 'choices' in response_json and len(response_json['choices']) > 0:
                    content = response_json['choices'][0].get('message', {}).get('content', '')
                    print(f"\n✅ 提取的内容: {content}")
            except Exception as e:
                print(f"❌ 解析 JSON 失败: {e}")
                print(f"原始内容: {response.text}")
            print("-" * 60)
            
        return response
        
    except Exception as e:
        print(f"\n❌ 请求失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_proxy_openai(agent_id, stream=False):
    """测试代理 OpenAI 接口"""
    print(f"\n{'='*60}")
    print(f"测试代理 OpenAI 接口 (stream={stream})")
    print(f"{'='*60}")
    
    url = f"{PROXY_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {agent_id}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "any-model",  # 代理会忽略这个字段
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
        response = requests.post(url, headers=headers, json=data, stream=stream, timeout=30)
        
        print(f"\n📥 响应状态码: {response.status_code}")
        print(f"📥 响应头: {dict(response.headers)}")
        
        if stream:
            print(f"\n📥 流式响应内容:")
            print("-" * 60)
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    print(line_str)
                    
                    # 解析并美化显示
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]
                        if data_str.strip() != '[DONE]':
                            try:
                                data_obj = json.loads(data_str)
                                print(f"  ↳ 解析: {json.dumps(data_obj, indent=4, ensure_ascii=False)}")
                            except:
                                pass
            print("-" * 60)
        else:
            print(f"\n📥 非流式响应内容:")
            print("-" * 60)
            try:
                response_json = response.json()
                print(json.dumps(response_json, indent=2, ensure_ascii=False))
                
                # 提取关键信息
                if 'choices' in response_json and len(response_json['choices']) > 0:
                    content = response_json['choices'][0].get('message', {}).get('content', '')
                    print(f"\n✅ 提取的内容: {content}")
            except Exception as e:
                print(f"❌ 解析 JSON 失败: {e}")
                print(f"原始内容: {response.text}")
            print("-" * 60)
            
        return response
        
    except Exception as e:
        print(f"\n❌ 请求失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def compare_responses():
    """对比两个接口的响应"""
    print("\n" + "="*80)
    print("开始对比测试")
    print("="*80)
    
    # 测试非流式
    print("\n\n" + "#"*80)
    print("# 第一组：非流式响应对比")
    print("#"*80)
    
    standard_response = test_standard_openai(stream=False)
    
    if len(sys.argv) > 1:
        agent_id = sys.argv[1]
        proxy_response = test_proxy_openai(agent_id, stream=False)
    else:
        print("\n⚠️  跳过代理测试（未提供 agent_id）")
        print("用法: python test_proxy_comparison.py <agent_id>")
    
    # 测试流式
    print("\n\n" + "#"*80)
    print("# 第二组：流式响应对比")
    print("#"*80)
    
    standard_response_stream = test_standard_openai(stream=True)
    
    if len(sys.argv) > 1:
        agent_id = sys.argv[1]
        proxy_response_stream = test_proxy_openai(agent_id, stream=True)
    else:
        print("\n⚠️  跳过代理测试（未提供 agent_id）")


if __name__ == "__main__":
    compare_responses()

