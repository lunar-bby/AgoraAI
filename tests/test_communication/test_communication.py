import pytest
import asyncio
from datetime import datetime
from agoraai.communication.protocol import Message, MessageType, ProtocolHandler
from agoraai.communication.messaging import MessageBroker, MessageHandler
from agoraai.communication.networking import NetworkNode, NetworkDiscovery

@pytest.fixture
def protocol_handler():
    return ProtocolHandler()

@pytest.fixture
def message_broker():
    return MessageBroker()

@pytest.fixture
def network_node():
    return NetworkNode("test_node", "localhost", 8000)

class TestProtocol:
    def test_message_creation(self):
        message = Message.create(
            MessageType.REQUEST,
            "sender1",
            "receiver1",
            {"action": "test"}
        )
        
        assert message.type == MessageType.REQUEST
        assert message.sender == "sender1"
        assert message.recipient == "receiver1"
        assert isinstance(message.timestamp, float)
        assert message.id is not None
        
    def test_message_serialization(self):
        original_message = Message.create(
            MessageType.REQUEST,
            "sender1",
            "receiver1",
            {"action": "test"}
        )
        
        json_str = original_message.to_json()
        deserialized_message = Message.from_json(json_str)
        
        assert deserialized_message.id == original_message.id
        assert deserialized_message.type == original_message.type
        assert deserialized_message.sender == original_message.sender
        assert deserialized_message.content == original_message.content
        
    @pytest.mark.asyncio
    async def test_protocol_handler(self, protocol_handler):
        message = Message.create(
            MessageType.REQUEST,
            "sender1",
            "receiver1",
            {"action": "test"}
        )
        
        response = await protocol_handler.handle_message(message)
        assert response is not None
        assert response.type == MessageType.RESPONSE
        assert response.correlation_id == message.id

class TestMessaging:
    @pytest.mark.asyncio
    async def test_message_broker_publish(self, message_broker):
        message = Message.create(
            MessageType.EVENT,
            "sender1",
            "receiver1",
            {"event": "test"}
        )
        
        await message_broker.publish(message)
        history = message_broker.get_message_history("sender1")
        assert len(history) == 1
        assert history[0].id == message.id
        
    @pytest.mark.asyncio
    async def test_message_subscription(self, message_broker):
        received_messages = []
        
        async def message_callback(message):
            received_messages.append(message)
            
        message_broker.subscribe("receiver1", message_callback)
        
        message = Message.create(
            MessageType.EVENT,
            "sender1",
            "receiver1",
            {"event": "test"}
        )
        
        await message_broker.publish(message)
        await asyncio.sleep(0.1)  # Allow time for async processing
        
        assert len(received_messages) == 1
        assert received_messages[0].id == message.id
        
    @pytest.mark.asyncio
    async def test_message_handler(self, message_broker):
        handler = MessageHandler("agent1", message_broker)
        
        response_message = None
        async def handle_response(message):
            nonlocal response_message
            response_message = message
            
        message_broker.subscribe("agent1", handle_response)
        
        await handler.send_request(
            "agent2",
            {"action": "test"},
            timeout=1.0
        )
        
        assert response_message is None  # No response since agent2 doesn't exist

class TestNetworking:
    @pytest.mark.asyncio
    async def test_network_node_connection(self, network_node):
        # Start the node
        server_task = asyncio.create_task(network_node.start())
        await asyncio.sleep(0.1)  # Allow time for server to start
        
        # Try to connect to a peer
        success = await network_node.connect_to_peer(
            "peer1",
            "localhost",
            8001
        )
        assert not success  # Should fail since peer doesn't exist
        
        # Cleanup
        await network_node.stop()
        server_task.cancel()
        
    @pytest.mark.asyncio
    async def test_message_broadcasting(self, network_node):
        message = Message.create(
            MessageType.EVENT,
            "node1",
            "*",
            {"event": "broadcast"}
        )
        
        await network_node.broadcast_message(message)
        # No assertions needed, just testing that broadcast doesn't raise exceptions
        
    @pytest.mark.asyncio
    async def test_network_discovery(self, network_node):
        discovery = NetworkDiscovery(network_node)
        
        await discovery.discover_peers([
            {"id": "peer1", "host": "localhost", "port": 8001},
            {"id": "peer2", "host": "localhost", "port": 8002}
        ])
        
        # Peers won't actually connect since they don't exist
        assert len(network_node.connections) == 0