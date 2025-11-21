#!/usr/bin/env python3
"""
Simple clustering demonstration test.

This script demonstrates how WebSocket clustering works by:
1. Starting two clustered nodes
2. Connecting clients to different nodes
3. Showing message propagation across the cluster
"""

import asyncio
import json
import aiohttp
import websockets
from datetime import datetime

async def get_auth_token(port):
    """Get JWT token from a specific node."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f'http://localhost:{port}/api/generate-token') as response:
            data = await response.json()
            return data['token']

async def test_clustering():
    """Test clustering functionality."""
    print("🔗 Testing WebSocket Clustering...")
    print("=" * 50)
    
    # Test two nodes
    node1_port = 8021  # websocket_enhanced_app
    node2_port = 8022  # websocket_clustered_app
    
    try:
        # Get tokens from both nodes
        print("🔐 Getting authentication tokens...")
        token1 = await get_auth_token(node1_port)
        token2 = await get_auth_token(node2_port)
        print(f"✅ Token from node1: {token1[:20]}...")
        print(f"✅ Token from node2: {token2[:20]}...")
        
        # Connect to both nodes
        print("\n🔗 Connecting to both nodes...")
        
        # Connect to node1
        uri1 = f"ws://localhost:{node1_port}/ws"
        async with websockets.connect(uri1) as ws1:
            print(f"✅ Connected to node1 ({node1_port})")
            
            # Authenticate on node1
            auth_msg1 = {"type": "auth", "data": {"token": token1}}
            await ws1.send(json.dumps(auth_msg1))
            
            # Get welcome message
            welcome1 = await ws1.recv()
            print(f"📥 Node1 welcome: {json.loads(welcome1)['data']['message']}")
            
            # Get auth success
            auth_response1 = await ws1.recv()
            auth_data1 = json.loads(auth_response1)
            if auth_data1['type'] == 'auth_success':
                print(f"✅ Authenticated on node1: {auth_data1['data']['node_id']}")
            
            # Connect to node2
            uri2 = f"ws://localhost:{node2_port}/ws"
            async with websockets.connect(uri2) as ws2:
                print(f"✅ Connected to node2 ({node2_port})")
                
                # Authenticate on node2
                auth_msg2 = {"type": "auth", "data": {"token": token2}}
                await ws2.send(json.dumps(auth_msg2))
                
                # Get welcome message
                welcome2 = await ws2.recv()
                print(f"📥 Node2 welcome: {json.loads(welcome2)['data']['message']}")
                
                # Get auth success
                auth_response2 = await ws2.recv()
                auth_data2 = json.loads(auth_response2)
                if auth_data2['type'] == 'auth_success':
                    print(f"✅ Authenticated on node2: {auth_data2['data']['node_id']}")
                
                # Send message from node1
                print("\n📤 Sending message from node1...")
                chat_msg1 = {
                    "type": "chat",
                    "data": {
                        "message": "Hello from node1!",
                        "room": "test_room",
                        "sender_name": "Node1User"
                    }
                }
                await ws1.send(json.dumps(chat_msg1))
                
                # Get confirmation from node1
                confirm1 = await ws1.recv()
                print(f"📥 Node1 confirmation: {json.loads(confirm1)['type']}")
                
                # Check if message propagated to node2
                print("⏳ Waiting for message propagation to node2...")
                try:
                    # Wait for message on node2 (with timeout)
                    await asyncio.wait_for(ws2.recv(), timeout=5.0)
                    print("✅ Message propagated to node2!")
                except asyncio.TimeoutError:
                    print("⚠️ Message did not propagate to node2 (expected if Redis not running)")
                
                # Send message from node2
                print("\n📤 Sending message from node2...")
                chat_msg2 = {
                    "type": "chat",
                    "data": {
                        "message": "Hello from node2!",
                        "room": "test_room",
                        "sender_name": "Node2User"
                    }
                }
                await ws2.send(json.dumps(chat_msg2))
                
                # Get confirmation from node2
                confirm2 = await ws2.recv()
                print(f"📥 Node2 confirmation: {json.loads(confirm2)['type']}")
                
                # Check if message propagated to node1
                print("⏳ Waiting for message propagation to node1...")
                try:
                    # Wait for message on node1 (with timeout)
                    await asyncio.wait_for(ws1.recv(), timeout=5.0)
                    print("✅ Message propagated to node1!")
                except asyncio.TimeoutError:
                    print("⚠️ Message did not propagate to node1 (expected if Redis not running)")
                
                # Test cluster info
                print("\n📊 Testing cluster info...")
                cluster_info_msg = {"type": "get_connections"}
                await ws2.send(json.dumps(cluster_info_msg))
                
                try:
                    cluster_response = await asyncio.wait_for(ws2.recv(), timeout=3.0)
                    cluster_data = json.loads(cluster_response)
                    if cluster_data['type'] == 'connections_info':
                        print(f"📊 Cluster info received from node2")
                        if 'cluster' in cluster_data['data']:
                            print(f"   - Cluster node: {cluster_data['data']['cluster']['node_info']['node_id']}")
                            print(f"   - Total connections: {cluster_data['data']['cluster']['total_connections']}")
                        else:
                            print("   - Running in single-node mode")
                except asyncio.TimeoutError:
                    print("⚠️ Cluster info not received")
                
                print("\n🎉 Clustering test completed!")
                print("\n💡 Note: For full clustering functionality, you need:")
                print("   1. Redis server running on localhost:6379")
                print("   2. Both nodes configured with the same Redis URL")
                print("   3. Messages will then propagate across the cluster")
                
    except Exception as e:
        print(f"❌ Error during clustering test: {e}")
        print("\n💡 Make sure both applications are running:")
        print(f"   - Node1: http://localhost:{node1_port}")
        print(f"   - Node2: http://localhost:{node2_port}")

if __name__ == "__main__":
    asyncio.run(test_clustering()) 