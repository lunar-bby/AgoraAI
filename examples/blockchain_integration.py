from agoraai.blockchain import BlockchainManager, ServiceContract, ContractState
from agoraai.blockchain.contracts import SmartContract
from datetime import datetime, timedelta
import asyncio
import logging

async def simulate_contract_lifecycle():
    blockchain_manager = BlockchainManager(difficulty=2)
    
    # Create a service contract
    contract = ServiceContract(
        contract_id="contract_001",
        provider_id="provider_001",
        consumer_id="consumer_001",
        service_type="data_processing",
        terms={
            "max_time": 3600,
            "max_resources": {"cpu": 4, "memory": "8G"},
            "expected_output": "processed_data"
        },
        start_time=datetime.now(),
        end_time=datetime.now() + timedelta(hours=1),
        state=ContractState.PENDING,
        payment_amount=10.0,
        payment_status="pending"
    )
    
    # Create smart contract
    smart_contract = SmartContract(contract)
    
    # Record initial contract on blockchain
    tx_id = await blockchain_manager.record_transaction(contract)
    print(f"Contract recorded with transaction ID: {tx_id}")
    
    # Simulate contract activation
    await asyncio.sleep(1)
    smart_contract.update_state(
        ContractState.ACTIVE,
        {"activation_time": datetime.now().isoformat()}
    )
    await blockchain_manager.update_transaction(contract)
    
    # Simulate contract execution
    await asyncio.sleep(2)
    smart_contract.process_payment(
        amount=10.0,
        metadata={"payment_method": "tokens", "timestamp": datetime.now().isoformat()}
    )
    
    # Complete contract
    smart_contract.update_state(
        ContractState.COMPLETED,
        {"completion_time": datetime.now().isoformat()}
    )
    await blockchain_manager.update_transaction(contract)
    
    # Verify contract completion
    completion_verified = smart_contract.verify_completion()
    print(f"Contract completion verified: {completion_verified}")
    
    # Get contract history
    history = blockchain_manager.get_transaction_history(tx_id)
    print("\nContract History:")
    for entry in history:
        print(f"Block {entry['block_index']}: {entry['transaction']['data']['state']}")
    
    # Verify chain integrity
    chain_valid = blockchain_manager.is_chain_valid()
    print(f"\nBlockchain integrity: {chain_valid}")

async def simulate_blockchain_operations():
    blockchain_manager = BlockchainManager(difficulty=2)
    
    # Simulate multiple transactions
    for i in range(5):
        tx_data = {
            "type": "data_transfer",
            "from": f"agent_{i}",
            "to": f"agent_{i+1}",
            "amount": 1.0,
            "timestamp": datetime.now().isoformat()
        }
        await blockchain_manager.record_transaction(tx_data)
        await asyncio.sleep(1)
    
    # Mine pending transactions
    miner_address = "miner_001"
    block = await blockchain_manager.mine_block(miner_address)
    print(f"\nNew block mined: {block.hash}")
    print(f"Block transactions: {len(block.transactions)}")
    
    # Verify the chain
    print(f"Chain valid: {blockchain_manager.is_chain_valid()}")
    print(f"Chain length: {len(blockchain_manager.chain)}")

async def main():
    logging.basicConfig(level=logging.INFO)
    
    print("Simulating contract lifecycle...")
    await simulate_contract_lifecycle()
    
    print("\nSimulating blockchain operations...")
    await simulate_blockchain_operations()

if __name__ == "__main__":
    asyncio.run(main())