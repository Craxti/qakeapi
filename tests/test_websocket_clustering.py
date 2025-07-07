"""Tests for WebSocket clustering functionality."""

import pytest
import asyncio
import json
from datetime import datetime
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from qakeapi.core.clustering import (
    ClusterMessage,
    ClusterNode,
    RedisClusterNode,
    ClusteredWebSocketManager,
    create_clustered_manager
)


class TestClusterMessage:
    """Test cluster message functionality."""
    
    def test_message_creation(self):
        """Test cluster message creation."""
        message = ClusterMessage(
            message_type="test",
            data={"key": "value"},
            source_node="node1"
        )
        
        assert message.message_type == "test"
        assert message.data == {"key": "value"}
        assert message.source_node == "node1"
        assert message.message_id is not None
        assert message.timestamp is not None
    
    def test_message_with_target_nodes(self):
        """Test message with target nodes."""
        message = ClusterMessage(
            message_type="test",
            data={"key": "value"},
            source_node="node1",
            target_nodes={"node2", "node3"}
        )
        
        assert message.target_nodes == {"node2", "node3"}
    
    def test_message_serialization(self):
        """Test message serialization and deserialization."""
        original = ClusterMessage(
            message_type="test",
            data={"key": "value", "nested": {"a": 1}},
            source_node="node1",
            target_nodes={"node2"}
        )
        
        # Serialize
        data = original.to_dict()
        
        # Deserialize
        restored = ClusterMessage.from_dict(data)
        
        assert restored.message_type == original.message_type
        assert restored.data == original.data
        assert restored.source_node == original.source_node
        assert restored.target_nodes == original.target_nodes
        assert restored.message_id == original.message_id


class TestRedisClusterNode:
    """Test Redis cluster node functionality."""
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        with patch('qakeapi.core.clustering.redis') as mock_redis:
            mock_redis.from_url.return_value = AsyncMock()
            mock_redis.client.PubSub = AsyncMock
            yield mock_redis
    
    @pytest.mark.asyncio
    async def test_node_initialization(self, mock_redis):
        """Test cluster node initialization."""
        node = RedisClusterNode("test-node", "redis://localhost:6379")
        
        assert node.node_id == "test-node"
        assert node.redis_url == "redis://localhost:6379"
        assert node.cluster_channel == "websocket_cluster"
        assert not node.running
    
    @pytest.mark.asyncio
    async def test_node_start_stop(self, mock_redis):
        """Test node start and stop."""
        node = RedisClusterNode("test-node")
        
        # Mock Redis client
        mock_client = AsyncMock()
        mock_pubsub = AsyncMock()
        mock_redis.from_url.return_value = mock_client
        mock_client.pubsub.return_value = mock_pubsub
        mock_pubsub.subscribe = AsyncMock()
        mock_pubsub.listen.return_value = []
        
        # Start node
        await node.start()
        
        assert node.running
        assert mock_client.pubsub.called
        assert mock_pubsub.subscribe.called
        
        # Stop node
        await node.stop()
        
        assert not node.running
        assert mock_pubsub.close.called
        assert mock_client.close.called
    
    @pytest.mark.asyncio
    async def test_broadcast_message(self, mock_redis):
        """Test broadcasting messages."""
        node = RedisClusterNode("test-node")
        
        # Mock Redis client
        mock_client = AsyncMock()
        mock_pubsub = AsyncMock()
        mock_redis.from_url.return_value = mock_client
        mock_client.pubsub.return_value = mock_pubsub
        mock_pubsub.subscribe = AsyncMock()
        mock_pubsub.listen.return_value = []
        
        # Start node
        await node.start()
        
        # Create and broadcast message
        message = ClusterMessage(
            message_type="test",
            data={"key": "value"},
            source_node="test-node"
        )
        
        await node.broadcast(message)
        
        # Check that message was published (node_join + our message = 2 calls)
        assert mock_client.publish.call_count == 2
        
        # Get the last call (our message)
        call_args = mock_client.publish.call_args_list[-1]
        assert call_args[0][0] == "websocket_cluster"
        
        # Verify message content
        published_data = json.loads(call_args[0][1])
        assert published_data["message_type"] == "test"
        assert published_data["data"] == {"key": "value"}
        
        await node.stop()
    
    @pytest.mark.asyncio
    async def test_send_to_node(self, mock_redis):
        """Test sending message to specific node."""
        node = RedisClusterNode("test-node")
        
        # Mock Redis client
        mock_client = AsyncMock()
        mock_pubsub = AsyncMock()
        mock_redis.from_url.return_value = mock_client
        mock_client.pubsub.return_value = mock_pubsub
        mock_pubsub.subscribe = AsyncMock()
        mock_pubsub.listen.return_value = []
        
        # Start node
        await node.start()
        
        # Send message to specific node
        message = ClusterMessage(
            message_type="test",
            data={"key": "value"},
            source_node="test-node"
        )
        
        await node.send_to_node("target-node", message)
        
        # Check that message was published with target (node_join + our message = 2 calls)
        assert mock_client.publish.call_count == 2
        
        # Get the last call (our message)
        call_args = mock_client.publish.call_args_list[-1]
        published_data = json.loads(call_args[0][1])
        assert "target-node" in published_data["target_nodes"]
        
        await node.stop()
    
    @pytest.mark.asyncio
    async def test_message_handler_decorator(self, mock_redis):
        """Test message handler decorator."""
        node = RedisClusterNode("test-node")
        
        handler_called = False
        
        @node.on_message("custom_type")
        async def custom_handler(message):
            nonlocal handler_called
            handler_called = True
        
        assert "custom_type" in node.message_handlers
        assert node.message_handlers["custom_type"] == custom_handler
    
    @pytest.mark.asyncio
    async def test_node_info(self, mock_redis):
        """Test node information."""
        node = RedisClusterNode("test-node", "redis://test:6379")
        
        info = node.get_node_info()
        
        assert info["node_id"] == "test-node"
        assert info["redis_url"] == "redis://test:6379"
        assert info["cluster_channel"] == "websocket_cluster"
        assert not info["running"]


