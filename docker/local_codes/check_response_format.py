#!/usr/bin/env python3
"""
检查代理 API 的响应格式，确认是否符合客户端期望
"""

import requests
import json

PROXY_URL = "http://localhost:10101"
AGENT_ID = "8575e77eaf2a11f0884eeec4e72d301e"

def check_response_structure():
    """检查响应结构是否完整"""
    print("=" * 100)
    print("检查代理 API 响应结构")
    print("=" * 100)
    
    url = f"{PROXY_URL}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {AGENT_ID}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "any-model",
        "messages": [
            {"role": "user", "content": "测试"}
        ],
        "stream": False
    }
    
    print(f"\n📤 发送测试请求...")
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        print(f"📥 状态码: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            
            print(f"\n✅ 响应 JSON:")
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
            
            # 检查关键字段
            print(f"\n🔍 字段检查:")
            
            # 检查 choices
            if 'choices' in response_data:
                print(f"  ✅ choices 字段存在")
                
                if isinstance(response_data['choices'], list):
                    print(f"  ✅ choices 是数组")
                    
                    if len(response_data['choices']) > 0:
                        print(f"  ✅ choices 有元素 (长度: {len(response_data['choices'])})")
                        
                        choice = response_data['choices'][0]
                        print(f"\n  第一个 choice 的结构:")
                        print(f"    - index: {choice.get('index', 'MISSING')}")
                        print(f"    - finish_reason: {choice.get('finish_reason', 'MISSING')}")
                        
                        # 检查 message
                        if 'message' in choice:
                            print(f"    ✅ message 字段存在")
                            message = choice['message']
                            print(f"      - role: {message.get('role', 'MISSING')}")
                            print(f"      - content: {message.get('content', 'MISSING')}")
                            
                            if 'content' in message and message['content']:
                                print(f"    ✅ content 有内容: {len(message['content'])} 字符")
                            else:
                                print(f"    ❌ content 为空或不存在！")
                        else:
                            print(f"    ❌ message 字段不存在！")
                            print(f"    可用字段: {list(choice.keys())}")
                    else:
                        print(f"  ❌ choices 数组为空！")
                else:
                    print(f"  ❌ choices 不是数组！类型: {type(response_data['choices'])}")
            else:
                print(f"  ❌ choices 字段不存在！")
                print(f"  可用字段: {list(response_data.keys())}")
            
            # 检查其他标准字段
            print(f"\n🔍 其他标准字段:")
            standard_fields = ['id', 'object', 'created', 'model']
            for field in standard_fields:
                if field in response_data:
                    print(f"  ✅ {field}: {response_data[field]}")
                else:
                    print(f"  ⚠️  {field}: 不存在")
            
            # 模拟客户端访问
            print(f"\n🧪 模拟客户端访问:")
            try:
                # 这是客户端可能的访问方式
                content = response_data['choices'][0]['message']['content']
                print(f"  ✅ response['choices'][0]['message']['content'] = {content}")
            except (KeyError, IndexError, TypeError) as e:
                print(f"  ❌ 访问失败: {e}")
                print(f"  这就是客户端报错的原因！")
            
        else:
            print(f"\n❌ 请求失败")
            print(f"响应内容: {response.text}")
            
    except Exception as e:
        print(f"\n❌ 异常: {e}")
        import traceback
        traceback.print_exc()


def check_error_response():
    """检查错误情况下的响应"""
    print("\n\n" + "=" * 100)
    print("检查错误响应格式")
    print("=" * 100)
    
    url = f"{PROXY_URL}/v1/chat/completions"
    headers = {
        "Authorization": "Bearer invalid-agent-id",  # 故意使用错误的 ID
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "any-model",
        "messages": [
            {"role": "user", "content": "测试"}
        ],
        "stream": False
    }
    
    print(f"\n📤 发送错误请求（使用无效 Agent ID）...")
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        print(f"📥 状态码: {response.status_code}")
        print(f"📥 响应内容:")
        print(response.text)
        
        if response.status_code != 200:
            try:
                error_data = response.json()
                print(f"\n解析后的错误响应:")
                print(json.dumps(error_data, indent=2, ensure_ascii=False))
                
                # 检查错误响应是否有 message 字段
                if 'message' in error_data:
                    print(f"\n✅ 错误响应有 message 字段")
                else:
                    print(f"\n⚠️  错误响应没有 message 字段")
                    print(f"可用字段: {list(error_data.keys())}")
                    
            except json.JSONDecodeError:
                print(f"\n⚠️  错误响应不是 JSON 格式")
                
    except Exception as e:
        print(f"\n❌ 异常: {e}")


if __name__ == "__main__":
    check_response_structure()
    check_error_response()
    
    print("\n" + "=" * 100)
    print("检查完成")
    print("=" * 100)

