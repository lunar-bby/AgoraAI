import asyncio
from agoraai.agent import AgentRegistry, Agent, AgentFactory
from agoraai.agent.types import DataProcessingAgent, StorageAgent
from agoraai.marketplace import Marketplace
from agoraai.blockchain import BlockchainManager
from agoraai.communication import MessageBroker
import logging

async def main():
    # Initialize core components
    agent_registry = AgentRegistry()
    blockchain_manager = BlockchainManager(difficulty=4)
    message_broker = MessageBroker()
    marketplace = Marketplace(agent_registry, blockchain_manager)

    # Create and register agents
    data_agent = DataProcessingAgent(
        name="DataProcessor1",
        capabilities=["data_processing", "data_transformation"]
    )
    storage_agent = StorageAgent(
        name="Storage1",
        capabilities=["data_storage", "data_retrieval"]
    )

    agent_registry.register_agent(data_agent)
    agent_registry.register_agent(storage_agent)

    # Simulate a service request
    transaction_id = await marketplace.request_service(
        requester_id=storage_agent.id,
        service_type="data_processing",
        requirements={
            "operation": "process",
            "data": [1, 2, 3, 4, 5],
            "transform": "normalize"
        }
    )

    if transaction_id:
        # Execute the transaction
        result = await marketplace.execute_transaction(transaction_id)
        print(f"Transaction result: {result}")

        # Get transaction status
        status = marketplace.get_transaction_status(transaction_id)
        print(f"Transaction status: {status}")

        # Get agent transactions
        data_agent_txs = marketplace.get_agent_transactions(data_agent.id)
        print(f"Data agent transactions: {len(data_agent_txs)}")

    # Cleanup
    agent_registry.unregister_agent(data_agent.id)
    agent_registry.unregister_agent(storage_agent.id)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())