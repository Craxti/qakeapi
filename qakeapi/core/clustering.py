"""
WebSocket Clustering Support

Provides distributed WebSocket management across multiple server instances.
Uses Redis pub/sub for message synchronization and connection tracking.
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, Set, Optional, Any, Callable
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available. Install with: pip install redis")


class ClusterMessage:
    """Message for inter-node communication."""
    
    def __init__(
        self,
        message_type: str,
        data: Dict[str, Any],
        source_node: str,
        target_nodes: Optional[Set[str]] = None,
        message_id: Optional[str] = None
    ):
        self.message_type = message_type
        self.data = data
        self.source_node = source_node
        self.target_nodes = target_nodes or set()
        self.message_id = message_id or str(uuid.uuid4())
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "message_type": self.message_type,
            "data": self.data,
            "source_node": self.source_node,
            "target_nodes": list(self.target_nodes),
            "message_id": self.message_id,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ClusterMessage':
        """Create from dictionary."""
        return cls(
            message_type=data["message_type"],
            data=data["data"],
            source_node=data["source_node"],
            target_nodes=set(data.get("target_nodes", [])),
            message_id=data.get("message_id")
        )


class ClusterNode(ABC):
    """Abstract cluster node interface."""
    
    @abstractmethod
    async def start(self) -> None:
        """Start the cluster node."""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the cluster node."""
        pass
    
    @abstractmethod
    async def broadcast(self, message: ClusterMessage) -> None:
        """Broadcast message to other nodes."""
        pass
    
    @abstractmethod
    async def send_to_node(self, node_id: str, message: ClusterMessage) -> None:
        """Send message to specific node."""
        pass
    
    @abstractmethod
    def get_node_info(self) -> Dict[str, Any]:
        """Get node information."""
        pass


