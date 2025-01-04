from typing import Dict, List, Optional, Any
from uuid import uuid4
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class AgentMetadata:
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    reputation_score: float = 0.0
    total_transactions: int = 0
    successful_transactions: int = 0

class Agent:
    def __init__(
        self,
        name: str,
        agent_type: str,
        capabilities: List[str],
        metadata: Optional[AgentMetadata] = None
    ):
        self.id = str(uuid4())
        self.name = name
        self.agent_type = agent_type
        self.capabilities = capabilities
        self.metadata = metadata or AgentMetadata()
        self.state: Dict[str, Any] = {}
        
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError
        
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError
        
    async def update_state(self, new_state: Dict[str, Any]) -> None:
        self.state.update(new_state)
        self.metadata.last_active = datetime.now()
        
    def get_capabilities(self) -> List[str]:
        return self.capabilities
        
    def update_reputation(self, score: float) -> None:
        self.metadata.reputation_score = (
            self.metadata.reputation_score * self.metadata.total_transactions + score
        ) / (self.metadata.total_transactions + 1)
        self.metadata.total_transactions += 1