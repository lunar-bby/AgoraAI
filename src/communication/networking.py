from typing import Dict, Set, Optional, Callable, Awaitable
import asyncio
import logging
from .protocol import Message, MessageType
from .messaging import MessageBroker
import json

class NetworkNode:
    def __init__(
        self,
        node_id: str,
        host: str = "localhost",
        port: int = 8000
    ):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.connections: Dict[str, asyncio.StreamWriter] = {}
        self.message_broker = MessageBroker()
        self.server: Optional[asyncio.Server] = None
        self.peer_info: Dict[str, Dict[str, Any]] = {}
        
    async def start(self) -> None:
        self.server = await asyncio.start_server(
            self._handle_connection,
            self.host,
            self.port
        )
        logging.info(f"Node {self.node_id} listening on {self.host}:{self.port}")
        await self.server.serve_forever()
        
    async def stop(self) -> None:
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            
        for peer_id in list(self.connections.keys()):
            await self.disconnect_from_peer(peer_id)
    
    async def connect_to_peer(self, peer_id: str, host: str, port: int) -> bool:
        try:
            reader, writer = await asyncio.open_connection(host, port)
            self.connections[peer_id] = writer
            self.peer_info[peer_id] = {"host": host, "port": port}
            
            asyncio.create_task(self._handle_peer_messages(peer_id, reader))
            await self._send_hello_message(writer)
            return True
            
        except Exception as e:
            logging.error(f"Failed to connect to peer {peer_id}: {str(e)}")
            return False
    
    async def disconnect_from_peer(self, peer_id: str) -> None:
        if peer_id in self.connections:
            writer = self.connections[peer_id]
            writer.close()
            await writer.wait_closed()
            del self.connections[peer_id]
            self.peer_info.pop(peer_id, None)
    
    async def broadcast_message(self, message: Message) -> None:
        for peer_id, writer in self.connections.items():
            try:
                await self._send_message(writer, message)
            except Exception as e:
                logging.error(f"Failed to send message to peer {peer_id}: {str(e)}")
                await self.disconnect_from_peer(peer_id)
    
    async def _handle_connection(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter
    ) -> None:
        peer_addr = writer.get_extra_info('peername')
        peer_id = None
        
        try:
            hello_message = await self._receive_message(reader)
            if hello_message.type != MessageType.HEARTBEAT:
                raise ValueError("First message must be HEARTBEAT")
                
            peer_id = hello_message.sender
            self.connections[peer_id] = writer
            self.peer_info[peer_id] = {
                "host": peer_addr[0],
                "port": peer_addr[1]
            }
            
            asyncio.create_task(self._handle_peer_messages(peer_id, reader))
            
        except Exception as e:
            logging.error(f"Error handling new connection: {str(e)}")
            writer.close()
            await writer.wait_closed()
            if peer_id and peer_id in self.connections:
                del self.connections[peer_id]
    
    async def _handle_peer_messages(
        self,
        peer_id: str,
        reader: asyncio.StreamReader
    ) -> None:
        try:
            while True:
                message = await self._receive_message(reader)
                await self.message_broker.publish(message)
                
        except asyncio.IncompleteReadError:
            logging.info(f"Peer {peer_id} disconnected")
        except Exception as e:
            logging.error(f"Error handling messages from peer {peer_id}: {str(e)}")
        finally:
            await self.disconnect_from_peer(peer_id)
    
    async def _send_message(
        self,
        writer: asyncio.StreamWriter,
        message: Message
    ) -> None:
        message_data = message.to_json().encode()
        writer.write(len(message_data).to_bytes(4, 'big'))
        writer.write(message_data)
        await writer.drain()
    
    async def _receive_message(
        self,
        reader: asyncio.StreamReader
    ) -> Message:
        length_bytes = await reader.readexactly(4)
        length = int.from_bytes(length_bytes, 'big')
        message_data = await reader.readexactly(length)
        return Message.from_json(message_data.decode())
    
    async def _send_hello_message(self, writer: asyncio.StreamWriter) -> None:
        hello_message = Message.create(
            MessageType.HEARTBEAT,
            self.node_id,
            "*",
            {"host": self.host, "port": self.port}
        )
        await self._send_message(writer, hello_message)

class NetworkDiscovery:
    def __init__(self, node: NetworkNode):
        self.node = node
        self.known_peers: Dict[str, Dict[str, Any]] = {}
        self._discovery_interval = 60
        asyncio.create_task(self._periodic_discovery())
    
    async def discover_peers(self, seed_nodes: List[Dict[str, Any]]) -> None:
        for seed in seed_nodes:
            if seed["id"] != self.node.node_id:
                await self.node.connect_to_peer(
                    seed["id"],
                    seed["host"],
                    seed["port"]
                )
    
    async def _periodic_discovery(self) -> None:
        while True:
            try:
                discovery_message = Message.create(
                    MessageType.REQUEST,
                    self.node.node_id,
                    "*",
                    {"type": "discovery"}
                )
                await self.node.broadcast_message(discovery_message)
            except Exception as e:
                logging.error(f"Error in periodic discovery: {str(e)}")
            
            await asyncio.sleep(self._discovery_interval)