class RedisClusterNode(ClusterNode):
    """Redis-based cluster node implementation."""
    
    def __init__(
        self,
        node_id: str,
        redis_url: str = "redis://localhost:6379",
        cluster_channel: str = "websocket_cluster",
        heartbeat_interval: float = 30.0
    ):
        self.node_id = node_id
        self.redis_url = redis_url
        self.cluster_channel = cluster_channel
        self.heartbeat_interval = heartbeat_interval
        
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        self.running = False
        self.connected_nodes: Set[str] = set()
        self.message_handlers: Dict[str, Callable] = {}
        self.heartbeat_task: Optional[asyncio.Task] = None
        
        logger.info(f"Initialized Redis cluster node: {node_id}")
    
    async def start(self) -> None:
        """Start the cluster node."""
        if not REDIS_AVAILABLE:
            raise RuntimeError("Redis is not available. Install with: pip install redis")
        
        try:
            self.redis_client = redis.from_url(self.redis_url)
            self.pubsub = await self.redis_client.pubsub()
            
            # Subscribe to cluster channel
            await self.pubsub.subscribe(self.cluster_channel)
            
            # Set running status BEFORE starting tasks that use broadcast
            self.running = True
            
            # Start message listener
            asyncio.create_task(self._message_listener())
            
            # Start heartbeat
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
            # Announce node presence
            await self._announce_presence()
            
            logger.info(f"Redis cluster node {self.node_id} started")
            
        except Exception as e:
            logger.error(f"Failed to start Redis cluster node: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the cluster node."""
        # Stop heartbeat first
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        
        # Announce departure before setting running to False
        await self._announce_departure()
        
        # Set running to False after announcement
        self.running = False
        
        # Close Redis connections
        if self.pubsub:
            await self.pubsub.close()
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info(f"Redis cluster node {self.node_id} stopped")
    
    async def broadcast(self, message: ClusterMessage) -> None:
        """Broadcast message to other nodes."""
        if not self.running:
            raise RuntimeError("Cluster node is not running")
        
        # Set source node
        message.source_node = self.node_id
        
        # Publish to Redis
        await self.redis_client.publish(
            self.cluster_channel,
            json.dumps(message.to_dict())
        )
        
        logger.debug(f"Broadcasted message {message.message_id} to cluster")
    
    async def send_to_node(self, node_id: str, message: ClusterMessage) -> None:
        """Send message to specific node."""
        if not self.running:
            raise RuntimeError("Cluster node is not running")
        
        # Add target node
        message.target_nodes = {node_id}
        message.source_node = self.node_id
        
        # Publish to Redis
        await self.redis_client.publish(
            self.cluster_channel,
            json.dumps(message.to_dict())
        )
        
        logger.debug(f"Sent message {message.message_id} to node {node_id}")
    
    def get_node_info(self) -> Dict[str, Any]:
        """Get node information."""
        return {
            "node_id": self.node_id,
            "running": self.running,
            "connected_nodes": list(self.connected_nodes),
            "redis_url": self.redis_url,
            "cluster_channel": self.cluster_channel
        }
    
    def on_message(self, message_type: str) -> Callable:
        """Decorator for message handlers."""
        def decorator(handler: Callable) -> Callable:
            self.message_handlers[message_type] = handler
            return handler
        return decorator
    
    async def _message_listener(self) -> None:
        """Listen for messages from other nodes."""
        try:
            # Get the listener iterator
            listener = self.pubsub.listen()
            async for message in listener:
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        cluster_message = ClusterMessage.from_dict(data)
                        
                        # Skip own messages
                        if cluster_message.source_node == self.node_id:
                            continue
                        
                        # Check if message is for this node
                        if (cluster_message.target_nodes and 
                            self.node_id not in cluster_message.target_nodes):
                            continue
                        
                        # Handle message
                        await self._handle_cluster_message(cluster_message)
                        
                    except json.JSONDecodeError:
                        logger.warning("Invalid JSON in cluster message")
                    except Exception as e:
                        logger.error(f"Error handling cluster message: {e}")
                        
        except Exception as e:
            logger.error(f"Cluster message listener error: {e}")
    
    async def _handle_cluster_message(self, message: ClusterMessage) -> None:
        """Handle incoming cluster message."""
        try:
            message_type = message.message_type
            
            if message_type == "node_join":
                self.connected_nodes.add(message.data["node_id"])
                logger.info(f"Node {message.data['node_id']} joined cluster")
                
            elif message_type == "node_leave":
                self.connected_nodes.discard(message.data["node_id"])
                logger.info(f"Node {message.data['node_id']} left cluster")
                
            elif message_type == "heartbeat":
                # Update node status
                pass
                
            elif message_type in self.message_handlers:
                # Call custom handler
                await self.message_handlers[message_type](message)
                
            else:
                logger.debug(f"Unknown cluster message type: {message_type}")
                
        except Exception as e:
            logger.error(f"Error handling cluster message {message.message_id}: {e}")
    
    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeat messages."""
        while self.running:
            try:
                heartbeat = ClusterMessage(
                    message_type="heartbeat",
                    data={
                        "node_id": self.node_id,
                        "timestamp": datetime.now().isoformat()
                    },
                    source_node=self.node_id
                )
                
                await self.broadcast(heartbeat)
                await asyncio.sleep(self.heartbeat_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                await asyncio.sleep(5.0)
    
    async def _announce_presence(self) -> None:
        """Announce node presence to cluster."""
        join_message = ClusterMessage(
            message_type="node_join",
            data={
                "node_id": self.node_id,
                "timestamp": datetime.now().isoformat()
            },
            source_node=self.node_id
        )
        
        await self.broadcast(join_message)
    
    async def _announce_departure(self) -> None:
        """Announce node departure from cluster."""
        leave_message = ClusterMessage(
            message_type="node_leave",
            data={
                "node_id": self.node_id,
                "timestamp": datetime.now().isoformat()
            },
            source_node=self.node_id
        )
        
        await self.broadcast(leave_message)


class ClusteredWebSocketManager:
    """WebSocket manager with clustering support."""
    
    def __init__(
        self,
        cluster_node: ClusterNode,
        local_manager: Any = None  # Local WebSocket manager
    ):
        self.cluster_node = cluster_node
        self.local_manager = local_manager
        self.connection_mapping: Dict[str, str] = {}  # connection_id -> node_id
        
        # Register cluster message handlers
        self.cluster_node.on_message("websocket_broadcast")(self._handle_broadcast)
        self.cluster_node.on_message("websocket_send")(self._handle_send)
        self.cluster_node.on_message("connection_moved")(self._handle_connection_moved)
        
        logger.info("Initialized clustered WebSocket manager")
    
    async def add_connection(self, connection_id: str, node_id: str = None) -> None:
        """Add connection to cluster."""
        if node_id is None:
            node_id = self.cluster_node.node_id
        
        self.connection_mapping[connection_id] = node_id
        
        # Announce to cluster
        message = ClusterMessage(
            message_type="connection_added",
            data={
                "connection_id": connection_id,
                "node_id": node_id,
                "timestamp": datetime.now().isoformat()
            },
            source_node=self.cluster_node.node_id
        )
        
        await self.cluster_node.broadcast(message)
        logger.debug(f"Added connection {connection_id} to cluster")
    
    async def remove_connection(self, connection_id: str) -> None:
        """Remove connection from cluster."""
        node_id = self.connection_mapping.pop(connection_id, None)
        
        if node_id:
            # Announce to cluster
            message = ClusterMessage(
                message_type="connection_removed",
                data={
                    "connection_id": connection_id,
                    "node_id": node_id,
                    "timestamp": datetime.now().isoformat()
                },
                source_node=self.cluster_node.node_id
            )
            
            await self.cluster_node.broadcast(message)
            logger.debug(f"Removed connection {connection_id} from cluster")
    
    async def broadcast(self, message_data: Dict[str, Any], room: str = None) -> None:
        """Broadcast message across cluster."""
        # Send to local connections
        if self.local_manager:
            await self.local_manager.broadcast(message_data, room)
        
        # Send to other nodes
        cluster_message = ClusterMessage(
            message_type="websocket_broadcast",
            data={
                "message": message_data,
                "room": room,
                "timestamp": datetime.now().isoformat()
            },
            source_node=self.cluster_node.node_id
        )
        
        await self.cluster_node.broadcast(cluster_message)
        logger.debug(f"Broadcasted message across cluster")
    
    async def send_to_connection(self, connection_id: str, message_data: Dict[str, Any]) -> None:
        """Send message to specific connection across cluster."""
        node_id = self.connection_mapping.get(connection_id)
        
        if node_id == self.cluster_node.node_id:
            # Send locally
            if self.local_manager:
                await self.local_manager.send_to_connection(connection_id, message_data)
        else:
            # Send to other node
            cluster_message = ClusterMessage(
                message_type="websocket_send",
                data={
                    "connection_id": connection_id,
                    "message": message_data,
                    "timestamp": datetime.now().isoformat()
                },
                source_node=self.cluster_node.node_id,
                target_nodes={node_id} if node_id else set()
            )
            
            await self.cluster_node.send_to_node(node_id, cluster_message)
        
        logger.debug(f"Sent message to connection {connection_id}")
    
    async def _handle_broadcast(self, message: ClusterMessage) -> None:
        """Handle broadcast message from other nodes."""
        if self.local_manager:
            message_data = message.data["message"]
            room = message.data.get("room")
            await self.local_manager.broadcast(message_data, room)
    
    async def _handle_send(self, message: ClusterMessage) -> None:
        """Handle send message from other nodes."""
        if self.local_manager:
            connection_id = message.data["connection_id"]
            message_data = message.data["message"]
            await self.local_manager.send_to_connection(connection_id, message_data)
    
    async def _handle_connection_moved(self, message: ClusterMessage) -> None:
        """Handle connection moved to another node."""
        connection_id = message.data["connection_id"]
        new_node_id = message.data["node_id"]
        
        # Update mapping
        if connection_id in self.connection_mapping:
            self.connection_mapping[connection_id] = new_node_id
            logger.debug(f"Connection {connection_id} moved to node {new_node_id}")
    
    def get_cluster_info(self) -> Dict[str, Any]:
        """Get cluster information."""
        return {
            "node_info": self.cluster_node.get_node_info(),
            "connection_mapping": self.connection_mapping,
            "total_connections": len(self.connection_mapping)
        }


# Factory function for easy setup
def create_clustered_manager(
    node_id: str,
    redis_url: str = "redis://localhost:6379",
    local_manager: Any = None
) -> ClusteredWebSocketManager:
    """Create a clustered WebSocket manager."""
    cluster_node = RedisClusterNode(node_id, redis_url)
    return ClusteredWebSocketManager(cluster_node, local_manager) 