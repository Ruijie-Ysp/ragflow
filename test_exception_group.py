#!/usr/bin/env python3
"""
测试 ExceptionGroup 错误处理
"""

import asyncio
import logging

logging.basicConfig(level=logging.DEBUG)

async def test_with_wrong_url():
    """测试使用错误的 URL（会触发 ExceptionGroup）"""
    from mcp.client.streamable_http import streamablehttp_client
    from mcp.client.session import ClientSession
    
    # 使用一个不存在的 URL
    url = "http://host.docker.internal:9101/mcp"
    headers = {}
    
    print(f"🔍 测试连接到: {url}")
    print("   (这个 URL 可能无法从宿主机访问，会触发错误)")
    print("")
    
    try:
        async with streamablehttp_client(url, headers) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as client_session:
                await asyncio.wait_for(client_session.initialize(), timeout=5)
                print("✅ 连接成功")
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        
        print(f"❌ 捕获到异常:")
        print(f"   类型: {error_type}")
        print(f"   消息: {error_msg}")
        print("")
        
        # 检查是否是 ExceptionGroup
        if error_type == "ExceptionGroup":
            print("🔍 这是一个 ExceptionGroup，提取内部异常:")
            try:
                exceptions = e.exceptions if hasattr(e, 'exceptions') else [e]
                for i, exc in enumerate(exceptions, 1):
                    print(f"   异常 {i}: {type(exc).__name__}: {str(exc)}")
            except Exception as ex:
                print(f"   无法提取异常: {ex}")
        
        return False
    
    return True


async def test_with_correct_url():
    """测试使用正确的 URL"""
    from mcp.client.streamable_http import streamablehttp_client
    from mcp.client.session import ClientSession
    
    url = "http://127.0.0.1:9101/mcp"
    headers = {}
    
    print(f"\n🔍 测试连接到: {url}")
    print("")
    
    try:
        async with streamablehttp_client(url, headers) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as client_session:
                await asyncio.wait_for(client_session.initialize(), timeout=5)
                print("✅ 连接成功")
                return True
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        
        print(f"❌ 捕获到异常:")
        print(f"   类型: {error_type}")
        print(f"   消息: {error_msg}")
        
        if error_type == "ExceptionGroup":
            print("🔍 这是一个 ExceptionGroup，提取内部异常:")
            try:
                exceptions = e.exceptions if hasattr(e, 'exceptions') else [e]
                for i, exc in enumerate(exceptions, 1):
                    print(f"   异常 {i}: {type(exc).__name__}: {str(exc)}")
            except Exception as ex:
                print(f"   无法提取异常: {ex}")
        
        return False


async def main():
    print("=" * 60)
    print("ExceptionGroup 错误测试")
    print("=" * 60)
    print("")
    
    # 测试 1: 错误的 URL (host.docker.internal 在宿主机上可能无法访问)
    await test_with_wrong_url()
    
    # 测试 2: 正确的 URL
    await test_with_correct_url()
    
    print("")
    print("=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

