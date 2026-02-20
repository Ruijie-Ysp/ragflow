#!/usr/bin/env python3
"""
快速诊断脚本：检查所有服务和 API 的状态
"""

import requests
import json
import os
import sys

# 配置
STANDARD_OPENAI_BASE_URL = "http://10.0.154.103:8080/v1"
STANDARD_OPENAI_KEY = "gpustack_789d4d1cb010c27f_ac63b59a0ef8b495e1f0181356c05464"

RAGFLOW_BASE_URL = os.getenv('RAGFLOW_BASE_URL', 'http://localhost:80')
RAGFLOW_API_KEY = os.getenv('RAGFLOW_API_KEY', 'ragflow-I4Y2QzNTc4YWYxYTExZjBhYjViNjJlZD')

PROXY_BASE_URL = "http://localhost:10101/v1"


def check_service(name, url, timeout=5):
    """检查服务是否可访问"""
    print(f"\n{'='*80}")
    print(f"检查服务: {name}")
    print(f"{'='*80}")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=timeout)
        print(f"✅ 服务可访问")
        print(f"  状态码: {response.status_code}")
        print(f"  响应: {response.text[:200]}...")
        return True
    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到服务")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ 连接超时")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def check_standard_openai():
    """检查标准 OpenAI API"""
    print(f"\n{'='*80}")
    print(f"检查标准 OpenAI API")
    print(f"{'='*80}")
    
    # 检查 models 端点
    url = f"{STANDARD_OPENAI_BASE_URL}/models"
    headers = {"Authorization": f"Bearer {STANDARD_OPENAI_KEY}"}
    
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"✅ API 可访问")
        print(f"  状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            models = data.get('data', [])
            print(f"  可用模型数量: {len(models)}")
            if models:
                print(f"  第一个模型: {models[0].get('id', 'N/A')}")
        
        return True
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def check_ragflow():
    """检查 RAGFlow API"""
    print(f"\n{'='*80}")
    print(f"检查 RAGFlow API")
    print(f"{'='*80}")
    
    # 检查 agents 端点
    url = f"{RAGFLOW_BASE_URL}/api/v1/agents"
    headers = {"Authorization": f"Bearer {RAGFLOW_API_KEY}"}
    
    print(f"URL: {url}")
    print(f"API Key: {RAGFLOW_API_KEY[:30]}...")
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"✅ API 可访问")
        print(f"  状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            agents = data.get('data', [])

            # 检查 agents 是否是列表
            if not isinstance(agents, list):
                print(f"  ⚠️  API 返回格式异常: {data}")
                return None

            print(f"  可用 Agent 数量: {len(agents)}")
            
            if agents:
                print(f"\n  Agent 列表:")
                for i, agent in enumerate(agents[:5], 1):  # 只显示前5个
                    print(f"    {i}. {agent.get('title', 'Untitled')}")
                    print(f"       ID: {agent.get('id')}")
                
                return agents
            else:
                print(f"  ⚠️  没有可用的 Agent")
                return []
        else:
            print(f"  ❌ API 返回错误: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return None


def check_proxy():
    """检查代理服务"""
    print(f"\n{'='*80}")
    print(f"检查代理服务")
    print(f"{'='*80}")
    
    # 检查健康端点
    url = f"{PROXY_BASE_URL.replace('/v1', '')}/health"
    
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=5)
        print(f"✅ 代理服务可访问")
        print(f"  状态码: {response.status_code}")
        print(f"  响应: {response.text}")
        return True
    except Exception as e:
        print(f"❌ 错误: {e}")
        print(f"\n提示: 请确保代理服务正在运行:")
        print(f"  python ragflow_openai_proxy.py")
        return False


def test_simple_request(agent_id):
    """测试简单的请求"""
    print(f"\n{'='*80}")
    print(f"测试简单请求")
    print(f"{'='*80}")
    
    # 测试 RAGFlow 原始 API
    print(f"\n1. 测试 RAGFlow 原始 API")
    print(f"-" * 80)
    
    url = f"{RAGFLOW_BASE_URL}/api/v1/agents_openai/{agent_id}/chat/completions"
    headers = {
        "Authorization": f"Bearer {RAGFLOW_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "any",
        "messages": [{"role": "user", "content": "你好"}],
        "stream": False
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            print(f"✅ 成功")
            print(f"  内容长度: {len(content)} 字符")
            print(f"  内容: {content}")
        else:
            print(f"❌ 失败: {response.text}")
    except Exception as e:
        print(f"❌ 错误: {e}")
    
    # 测试代理 API
    print(f"\n2. 测试代理 API")
    print(f"-" * 80)
    
    url = f"{PROXY_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {agent_id}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "any",
        "messages": [{"role": "user", "content": "你好"}],
        "stream": False
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            print(f"✅ 成功")
            print(f"  内容长度: {len(content)} 字符")
            print(f"  内容: {content}")
        else:
            print(f"❌ 失败: {response.text}")
    except Exception as e:
        print(f"❌ 错误: {e}")


def main():
    """主函数"""
    print("\n" + "="*80)
    print("  RAGFlow OpenAI 代理 - 快速诊断")
    print("="*80)
    
    # 1. 检查标准 OpenAI 服务
    standard_ok = check_standard_openai()
    
    # 2. 检查 RAGFlow 服务
    agents = check_ragflow()
    ragflow_ok = agents is not None
    
    # 3. 检查代理服务
    proxy_ok = check_proxy()
    
    # 总结
    print(f"\n{'='*80}")
    print(f"诊断总结")
    print(f"{'='*80}")
    
    print(f"\n服务状态:")
    print(f"  标准 OpenAI API: {'✅ 正常' if standard_ok else '❌ 异常'}")
    print(f"  RAGFlow API:     {'✅ 正常' if ragflow_ok else '❌ 异常'}")
    print(f"  代理服务:        {'✅ 正常' if proxy_ok else '❌ 异常'}")
    
    # 如果所有服务都正常，进行简单测试
    if ragflow_ok and proxy_ok and agents:
        print(f"\n所有服务正常，进行功能测试...")
        
        # 使用第一个 Agent 进行测试
        if len(sys.argv) > 1:
            agent_id = sys.argv[1]
        else:
            agent_id = agents[0]['id']
        
        print(f"\n使用 Agent ID: {agent_id}")
        test_simple_request(agent_id)
    else:
        print(f"\n⚠️  部分服务异常，请先修复服务问题")
        
        if not ragflow_ok:
            print(f"\nRAGFlow 服务问题:")
            print(f"  1. 检查 RAGFlow 是否正在运行")
            print(f"  2. 检查 RAGFLOW_BASE_URL 环境变量: {RAGFLOW_BASE_URL}")
            print(f"  3. 检查 RAGFLOW_API_KEY 是否正确")
        
        if not proxy_ok:
            print(f"\n代理服务问题:")
            print(f"  1. 启动代理服务: python ragflow_openai_proxy.py")
            print(f"  2. 检查端口 10101 是否被占用")
    
    print(f"\n{'='*80}")
    print(f"诊断完成")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()

