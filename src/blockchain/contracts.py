from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
import json

class ContractState(Enum):
    PENDING = auto()
    ACTIVE = auto()
    COMPLETED = auto()
    CANCELLED = auto()
    DISPUTED = auto()

@dataclass
class ServiceContract:
    contract_id: str
    provider_id: str
    consumer_id: str
    service_type: str
    terms: Dict[str, Any]
    start_time: datetime
    end_time: Optional[datetime]
    state: ContractState
    payment_amount: float
    payment_status: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "provider_id": self.provider_id,
            "consumer_id": self.consumer_id,
            "service_type": self.service_type,
            "terms": self.terms,
            "start_time": self.start_time.timestamp(),
            "end_time": self.end_time.timestamp() if self.end_time else None,
            "state": self.state.name,
            "payment_amount": self.payment_amount,
            "payment_status": self.payment_status
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ServiceContract':
        data["start_time"] = datetime.fromtimestamp(data["start_time"])
        if data["end_time"]:
            data["end_time"] = datetime.fromtimestamp(data["end_time"])
        data["state"] = ContractState[data["state"]]
        return cls(**data)

class SmartContract:
    def __init__(self, contract: ServiceContract):
        self.contract = contract
        self.events: List[Dict[str, Any]] = []
        
    def validate_transition(self, new_state: ContractState) -> bool:
        valid_transitions = {
            ContractState.PENDING: {ContractState.ACTIVE, ContractState.CANCELLED},
            ContractState.ACTIVE: {ContractState.COMPLETED, ContractState.DISPUTED},
            ContractState.DISPUTED: {ContractState.COMPLETED, ContractState.CANCELLED},
            ContractState.COMPLETED: set(),
            ContractState.CANCELLED: set()
        }
        
        return new_state in valid_transitions[self.contract.state]
        
    def update_state(self, new_state: ContractState, metadata: Dict[str, Any]) -> bool:
        if not self.validate_transition(new_state):
            return False
            
        self.contract.state = new_state
        self.events.append({
            "timestamp": datetime.now(),
            "type": "state_change",
            "old_state": self.contract.state.name,
            "new_state": new_state.name,
            "metadata": metadata
        })
        return True
        
    def process_payment(self, amount: float, metadata: Dict[str, Any]) -> bool:
        if amount != self.contract.payment_amount:
            return False
            
        self.contract.payment_status = "completed"
        self.events.append({
            "timestamp": datetime.now(),
            "type": "payment",
            "amount": amount,
            "metadata": metadata
        })
        return True
        
    def get_events(self) -> List[Dict[str, Any]]:
        return self.events
        
    def verify_completion(self) -> bool:
        return (
            self.contract.state == ContractState.COMPLETED and
            self.contract.payment_status == "completed" and
            (self.contract.end_time is None or
             datetime.now() >= self.contract.end_time)
        )