from typing import Dict, List, Any, Optional, Callable, Awaitable
from .protocol import Message, MessageType, ProtocolHandler
import asyncio
from collections import defaultdict
import logging
from datetime import datetime

class MessageBroker:
    def __init__(self):
        self.subscribers: Dict[str, List[Callable[[Message], Awaitable[None]]]] = defaultdict(list)
        self.protocol_handler = ProtocolHandler()
        self.message_queue: asyncio.Queue[Message] = asyncio.Queue()
        self.message_history: Dict[str, List[Message]] = defaultdict(list)
        asyncio.create_task(self._process_queue())
    
    async def publish(self, message: Message) -> None:
        await self.message_queue.put(message)
        self.message_history[message.sender].append(message)
    
    def subscribe(
        self,
        topic: str,
        callback: Callable[[Message], Awaitable[None]]
    ) -> None:
        self.subscribers[topic].append(callback)
    
    def unsubscribe(
        self,
        topic: str,
        callback: Callable[[Message], Awaitable[None]]
    ) -> None:
        if topic in self.subscribers:
            self.subscribers[topic].remove(callback)
            if not self.subscribers[topic]:
                del self.subscribers[topic]
    
    async def _process_queue(self) -> None:
        while True:
            message = await self.message_queue.get()
            try:
                response = await self.protocol_handler.handle_message(message)
                if response:
                    await self.publish(response)
                
                await self._notify_subscribers(message)
            except Exception as e:
                logging.error(f"Error processing message: {str(e)}")
            finally:
                self.message_queue.task_done()
    
    async def _notify_subscribers(self, message: Message) -> None:
        tasks = []
        for topic, callbacks in self.subscribers.items():
            if topic in [message.recipient, "*"]:
                for callback in callbacks:
                    tasks.append(asyncio.create_task(callback(message)))
        if tasks:
            await asyncio.gather(*tasks)
    
    def get_message_history(
        self,
        agent_id: str,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> List[Message]:
        messages = self.message_history.get(agent_id, [])
        if not (start_time or end_time):
            return messages
        
        filtered_messages = []
        for message in messages:
            if start_time and message.timestamp < start_time:
                continue
            if end_time and message.timestamp > end_time:
                continue
            filtered_messages.append(message)
        return filtered_messages

class MessageHandler:
    def __init__(self, agent_id: str, broker: MessageBroker):
        self.agent_id = agent_id
        self.broker = broker
        self.pending_requests: Dict[str, asyncio.Future] = {}
        
    async def send_request(
        self,
        recipient: str,
        content: Dict[str, Any],
        timeout: float = 30.0
    ) -> Optional[Message]:
        message = Message.create(
            MessageType.REQUEST,
            self.agent_id,
            recipient,
            content
        )
        
        future = asyncio.Future()
        self.pending_requests[message.id] = future
        
        try:
            await self.broker.publish(message)
            return await asyncio.wait_for(future, timeout)
        except asyncio.TimeoutError:
            return None
        finally:
            self.pending_requests.pop(message.id, None)
    
    async def handle_message(self, message: Message) -> None:
        if message.correlation_id in self.pending_requests:
            future = self.pending_requests[message.correlation_id]
            if not future.done():
                future.set_result(message)
        
        if message.type == MessageType.REQUEST:
            response = await self._handle_request(message)
            if response:
                await self.broker.publish(response)
    
    async def _handle_request(self, message: Message) -> Optional[Message]:
        return Message.create(
            MessageType.RESPONSE,
            self.agent_id,
            message.sender,
            {"status": "processed"},
            message.id
        )