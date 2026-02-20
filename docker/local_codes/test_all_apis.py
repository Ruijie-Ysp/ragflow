#!/usr/bin/env python3
"""
综合测试：对比标准 OpenAI API、RAGFlow 原始 API 和代理 API
"""

import requests
import json
import sys
import os
from datetime import datetime

# 配置
STANDARD_OPENAI_BASE_URL = "http://10.0.154.103:8080/v1"
STANDARD_OPENAI_MODEL = "qwen3-32b"
STANDARD_OPENAI_KEY = "gpustack_789d4d1cb010c27f_ac63b59a0ef8b495e1f0181356c05464"

RAGFLOW_BASE_URL = os.getenv('RAGFLOW_BASE_URL', 'http://localhost:80')
RAGFLOW_API_KEY = os.getenv('RAGFLOW_API_KEY', 'ragflow-I4Y2QzNTc4YWYxYTExZjBhYjViNjJlZD')

PROXY_BASE_URL = "http://localhost:10101/v1"

TEST_MESSAGE = "你好，请用一句话介绍你自己"


def print_section(title):
    """打印分节标题"""
    print("\n" + "="*100)
    print(f"  {title}")
    print("="*100)


def print_subsection(title):
    """打印子节标题"""
    print("\n" + "-"*100)
    print(f"  {title}")
    print("-"*100)


def extract_content_from_response(response_json):
    """从响应中提取内容"""
    try:
        if 'choices' in response_json and len(response_json['choices']) > 0:
            choice = response_json['choices'][0]
            if 'message' in choice:
                return choice['message'].get('content', '')
            elif 'delta' in choice:
                return choice['delta'].get('content', '')
        return None
    except:
        return None


def test_api(name, url, headers, data, stream=False):
    """通用 API 测试函数"""
    print_subsection(f"{name} - {'流式' if stream else '非流式'}响应")
    
    print(f"\n📤 请求信息:")
    print(f"  URL: {url}")
    print(f"  Headers: {json.dumps(headers, indent=4, ensure_ascii=False)}")
    print(f"  Body: {json.dumps(data, indent=4, ensure_ascii=False)}")
    
    start_time = datetime.now()
    
    try:
        response = requests.post(url, headers=headers, json=data, stream=stream, timeout=60)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        print(f"\n📥 响应信息:")
        print(f"  状态码: {response.status_code}")
        print(f"  耗时: {elapsed:.2f} 秒")
        print(f"  响应头:")
        for key, value in response.headers.items():
            print(f"    {key}: {value}")
        
        if stream:
            # 流式响应
            print(f"\n📥 流式响应内容:")
            line_count = 0
            content_pieces = []
            
            for line in response.iter_lines():
                if line:
                    line_count += 1
                    line_str = line.decode('utf-8')
                    
                    # 只打印前3行和最后一行的完整内容
                    if line_count <= 3 or line_str.startswith('data: [DONE]'):
                        print(f"  [{line_count:03d}] {line_str}")
                    elif line_count == 4:
                        print(f"  ... (省略中间内容) ...")
                    
                    # 提取内容
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]
                        if data_str.strip() != '[DONE]':
                            try:
                                data_obj = json.loads(data_str)
                                content = extract_content_from_response(data_obj)
                                if content:
                                    content_pieces.append(content)
                            except:
                                pass
            
            full_content = ''.join(content_pieces)
            print(f"\n✅ 结果:")
            print(f"  总行数: {line_count}")
            print(f"  内容长度: {len(full_content)} 字符")
            print(f"  完整内容: {full_content}")
            
            return {
                'success': True,
                'status_code': response.status_code,
                'content': full_content,
                'elapsed': elapsed,
                'line_count': line_count
            }
            
        else:
            # 非流式响应
            print(f"\n📥 响应内容:")
            
            try:
                response_json = response.json()
                print(json.dumps(response_json, indent=2, ensure_ascii=False))
                
                content = extract_content_from_response(response_json)
                
                print(f"\n✅ 结果:")
                print(f"  内容长度: {len(content) if content else 0} 字符")
                print(f"  完整内容: {content if content else '(无内容)'}")
                
                return {
                    'success': True,
                    'status_code': response.status_code,
                    'content': content,
                    'elapsed': elapsed,
                    'response': response_json
                }
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON 解析失败: {e}")
                print(f"原始响应: {response.text}")
                
                return {
                    'success': False,
                    'status_code': response.status_code,
                    'error': f"JSON 解析失败: {e}",
                    'elapsed': elapsed
                }
        
    except Exception as e:
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"\n❌ 请求失败: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'success': False,
            'error': str(e),
            'elapsed': elapsed
        }


