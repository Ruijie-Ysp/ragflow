#!/usr/bin/env python3
"""
测试 BrowserOS MCP Server 连接
用于诊断 RAGFlow 连接 BrowserOS 的问题
"""

import asyncio
import logging

logging.basicConfig(level=logging.DEBUG)

async def test_browseros_connection():
    """测试连接 BrowserOS MCP Server"""
    from mcp.client.streamable_http import streamablehttp_client
    from mcp.client.session import ClientSession
    
    url = "http://127.0.0.1:9101/mcp"
    headers = {}  # 不需要认证
    
    print(f"🔍 测试连接到: {url}")
    print(f"📋 Headers: {headers}")
    print("")
    
    try:
        print("1️⃣ 创建 streamablehttp_client...")
        async with streamablehttp_client(url, headers) as (read_stream, write_stream, _):
            print("✅ streamablehttp_client 创建成功")
            
            print("2️⃣ 创建 ClientSession...")
            async with ClientSession(read_stream, write_stream) as client_session:
                print("✅ ClientSession 创建成功")
                
                print("3️⃣ 初始化 session...")
                result = await asyncio.wait_for(client_session.initialize(), timeout=10)
                print(f"✅ Session 初始化成功!")
                print(f"   Protocol Version: {result.protocolVersion}")
                print(f"   Server Info: {result.serverInfo}")
                print("")
                
                print("4️⃣ 获取工具列表...")
                tools_result = await client_session.list_tools()
                tools = tools_result.tools
                print(f"✅ 成功获取 {len(tools)} 个工具:")
                for i, tool in enumerate(tools[:5], 1):
                    print(f"   {i}. {tool.name}: {tool.description}")
                if len(tools) > 5:
                    print(f"   ... 还有 {len(tools) - 5} 个工具")
                
                return True
                
    except Exception as e:
        print(f"❌ 连接失败:")
        print(f"   错误类型: {type(e).__name__}")
        print(f"   错误信息: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_with_docker_url():
    """测试使用 Docker 内部 URL"""
    from mcp.client.streamable_http import streamablehttp_client
    from mcp.client.session import ClientSession
    
    url = "http://host.docker.internal:9101/mcp"
    headers = {}
    
    print(f"\n🔍 测试 Docker 内部连接到: {url}")
    print(f"📋 Headers: {headers}")
    print("")
    
    try:
        async with streamablehttp_client(url, headers) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as client_session:
                result = await asyncio.wait_for(client_session.initialize(), timeout=10)
                print(f"✅ Docker 内部连接成功!")
                print(f"   Protocol Version: {result.protocolVersion}")
                return True
    except Exception as e:
        print(f"❌ Docker 内部连接失败:")
        print(f"   错误类型: {type(e).__name__}")
        print(f"   错误信息: {str(e)}")
        return False


async def test_with_custom_headers():
    """测试使用自定义 headers"""
    from mcp.client.streamable_http import streamablehttp_client
    from mcp.client.session import ClientSession
    
    url = "http://127.0.0.1:9101/mcp"
    
    # 测试不同的 header 组合
    test_cases = [
        ("无 headers", {}),
        ("空 Authorization", {"Authorization": ""}),
        ("Bearer Token", {"Authorization": "Bearer test-token"}),
        ("自定义 header", {"X-Custom": "test"}),
    ]
    
    for name, headers in test_cases:
        print(f"\n🧪 测试 {name}: {headers}")
        try:
            async with streamablehttp_client(url, headers) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as client_session:
                    await asyncio.wait_for(client_session.initialize(), timeout=5)
                    print(f"   ✅ 成功")
        except Exception as e:
            print(f"   ❌ 失败: {type(e).__name__}: {str(e)}")


async def main():
    print("=" * 60)
    print("BrowserOS MCP Server 连接测试")
    print("=" * 60)
    print("")
    
    # 测试 1: 基本连接
    success1 = await test_browseros_connection()
    
    # 测试 2: Docker URL (可能失败，因为不在 Docker 内)
    # success2 = await test_with_docker_url()
    
    # 测试 3: 不同的 headers
    await test_with_custom_headers()
    
    print("")
    print("=" * 60)
    print("测试总结")
    print("=" * 60)
    if success1:
        print("✅ BrowserOS MCP Server 可以正常连接，不需要认证")
        print("")
        print("💡 建议:")
        print("   1. 在 RAGFlow 中使用 URL: http://host.docker.internal:9101/mcp")
        print("   2. Server Type: streamable-http")
        print("   3. Headers: 留空或不填")
        print("   4. 不需要 Authorization Token")
    else:
        print("❌ 连接失败，请检查:")
        print("   1. BrowserOS MCP Server 是否正在运行")
        print("   2. 端口 9101 是否被监听")
        print("   3. 防火墙设置")


if __name__ == "__main__":
    asyncio.run(main())

