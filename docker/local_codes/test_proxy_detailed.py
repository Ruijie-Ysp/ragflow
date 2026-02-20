#!/usr/bin/env python3
"""
详细测试代理 API 的响应
"""

import requests
import json
import sys

# 配置
PROXY_URL = "http://localhost:10101"
AGENT_ID = "8575e77eaf2a11f0884eeec4e72d301e"

def test_proxy_non_streaming():
    """测试非流式响应"""
    print("=" * 100)
    print("测试代理 API - 非流式响应")
    print("=" * 100)
    
    url = f"{PROXY_URL}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {AGENT_ID}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "any-model",
        "messages": [
            {"role": "user", "content": "你好"}
        ],
        "stream": False
    }
    
    print(f"\n📤 请求 URL: {url}")
    print(f"📤 请求头: {json.dumps(headers, indent=2, ensure_ascii=False)}")
    print(f"📤 请求体: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        print(f"\n📥 响应状态码: {response.status_code}")
        print(f"📥 响应头:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        
        print(f"\n📥 响应原始文本:")
        print(response.text)
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                print(f"\n📥 解析后的 JSON:")
                print(json.dumps(response_data, indent=2, ensure_ascii=False))
                
                # 提取内容
                if 'choices' in response_data and len(response_data['choices']) > 0:
                    content = response_data['choices'][0].get('message', {}).get('content', '')
                    print(f"\n✅ 提取的内容:")
                    print(f"  长度: {len(content)} 字符")
                    print(f"  内容: {content}")
                    
                    if not content:
                        print("\n❌ 警告: content 字段为空！")
                    else:
                        print("\n✅ 成功: content 字段有内容")
                else:
                    print("\n❌ 错误: 响应中没有 choices 字段")
                    
            except json.JSONDecodeError as e:
                print(f"\n❌ JSON 解析失败: {e}")
        else:
            print(f"\n❌ 请求失败，状态码: {response.status_code}")
            
    except Exception as e:
        print(f"\n❌ 请求异常: {e}")
        import traceback
        traceback.print_exc()


def test_proxy_streaming():
    """测试流式响应"""
    print("\n\n" + "=" * 100)
    print("测试代理 API - 流式响应")
    print("=" * 100)
    
    url = f"{PROXY_URL}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {AGENT_ID}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "any-model",
        "messages": [
            {"role": "user", "content": "你好"}
        ],
        "stream": True
    }
    
    print(f"\n📤 请求 URL: {url}")
    print(f"📤 请求头: {json.dumps(headers, indent=2, ensure_ascii=False)}")
    print(f"📤 请求体: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(url, headers=headers, json=data, stream=True, timeout=30)
        
        print(f"\n📥 响应状态码: {response.status_code}")
        print(f"📥 响应头:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        
        if response.status_code == 200:
            print(f"\n📥 流式响应内容:")
            print("-" * 100)
            
            full_content = ""
            chunk_count = 0
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    chunk_count += 1
                    print(f"[{chunk_count:03d}] {line_str}")
                    
                    # 尝试解析 SSE 数据
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]  # 去掉 "data: " 前缀
                        
                        if data_str == '[DONE]':
                            continue
                        
                        try:
                            chunk_data = json.loads(data_str)
                            if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                                delta = chunk_data['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    full_content += content
                                    print(f"      ↳ 内容片段: {content}")
                        except json.JSONDecodeError:
                            pass
            
            print("-" * 100)
            print(f"\n✅ 流式响应完成，共 {chunk_count} 行")
            print(f"✅ 完整内容长度: {len(full_content)} 字符")
            print(f"✅ 完整内容: {full_content}")
            
            if not full_content:
                print("\n❌ 警告: 流式响应没有返回任何内容！")
            else:
                print("\n✅ 成功: 流式响应返回了内容")
        else:
            print(f"\n❌ 请求失败，状态码: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"\n❌ 请求异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        AGENT_ID = sys.argv[1]
    
    print(f"使用 Agent ID: {AGENT_ID}\n")
    
    test_proxy_non_streaming()
    test_proxy_streaming()
    
    print("\n" + "=" * 100)
    print("测试完成")
    print("=" * 100)