def test_standard_openai(stream=False):
    """测试标准 OpenAI API"""
    url = f"{STANDARD_OPENAI_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {STANDARD_OPENAI_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": STANDARD_OPENAI_MODEL,
        "messages": [{"role": "user", "content": TEST_MESSAGE}],
        "stream": stream
    }
    
    return test_api("标准 OpenAI API", url, headers, data, stream)


def test_ragflow_direct(agent_id, stream=False):
    """测试 RAGFlow 原始 API"""
    url = f"{RAGFLOW_BASE_URL}/api/v1/agents_openai/{agent_id}/chat/completions"
    headers = {
        "Authorization": f"Bearer {RAGFLOW_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "any-model",
        "messages": [{"role": "user", "content": TEST_MESSAGE}],
        "stream": stream
    }
    
    return test_api("RAGFlow 原始 API", url, headers, data, stream)


def test_proxy(agent_id, stream=False):
    """测试代理 API"""
    url = f"{PROXY_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {agent_id}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "any-model",
        "messages": [{"role": "user", "content": TEST_MESSAGE}],
        "stream": stream
    }
    
    return test_api("代理 API", url, headers, data, stream)


def compare_results(results):
    """对比测试结果"""
    print_section("测试结果对比")
    
    print(f"\n{'API':<25} {'状态':<10} {'状态码':<10} {'耗时(秒)':<12} {'内容长度':<12} {'内容预览'}")
    print("-" * 120)
    
    for name, result in results.items():
        status = "✅ 成功" if result.get('success') else "❌ 失败"
        status_code = result.get('status_code', 'N/A')
        elapsed = f"{result.get('elapsed', 0):.2f}"
        content = result.get('content', '')
        content_len = len(content) if content else 0
        content_preview = content[:30] + "..." if content and len(content) > 30 else (content or "(无)")
        
        print(f"{name:<25} {status:<10} {status_code:<10} {elapsed:<12} {content_len:<12} {content_preview}")
    
    print("-" * 120)
    
    # 检查内容一致性
    print("\n内容一致性检查:")
    contents = {name: result.get('content', '') for name, result in results.items() if result.get('success')}
    
    if len(contents) > 1:
        content_values = list(contents.values())
        all_same = all(c == content_values[0] for c in content_values)
        
        if all_same:
            print("  ✅ 所有 API 返回的内容完全一致")
        else:
            print("  ⚠️  不同 API 返回的内容不同（这是正常的，因为 LLM 每次生成的内容可能不同）")
            for name, content in contents.items():
                print(f"    {name}: {len(content)} 字符")


def main():
    """主函数"""
    print_section("API 综合对比测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试消息: {TEST_MESSAGE}")
    
    # 获取 agent_id
    if len(sys.argv) > 1:
        agent_id = sys.argv[1]
    else:
        print("\n⚠️  未提供 Agent ID")
        print("用法: python test_all_apis.py <agent_id>")
        print("\n将只测试标准 OpenAI API")
        agent_id = None
    
    # 测试 1: 标准 OpenAI API（非流式）
    print_section("测试 1: 标准 OpenAI API")
    standard_result = test_standard_openai(stream=False)
    
    if agent_id:
        # 测试 2: RAGFlow 原始 API（非流式）
        print_section("测试 2: RAGFlow 原始 API")
        ragflow_result = test_ragflow_direct(agent_id, stream=False)
        
        # 测试 3: 代理 API（非流式）
        print_section("测试 3: 代理 API")
        proxy_result = test_proxy(agent_id, stream=False)
        
        # 对比结果
        results = {
            "标准 OpenAI (非流式)": standard_result,
            "RAGFlow 原始 (非流式)": ragflow_result,
            "代理 API (非流式)": proxy_result
        }
        compare_results(results)
        
        # 流式测试
        print_section("流式响应测试")
        
        print_subsection("标准 OpenAI API - 流式")
        standard_stream_result = test_standard_openai(stream=True)
        
        print_subsection("RAGFlow 原始 API - 流式")
        ragflow_stream_result = test_ragflow_direct(agent_id, stream=True)
        
        print_subsection("代理 API - 流式")
        proxy_stream_result = test_proxy(agent_id, stream=True)
        
        # 对比流式结果
        stream_results = {
            "标准 OpenAI (流式)": standard_stream_result,
            "RAGFlow 原始 (流式)": ragflow_stream_result,
            "代理 API (流式)": proxy_stream_result
        }
        compare_results(stream_results)
    
    print_section("测试完成")


if __name__ == "__main__":
    main()

