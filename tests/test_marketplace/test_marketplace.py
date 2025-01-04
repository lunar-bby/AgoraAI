import pytest
from datetime import datetime, timedelta
from agoraai.marketplace.core import Marketplace, Transaction
from agoraai.marketplace.matching import ServiceMatcher, ServiceRequest, ServiceOffer
from agoraai.marketplace.reputation import ReputationSystem, Review
from agoraai.agent import AgentRegistry
from agoraai.blockchain import BlockchainManager
from agoraai.agent.types import DataProcessingAgent, StorageAgent

@pytest.fixture
def agent_registry():
    return AgentRegistry()

@pytest.fixture
def blockchain_manager():
    return BlockchainManager(difficulty=2)

@pytest.fixture
def marketplace(agent_registry, blockchain_manager):
    return Marketplace(agent_registry, blockchain_manager)

@pytest.fixture
def data_agent():
    return DataProcessingAgent(
        name="DataProcessor1",
        capabilities=["data_processing"]
    )

@pytest.fixture
def storage_agent():
    return StorageAgent(
        name="Storage1",
        capabilities=["data_storage"]
    )

class TestMarketplace:
    @pytest.mark.asyncio
    async def test_request_service(self, marketplace, agent_registry, data_agent):
        agent_registry.register_agent(data_agent)
        
        transaction_id = await marketplace.request_service(
            requester_id="requester_1",
            service_type="data_processing",
            requirements={"data": [1, 2, 3]}
        )
        
        assert transaction_id is not None
        assert transaction_id in marketplace.active_transactions
        
    @pytest.mark.asyncio
    async def test_execute_transaction(self, marketplace, agent_registry, data_agent):
        agent_registry.register_agent(data_agent)
        
        transaction_id = await marketplace.request_service(
            requester_id="requester_1",
            service_type="data_processing",
            requirements={"data": [1, 2, 3]}
        )
        
        result = await marketplace.execute_transaction(transaction_id)
        assert result["status"] == "success"
        assert transaction_id not in marketplace.active_transactions
        assert len(marketplace.transaction_history) == 1
        
    @pytest.mark.asyncio
    async def test_nonexistent_service(self, marketplace):
        transaction_id = await marketplace.request_service(
            requester_id="requester_1",
            service_type="nonexistent_service",
            requirements={}
        )
        
        assert transaction_id is None
        
    def test_transaction_status(self, marketplace, agent_registry, data_agent):
        agent_registry.register_agent(data_agent)
        
        # Test active transaction
        transaction = Transaction(
            id="test_tx",
            requester_id="requester_1",
            provider_id=data_agent.id,
            service_type="data_processing",
            status="pending",
            created_at=datetime.now(),
            completed_at=None,
            amount=1.0,
            metadata={}
        )
        
        marketplace.active_transactions[transaction.id] = transaction
        assert marketplace.get_transaction_status(transaction.id) == "pending"
        
        # Test completed transaction
        transaction.status = "completed"
        transaction.completed_at = datetime.now()
        marketplace.transaction_history.append(transaction)
        assert marketplace.get_transaction_status(transaction.id) == "completed"

class TestServiceMatcher:
    @pytest.fixture
    def matcher(self):
        return ServiceMatcher()
        
    def test_add_request(self, matcher):
        request = ServiceRequest(
            requester_id="requester_1",
            service_type="data_processing",
            requirements={"cpu": 2},
            priority=1,
            max_price=10.0,
            deadline=datetime.now() + timedelta(hours=1)
        )
        matcher.add_request(request)
        assert len(matcher.pending_requests) == 1
        
    def test_add_offer(self, matcher):
        offer = ServiceOffer(
            provider_id="provider_1",
            service_type="data_processing",
            capabilities={"cpu": 4},
            price=5.0,
            availability=1.0
        )
        matcher.add_offer(offer)
        assert len(matcher.active_offers) == 1
        
    def test_find_match(self, matcher):
        request = ServiceRequest(
            requester_id="requester_1",
            service_type="data_processing",
            requirements={"cpu": 2},
            priority=1,
            max_price=10.0,
            deadline=datetime.now() + timedelta(hours=1)
        )
        
        offer = ServiceOffer(
            provider_id="provider_1",
            service_type="data_processing",
            capabilities={"cpu": 4},
            price=5.0,
            availability=1.0
        )
        
        matcher.add_request(request)
        matcher.add_offer(offer)
        
        match = matcher.find_match(request)
        assert match is not None
        assert match.provider_id == "provider_1"
        
    def test_find_matches(self, matcher):
        # Add multiple requests and offers
        for i in range(3):
            request = ServiceRequest(
                requester_id=f"requester_{i}",
                service_type="data_processing",
                requirements={"cpu": 2},
                priority=i,
                max_price=10.0,
                deadline=datetime.now() + timedelta(hours=1)
            )
            matcher.add_request(request)
            
            offer = ServiceOffer(
                provider_id=f"provider_{i}",
                service_type="data_processing",
                capabilities={"cpu": 4},
                price=5.0,
                availability=1.0
            )
            matcher.add_offer(offer)
            
        matches = matcher.find_matches(max_matches=2)
        assert len(matches) == 2
        # Check that matches are ordered by priority
        assert matches[0][0].priority > matches[1][0].priority

class TestReputationSystem:
    @pytest.fixture
    def reputation_system(self):
        return ReputationSystem()
        
    def test_add_review(self, reputation_system):
        review = Review(
            reviewer_id="reviewer_1",
            agent_id="agent_1",
            score=4.5,
            timestamp=datetime.now(),
            transaction_id="tx_1",
            feedback="Good service"
        )
        
        reputation_system.add_review(review)
        assert len(reputation_system.reviews["agent_1"]) == 1
        
    def test_calculate_reputation(self, reputation_system):
        # Add multiple reviews
        for i in range(3):
            review = Review(
                reviewer_id=f"reviewer_{i}",
                agent_id="agent_1",
                score=4.0,  # Consistent score
                timestamp=datetime.now(),
                transaction_id=f"tx_{i}",
                feedback="Good service"
            )
            reputation_system.add_review(review)
            
        reputation = reputation_system.calculate_reputation("agent_1")
        assert 0 <= reputation <= 1.0  # Reputation should be normalized
        
    def test_no_reviews(self, reputation_system):
        reputation = reputation_system.calculate_reputation("nonexistent_agent")
        assert reputation == 0.0