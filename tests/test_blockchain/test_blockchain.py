import pytest
from datetime import datetime, timedelta
from agoraai.blockchain.core import BlockchainManager, Block
from agoraai.blockchain.contracts import ServiceContract, SmartContract, ContractState
from agoraai.blockchain.validation import TransactionValidator, ChainValidator, StateValidator

@pytest.fixture
def blockchain_manager():
    return BlockchainManager(difficulty=2)

@pytest.fixture
def service_contract():
    return ServiceContract(
        contract_id="contract_001",
        provider_id="provider_001",
        consumer_id="consumer_001",
        service_type="data_processing",
        terms={"cpu": 2, "memory": "4G"},
        start_time=datetime.now(),
        end_time=None,
        state=ContractState.PENDING,
        payment_amount=10.0,
        payment_status="pending"
    )

@pytest.fixture
def validator():
    return TransactionValidator()

@pytest.fixture
def chain_validator():
    return ChainValidator(difficulty=2)

class TestBlockchainManager:
    @pytest.mark.asyncio
    async def test_create_genesis_block(self, blockchain_manager):
        assert len(blockchain_manager.chain) == 1
        genesis_block = blockchain_manager.chain[0]
        assert genesis_block.index == 0
        assert genesis_block.previous_hash == "0"
        
    @pytest.mark.asyncio
    async def test_add_transaction(self, blockchain_manager):
        transaction = {
            "sender": "agent1",
            "receiver": "agent2",
            "amount": 10
        }
        tx_id = await blockchain_manager.record_transaction(transaction)
        assert tx_id is not None
        assert len(blockchain_manager.pending_transactions) == 1
        
    @pytest.mark.asyncio
    async def test_mine_block(self, blockchain_manager):
        # Add some transactions
        for i in range(3):
            await blockchain_manager.record_transaction({
                "sender": f"agent{i}",
                "receiver": f"agent{i+1}",
                "amount": 10
            })
            
        initial_chain_length = len(blockchain_manager.chain)
        block = await blockchain_manager.mine_block("miner1")
        
        assert block is not None
        assert len(blockchain_manager.chain) == initial_chain_length + 1
        assert block.hash.startswith("0" * blockchain_manager.difficulty)
        
    def test_chain_validity(self, blockchain_manager):
        assert blockchain_manager.is_chain_valid()
        
    @pytest.mark.asyncio
    async def test_get_transaction_history(self, blockchain_manager):
        tx_id = await blockchain_manager.record_transaction({
            "sender": "agent1",
            "receiver": "agent2",
            "amount": 10
        })
        await blockchain_manager.mine_block("miner1")
        
        history = blockchain_manager.get_transaction_history(tx_id)
        assert len(history) == 1
        assert history[0]["transaction"]["id"] == tx_id

class TestSmartContract:
    def test_contract_initialization(self, service_contract):
        contract = SmartContract(service_contract)
        assert contract.contract.state == ContractState.PENDING
        
    def test_valid_state_transition(self, service_contract):
        contract = SmartContract(service_contract)
        assert contract.validate_transition(ContractState.ACTIVE)
        assert not contract.validate_transition(ContractState.COMPLETED)
        
    def test_update_state(self, service_contract):
        contract = SmartContract(service_contract)
        result = contract.update_state(
            ContractState.ACTIVE,
            {"activation_time": datetime.now().isoformat()}
        )
        assert result is True
        assert contract.contract.state == ContractState.ACTIVE
        assert len(contract.events) == 1
        
    def test_process_payment(self, service_contract):
        contract = SmartContract(service_contract)
        result = contract.process_payment(
            10.0,
            {"payment_method": "tokens"}
        )
        assert result is True
        assert contract.contract.payment_status == "completed"
        assert len(contract.events) == 1
        
    def test_verify_completion(self, service_contract):
        contract = SmartContract(service_contract)
        contract.update_state(ContractState.ACTIVE, {})
        contract.process_payment(10.0, {})
        contract.update_state(ContractState.COMPLETED, {})
        assert contract.verify_completion() is True

class TestValidation:
    def test_transaction_validation(self, validator):
        valid_tx = {
            "id": "tx1",
            "timestamp": datetime.now().timestamp(),
            "type": "transfer",
            "data": {"amount": 10}
        }
        assert validator.validate_transaction(valid_tx) is True
        
        invalid_tx = {
            "timestamp": "invalid",
            "data": {"amount": 10}
        }
        assert validator.validate_transaction(invalid_tx) is False
        
    def test_contract_validation(self, validator, service_contract):
        assert validator.validate_contract(service_contract) is True
        
        # Test invalid contract
        service_contract.payment_amount = -10
        assert validator.validate_contract(service_contract) is False
        
    def test_payment_validation(self, validator):
        valid_payment = {
            "amount": 10.0,
            "sender": "agent1",
            "recipient": "agent2",
            "contract_id": "contract1"
        }
        assert validator.validate_payment(valid_payment) is True
        
        invalid_payment = {
            "amount": -10.0,
            "sender": "agent1",
            "recipient": "agent1",
            "contract_id": "contract1"
        }
        assert validator.validate_payment(invalid_payment) is False
        
    def test_chain_validation(self, chain_validator, blockchain_manager):
        # Create a valid chain
        chain = blockchain_manager.chain
        assert chain_validator.validate_chain(chain) is True
        
        # Tamper with a block
        chain[0].transactions.append({"invalid": "transaction"})
        assert chain_validator.validate_chain(chain) is False