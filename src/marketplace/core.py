from typing import Dict, List, Optional, Any
from ..agent.base import Agent
from ..agent.registry import AgentRegistry
from ..blockchain.core import BlockchainManager
from dataclasses import dataclass
from datetime import datetime
import asyncio
from uuid import uuid4

@dataclass
class Transaction:
    id: str
    requester_id: str
    provider_id: str
    service_type: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime]
    amount: float
    metadata: Dict[str, Any]

class Marketplace:
    def __init__(self, agent_registry: AgentRegistry, blockchain_manager: BlockchainManager):
        self.agent_registry = agent_registry
        self.blockchain_manager = blockchain_manager
        self.active_transactions: Dict[str, Transaction] = {}
        self.transaction_history: List[Transaction] = []
        
    async def request_service(
        self,
        requester_id: str,
        service_type: str,
        requirements: Dict[str, Any]
    ) -> Optional[str]:
        providers = self.agent_registry.get_agents_by_capability(service_type)
        if not providers:
            return None
            
        provider = await self._select_best_provider(providers, requirements)
        if not provider:
            return None
            
        transaction = Transaction(
            id=str(uuid4()),
            requester_id=requester_id,
            provider_id=provider.id,
            service_type=service_type,
            status="pending",
            created_at=datetime.now(),
            completed_at=None,
            amount=0.0,
            metadata=requirements
        )
        
        self.active_transactions[transaction.id] = transaction
        await self.blockchain_manager.record_transaction(transaction)
        return transaction.id
        
    async def execute_transaction(self, transaction_id: str) -> Dict[str, Any]:
        if transaction_id not in self.active_transactions:
            return {"status": "error", "message": "Transaction not found"}
            
        transaction = self.active_transactions[transaction_id]
        provider = self.agent_registry.get_agent(transaction.provider_id)
        
        if not provider:
            return {"status": "error", "message": "Provider not found"}
            
        try:
            result = await provider.handle_request(transaction.metadata)
            transaction.status = "completed"
            transaction.completed_at = datetime.now()
            
            self.transaction_history.append(transaction)
            del self.active_transactions[transaction_id]
            
            await self.blockchain_manager.update_transaction(transaction)
            return {"status": "success", "result": result}
            
        except Exception as e:
            transaction.status = "failed"
            await self.blockchain_manager.update_transaction(transaction)
            return {"status": "error", "message": str(e)}
            
    async def _select_best_provider(
        self,
        providers: List[Agent],
        requirements: Dict[str, Any]
    ) -> Optional[Agent]:
        if not providers:
            return None
            
        return max(providers, key=lambda x: x.metadata.reputation_score)
        
    def get_transaction_status(self, transaction_id: str) -> Optional[str]:
        if transaction_id in self.active_transactions:
            return self.active_transactions[transaction_id].status
        
        for tx in self.transaction_history:
            if tx.id == transaction_id:
                return tx.status
                
        return None
        
    def get_agent_transactions(self, agent_id: str) -> List[Transaction]:
        return [
            tx for tx in self.transaction_history
            if tx.requester_id == agent_id or tx.provider_id == agent_id
        ]