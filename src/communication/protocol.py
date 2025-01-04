from typing import Dict, Any, Optional
from enum import Enum, auto
from dataclasses import dataclass
import json
import uuid
from datetime import datetime

class MessageType(Enum):
    REQUEST = auto()
    RESPONSE = auto()
    EVENT = auto()
    ERROR = auto()
    HEARTBEAT = auto()

@dataclass
class Message:
    id: str
    type: MessageType
    sender: str
    recipient: str
    content: Dict[str, Any]
    timestamp: float
    correlation_id: Optional[str] = None
    
    @classmethod
    def create(
        cls,
        msg_type: MessageType,
        sender: str,
        recipient: str,
        content: Dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> 'Message':
        return cls(
            id=str(uuid.uuid4()),
            type=msg_type,
            sender=sender,
            recipient=recipient,
            content=content,
            timestamp=datetime.now().timestamp(),
            correlation_id=correlation_id
        )
    
    def to_json(self) -> str:
        return json.dumps({
            "id": self.id,
            "type": self.type.name,
            "sender": self.sender,
            "recipient": self.recipient,
            "content": self.content,
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id
        })
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        data = json.loads(json_str)
        data["type"] = MessageType[data["type"]]
        return cls(**data)

class ProtocolHandler:
    def __init__(self):
        self.message_handlers = {
            MessageType.REQUEST: self._handle_request,
            MessageType.RESPONSE: self._handle_response,
            MessageType.EVENT: self._handle_event,
            MessageType.ERROR: self._handle_error,
            MessageType.HEARTBEAT: self._handle_heartbeat
        }
    
    async def handle_message(self, message: Message) -> Optional[Message]:
        handler = self.message_handlers.get(message.type)
        if handler:
            return await handler(message)
        return None
    
    async def _handle_request(self, message: Message) -> Message:
        return Message.create(
            MessageType.RESPONSE,
            message.recipient,
            message.sender,
            {"status": "received"},
            message.id
        )
    
    async def _handle_response(self, message: Message) -> None:
        return None
    
    async def _handle_event(self, message: Message) -> None:
        return None
    
    async def _handle_error(self, message: Message) -> Message:
        return Message.create(
            MessageType.ERROR,
            message.recipient,
            message.sender,
            {"error": "Error processed"},
            message.id
        )
    
    async def _handle_heartbeat(self, message: Message) -> Message:
        return Message.create(
            MessageType.HEARTBEAT,
            message.recipient,
            message.sender,
            {"status": "alive"},
            message.id
        )