class TestClusteredWebSocketManager:
    """Test clustered WebSocket manager functionality."""
    
    @pytest.fixture
    def mock_cluster_node(self):
        """Mock cluster node."""
        node = Mock()
        node.node_id = "test-node"
        node.get_node_info.return_value = {"node_id": "test-node", "running": True}
        node.on_message.return_value = lambda func: func
        return node
    
    @pytest.fixture
    def mock_local_manager(self):
        """Mock local WebSocket manager."""
        manager = AsyncMock()
        manager.broadcast = AsyncMock()
        manager.send_to_connection = AsyncMock()
        return manager
    
    @pytest.mark.asyncio
    async def test_manager_initialization(self, mock_cluster_node, mock_local_manager):
        """Test clustered manager initialization."""
        manager = ClusteredWebSocketManager(mock_cluster_node, mock_local_manager)
        
        assert manager.cluster_node == mock_cluster_node
        assert manager.local_manager == mock_local_manager
        assert len(manager.connection_mapping) == 0
    
    @pytest.mark.asyncio
    async def test_add_connection(self, mock_cluster_node, mock_local_manager):
        """Test adding connection to cluster."""
        manager = ClusteredWebSocketManager(mock_cluster_node, mock_local_manager)
        
        # Mock broadcast
        mock_cluster_node.broadcast = AsyncMock()
        
        await manager.add_connection("conn-123")
        
        assert "conn-123" in manager.connection_mapping
        assert manager.connection_mapping["conn-123"] == "test-node"
        assert mock_cluster_node.broadcast.called
    
    @pytest.mark.asyncio
    async def test_remove_connection(self, mock_cluster_node, mock_local_manager):
        """Test removing connection from cluster."""
        manager = ClusteredWebSocketManager(mock_cluster_node, mock_local_manager)
        
        # Add connection first
        manager.connection_mapping["conn-123"] = "test-node"
        
        # Mock broadcast
        mock_cluster_node.broadcast = AsyncMock()
        
        await manager.remove_connection("conn-123")
        
        assert "conn-123" not in manager.connection_mapping
        assert mock_cluster_node.broadcast.called
    
    @pytest.mark.asyncio
    async def test_broadcast_local(self, mock_cluster_node, mock_local_manager):
        """Test broadcasting to local connections."""
        manager = ClusteredWebSocketManager(mock_cluster_node, mock_local_manager)
        
        # Mock broadcast
        mock_cluster_node.broadcast = AsyncMock()
        
        message_data = {"type": "test", "data": "value"}
        await manager.broadcast(message_data, "test-room")
        
        # Check local broadcast
        mock_local_manager.broadcast.assert_called_once_with(message_data, "test-room")
        
        # Check cluster broadcast
        assert mock_cluster_node.broadcast.called
    
    @pytest.mark.asyncio
    async def test_send_to_local_connection(self, mock_cluster_node, mock_local_manager):
        """Test sending to local connection."""
        manager = ClusteredWebSocketManager(mock_cluster_node, mock_local_manager)
        
        # Add local connection
        manager.connection_mapping["conn-123"] = "test-node"
        
        message_data = {"type": "test", "data": "value"}
        await manager.send_to_connection("conn-123", message_data)
        
        # Should send locally
        mock_local_manager.send_to_connection.assert_called_once_with("conn-123", message_data)
    
    @pytest.mark.asyncio
    async def test_send_to_remote_connection(self, mock_cluster_node, mock_local_manager):
        """Test sending to remote connection."""
        manager = ClusteredWebSocketManager(mock_cluster_node, mock_local_manager)
        
        # Add remote connection
        manager.connection_mapping["conn-123"] = "remote-node"
        
        # Mock send to node
        mock_cluster_node.send_to_node = AsyncMock()
        
        message_data = {"type": "test", "data": "value"}
        await manager.send_to_connection("conn-123", message_data)
        
        # Should send to remote node
        mock_cluster_node.send_to_node.assert_called_once()
        call_args = mock_cluster_node.send_to_node.call_args
        assert call_args[0][0] == "remote-node"  # node_id
        assert isinstance(call_args[0][1], ClusterMessage)  # message
    
    @pytest.mark.asyncio
    async def test_handle_broadcast_from_cluster(self, mock_cluster_node, mock_local_manager):
        """Test handling broadcast from cluster."""
        manager = ClusteredWebSocketManager(mock_cluster_node, mock_local_manager)
        
        # Create cluster message
        cluster_message = ClusterMessage(
            message_type="websocket_broadcast",
            data={
                "message": {"type": "test", "data": "value"},
                "room": "test-room"
            },
            source_node="other-node"
        )
        
        await manager._handle_broadcast(cluster_message)
        
        # Should broadcast locally
        mock_local_manager.broadcast.assert_called_once_with(
            {"type": "test", "data": "value"},
            "test-room"
        )
    
    @pytest.mark.asyncio
    async def test_handle_send_from_cluster(self, mock_cluster_node, mock_local_manager):
        """Test handling send from cluster."""
        manager = ClusteredWebSocketManager(mock_cluster_node, mock_local_manager)
        
        # Create cluster message
        cluster_message = ClusterMessage(
            message_type="websocket_send",
            data={
                "connection_id": "conn-123",
                "message": {"type": "test", "data": "value"}
            },
            source_node="other-node"
        )
        
        await manager._handle_send(cluster_message)
        
        # Should send locally
        mock_local_manager.send_to_connection.assert_called_once_with(
            "conn-123",
            {"type": "test", "data": "value"}
        )
    
    @pytest.mark.asyncio
    async def test_handle_connection_moved(self, mock_cluster_node, mock_local_manager):
        """Test handling connection moved to another node."""
        manager = ClusteredWebSocketManager(mock_cluster_node, mock_local_manager)
        
        # Add connection
        manager.connection_mapping["conn-123"] = "old-node"
        
        # Create cluster message
        cluster_message = ClusterMessage(
            message_type="connection_moved",
            data={
                "connection_id": "conn-123",
                "node_id": "new-node"
            },
            source_node="other-node"
        )
        
        await manager._handle_connection_moved(cluster_message)
        
        # Should update mapping
        assert manager.connection_mapping["conn-123"] == "new-node"
    
    def test_get_cluster_info(self, mock_cluster_node, mock_local_manager):
        """Test getting cluster information."""
        manager = ClusteredWebSocketManager(mock_cluster_node, mock_local_manager)
        
        # Add some connections
        manager.connection_mapping["conn-1"] = "test-node"
        manager.connection_mapping["conn-2"] = "remote-node"
        
        info = manager.get_cluster_info()
        
        assert info["total_connections"] == 2
        assert info["connection_mapping"] == {"conn-1": "test-node", "conn-2": "remote-node"}
        assert "node_info" in info


