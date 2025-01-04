from typing import Dict, List, Any, Optional
from .contracts import ServiceContract, ContractState
from datetime import datetime
import json
import hashlib

class TransactionValidator:
    def __init__(self):
        self.required_fields = {
            "transaction": ["id", "timestamp", "type", "data"],
            "contract": ["contract_id", "provider_id", "consumer_id", "service_type", "terms"],
            "payment": ["amount", "sender", "recipient", "contract_id"]
        }
        
    def validate_transaction(self, transaction: Dict[str, Any]) -> bool:
        if not self._check_required_fields(transaction, self.required_fields["transaction"]):
            return False
            
        if not isinstance(transaction["timestamp"], (int, float)):
            return False
            
        if transaction["timestamp"] > datetime.now().timestamp():
            return False
            
        return True
        
    def validate_contract(self, contract: ServiceContract) -> bool:
        contract_dict = contract.to_dict()
        if not self._check_required_fields(contract_dict, self.required_fields["contract"]):
            return False
            
        if contract.start_time > datetime.now():
            return False
            
        if contract.end_time and contract.end_time <= contract.start_time:
            return False
            
        if contract.payment_amount < 0:
            return False
            
        return True
        
    def validate_payment(self, payment: Dict[str, Any]) -> bool:
        if not self._check_required_fields(payment, self.required_fields["payment"]):
            return False
            
        if payment["amount"] <= 0:
            return False
            
        if payment["sender"] == payment["recipient"]:
            return False
            
        return True
        
    def _check_required_fields(self, data: Dict[str, Any], required: List[str]) -> bool:
        return all(field in data for field in required)

class ChainValidator:
    def __init__(self, difficulty: int = 4):
        self.transaction_validator = TransactionValidator()
        self.difficulty = difficulty
        
    def validate_block(self, block: Dict[str, Any], previous_hash: str) -> bool:
        if not self._validate_block_structure(block):
            return False
            
        if block["previous_hash"] != previous_hash:
            return False
            
        if not self._validate_block_hash(block):
            return False
            
        for transaction in block["transactions"]:
            if not self.transaction_validator.validate_transaction(transaction):
                return False
                
        return True
        
    def validate_chain(self, chain: List[Dict[str, Any]]) -> bool:
        for i in range(1, len(chain)):
            current_block = chain[i]
            previous_block = chain[i-1]
            
            if not self.validate_block(current_block, previous_block["hash"]):
                return False
                
            if not self._validate_block_sequence(current_block, previous_block):
                return False
                
        return True
        
    def _validate_block_structure(self, block: Dict[str, Any]) -> bool:
        required_fields = ["index", "timestamp", "transactions", "previous_hash", "nonce", "hash"]
        return all(field in block for field in required_fields)
        
    def _validate_block_hash(self, block: Dict[str, Any]) -> bool:
        block_data = {
            "index": block["index"],
            "timestamp": block["timestamp"],
            "transactions": block["transactions"],
            "previous_hash": block["previous_hash"],
            "nonce": block["nonce"]
        }
        
        block_string = json.dumps(block_data, sort_keys=True)
        calculated_hash = hashlib.sha256(block_string.encode()).hexdigest()
        
        return (
            block["hash"] == calculated_hash and
            block["hash"].startswith("0" * self.difficulty)
        )
        
    def _validate_block_sequence(self, current: Dict[str, Any], previous: Dict[str, Any]) -> bool:
        if current["index"] != previous["index"] + 1:
            return False
            
        if current["timestamp"] <= previous["timestamp"]:
            return False
            
        return True

class StateValidator:
    def __init__(self):
        self.valid_state_transitions = {
            ContractState.PENDING: {ContractState.ACTIVE, ContractState.CANCELLED},
            ContractState.ACTIVE: {ContractState.COMPLETED, ContractState.DISPUTED},
            ContractState.DISPUTED: {ContractState.COMPLETED, ContractState.CANCELLED},
            ContractState.COMPLETED: set(),
            ContractState.CANCELLED: set()
        }
    
    def validate_state_transition(
        self,
        current_state: ContractState,
        new_state: ContractState
    ) -> bool:
        return new_state in self.valid_state_transitions[current_state]
        
    def validate_contract_state(self, contract: ServiceContract) -> bool:
        if contract.state == ContractState.COMPLETED:
            if not contract.end_time or datetime.now() < contract.end_time:
                return False
                
        if contract.state == ContractState.ACTIVE:
            if contract.end_time and datetime.now() > contract.end_time:
                return False
                
        return True