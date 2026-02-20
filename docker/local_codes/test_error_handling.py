#!/usr/bin/env python3
"""
测试代理的错误处理
"""

import requests
import json

PROXY_URL = "http://localhost:10101"

def test_invalid_agent():
    """测试无效的 Agent ID"""
    print("=" * 100)
    print("测试 1: 无效的 Agent ID")
    print("=" * 100)
    
    url = f"{PROXY_URL}/v1/chat/completions"
    headers = {
        "Authorization": "Bearer invalid-agent-id-12345",
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
    print(f"📤 使用无效 Agent ID: invalid-agent-id-12345")
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        print(f"\n📥 响应状态码: {response.status_code}")
        print(f"📥 响应头:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        
        print(f"\n📥 响应内容:")
        print(response.text)
        
        try:
            response_data = response.json()
            print(f"\n📥 解析后的 JSON:")
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
            
            # 检查错误格式
            if 'error' in response_data:
                print(f"\n✅ 响应包含 error 字段（符合 OpenAI 标准）")
                error = response_data['error']
                print(f"  - message: {error.get('message')}")
                print(f"  - type: {error.get('type')}")
                print(f"  - code: {error.get('code')}")
            else:
                print(f"\n❌ 响应不包含 error 字段")
                
            # 检查是否有 choices 字段
            if 'choices' in response_data:
                print(f"\n⚠️  响应包含 choices 字段（不应该出现在错误响应中）")
            else:
                print(f"\n✅ 响应不包含 choices 字段（正确）")
                
        except json.JSONDecodeError as e:
            print(f"\n❌ JSON 解析失败: {e}")
        
        # 验证状态码
        if response.status_code == 200:
            print(f"\n❌ 错误: 状态码应该是 4xx 或 5xx，而不是 200")
        elif 400 <= response.status_code < 500:
            print(f"\n✅ 状态码正确: {response.status_code} (客户端错误)")
        elif response.status_code >= 500:
            print(f"\n✅ 状态码正确: {response.status_code} (服务器错误)")
            
    except Exception as e:
        print(f"\n❌ 请求异常: {e}")
        import traceback
        traceback.print_exc()


def test_valid_agent():
    """测试有效的 Agent ID"""
    print("\n\n" + "=" * 100)
    print("测试 2: 有效的 Agent ID")
    print("=" * 100)
    
    url = f"{PROXY_URL}/v1/chat/completions"
    headers = {
        "Authorization": "Bearer 8575e77eaf2a11f0884eeec4e72d301e",
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
    print(f"📤 使用有效 Agent ID: 8575e77eaf2a11f0884eeec4e72d301e")
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        print(f"\n📥 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ 状态码正确: 200")
            
            response_data = response.json()
            
            # 检查是否有 choices 字段
            if 'choices' in response_data:
                print(f"✅ 响应包含 choices 字段")
                
                if len(response_data['choices']) > 0:
                    choice = response_data['choices'][0]
                    if 'message' in choice:
                        message = choice['message']
                        if 'content' in message:
                            content = message['content']
                            print(f"✅ 成功获取内容: {content[:50]}...")
                        else:
                            print(f"❌ message 中没有 content 字段")
                    else:
                        print(f"❌ choice 中没有 message 字段")
                else:
                    print(f"❌ choices 数组为空")
            else:
                print(f"❌ 响应不包含 choices 字段")
                
            # 检查是否有 error 字段
            if 'error' in response_data:
                print(f"⚠️  响应包含 error 字段（不应该出现在成功响应中）")
            else:
                print(f"✅ 响应不包含 error 字段（正确）")
        else:
            print(f"❌ 状态码错误: {response.status_code}")
            print(f"响应内容: {response.text}")
            
    except Exception as e:
        print(f"\n❌ 请求异常: {e}")
        import traceback
        traceback.print_exc()


def test_client_simulation():
    """模拟客户端代码"""
    print("\n\n" + "=" * 100)
    print("测试 3: 模拟客户端代码")
    print("=" * 100)
    
    print("\n模拟客户端代码（不检查错误）:")
    print("```javascript")
    print("const response = await fetch('/v1/chat/completions', {...});")
    print("const data = await response.json();")
    print("const content = data.choices[0].message.content;  // 可能报错")
    print("```")
    
    # 测试无效 Agent
    print("\n\n--- 场景 1: 使用无效 Agent ID ---")
    url = f"{PROXY_URL}/v1/chat/completions"
    headers = {
        "Authorization": "Bearer invalid-agent-id",
        "Content-Type": "application/json"
    }
    data = {
        "model": "any-model",
        "messages": [{"role": "user", "content": "你好"}],
        "stream": False
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response_data = response.json()
        
        print(f"HTTP 状态码: {response.status_code}")
        
        # 模拟客户端直接访问 choices
        try:
            content = response_data['choices'][0]['message']['content']
            print(f"✅ 成功获取内容: {content}")
        except (KeyError, IndexError, TypeError) as e:
            print(f"❌ 客户端报错: {type(e).__name__}: {e}")
            print(f"   这就是用户看到的错误！")
            
            # 正确的错误处理
            if response.status_code != 200:
                print(f"\n💡 正确的处理方式:")
                print(f"   1. 先检查 HTTP 状态码")
                print(f"   2. 如果不是 200，检查 error 字段")
                if 'error' in response_data:
                    print(f"   3. 错误信息: {response_data['error'].get('message')}")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
    
    # 测试有效 Agent
    print("\n\n--- 场景 2: 使用有效 Agent ID ---")
    headers["Authorization"] = "Bearer 8575e77eaf2a11f0884eeec4e72d301e"
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response_data = response.json()
        
        print(f"HTTP 状态码: {response.status_code}")
        
        # 模拟客户端直接访问 choices
        try:
            content = response_data['choices'][0]['message']['content']
            print(f"✅ 成功获取内容: {content[:50]}...")
        except (KeyError, IndexError, TypeError) as e:
            print(f"❌ 客户端报错: {type(e).__name__}: {e}")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")


if __name__ == "__main__":
    test_invalid_agent()
    test_valid_agent()
    test_client_simulation()
    
    print("\n" + "=" * 100)
    print("测试完成")
    print("=" * 100)
    
    print("\n📝 总结:")
    print("1. 修改后的代理会检测 RAGFlow 的错误响应格式")
    print("2. 将错误响应转换为标准 OpenAI 格式")
    print("3. 返回正确的 HTTP 状态码（403, 401, 500 等）")
    print("4. 客户端可以通过检查状态码来判断是否成功")