class TestFactoryFunction:
    """Test factory function for creating clustered managers."""
    
    @patch('qakeapi.core.clustering.RedisClusterNode')
    def test_create_clustered_manager(self, mock_redis_node_class):
        """Test factory function."""
        mock_node = Mock()
        mock_redis_node_class.return_value = mock_node
        
        local_manager = Mock()
        
        manager = create_clustered_manager(
            node_id="test-node",
            redis_url="redis://test:6379",
            local_manager=local_manager
        )
        
        # Check Redis node was created
        mock_redis_node_class.assert_called_once_with("test-node", "redis://test:6379")
        
        # Check manager was created
        assert isinstance(manager, ClusteredWebSocketManager)
        assert manager.cluster_node == mock_node
        assert manager.local_manager == local_manager


@pytest.mark.asyncio
async def test_integration_scenario():
    """Test integration scenario with multiple nodes."""
    # This would require actual Redis server for full integration testing
    # For now, we'll test the basic flow with mocks
    
    with patch('qakeapi.core.clustering.REDIS_AVAILABLE', True):
        # Create two cluster nodes
        node1 = RedisClusterNode("node1")
        node2 = RedisClusterNode("node2")
        
        # Create local managers
        local_manager1 = AsyncMock()
        local_manager2 = AsyncMock()
        
        # Create clustered managers
        manager1 = ClusteredWebSocketManager(node1, local_manager1)
        manager2 = ClusteredWebSocketManager(node2, local_manager2)
        
        # Test that managers are properly initialized
        assert manager1.cluster_node.node_id == "node1"
        assert manager2.cluster_node.node_id == "node2"
        
        # Test connection mapping without starting cluster
        manager1.connection_mapping["conn-1"] = "node1"
        manager2.connection_mapping["conn-2"] = "node2"
        
        assert "conn-1" in manager1.connection_mapping
        assert "conn-2" in manager2.connection_mapping
        assert manager1.connection_mapping["conn-1"] == "node1"
        assert manager2.connection_mapping["conn-2"] == "node2" 