import pytest
from datetime import datetime
from agoraai.agent.base import Agent, AgentMetadata
from agoraai.agent.types import (
    DataProcessingAgent,
    StorageAgent,
    AnalysisAgent,
    ComputeAgent,
    TrainingAgent
)

@pytest.fixture
def basic_agent():
    return Agent(
        name="TestAgent",
        agent_type="test",
        capabilities=["test_capability"]
    )

@pytest.fixture
def data_processing_agent():
    return DataProcessingAgent(
        name="DataProcessor",
        capabilities=["data_processing", "transformation"]
    )

@pytest.fixture
def storage_agent():
    return StorageAgent(
        name="StorageAgent",
        capabilities=["data_storage", "data_retrieval"]
    )

class TestAgent:
    async def test_agent_initialization(self, basic_agent):
        assert basic_agent.name == "TestAgent"
        assert basic_agent.agent_type == "test"
        assert "test_capability" in basic_agent.capabilities
        assert isinstance(basic_agent.metadata, AgentMetadata)
        
    async def test_agent_state_update(self, basic_agent):
        new_state = {"status": "active", "load": 0.5}
        await basic_agent.update_state(new_state)
        assert basic_agent.state == new_state
        assert isinstance(basic_agent.metadata.last_active, datetime)
        
    async def test_agent_reputation_update(self, basic_agent):
        initial_score = basic_agent.metadata.reputation_score
        basic_agent.update_reputation(1.0)
        assert basic_agent.metadata.reputation_score > initial_score
        assert basic_agent.metadata.total_transactions == 1
        
    @pytest.mark.asyncio
    async def test_handle_request_not_implemented(self, basic_agent):
        with pytest.raises(NotImplementedError):
            await basic_agent.handle_request({"test": "data"})
            
    @pytest.mark.asyncio
    async def test_execute_task_not_implemented(self, basic_agent):
        with pytest.raises(NotImplementedError):
            await basic_agent.execute_task({"test": "task"})

class TestDataProcessingAgent:
    @pytest.mark.asyncio
    async def test_handle_request(self, data_processing_agent):
        request = {
            "data": [1, 2, 3],
            "operation": "process"
        }
        response = await data_processing_agent.handle_request(request)
        assert response["status"] == "success"
        assert "result" in response
        
    @pytest.mark.asyncio
    async def test_execute_task(self, data_processing_agent):
        task = {
            "data": [1, 2, 3],
            "operation": "process"
        }
        response = await data_processing_agent.execute_task(task)
        assert response["status"] == "success"
        assert "result" in response
        assert response["result"] == [1, 2, 3]  # Basic processing just returns data
        
    @pytest.mark.asyncio
    async def test_invalid_request(self, data_processing_agent):
        request = {
            "invalid": "data"
        }
        response = await data_processing_agent.handle_request(request)
        assert response["status"] == "success"  # Default behavior returns success

class TestStorageAgent:
    @pytest.mark.asyncio
    async def test_store_data(self, storage_agent):
        request = {
            "operation": "store",
            "key": "test_key",
            "value": "test_value"
        }
        response = await storage_agent.handle_request(request)
        assert response["status"] == "success"
        assert response["operation"] == "store"
        
    @pytest.mark.asyncio
    async def test_retrieve_data(self, storage_agent):
        # First store some data
        store_request = {
            "operation": "store",
            "key": "test_key",
            "value": "test_value"
        }
        await storage_agent.handle_request(store_request)
        
        # Then retrieve it
        retrieve_request = {
            "operation": "retrieve",
            "key": "test_key"
        }
        response = await storage_agent.handle_request(retrieve_request)
        assert response["status"] == "success"
        assert response["value"] == "test_value"
        
    @pytest.mark.asyncio
    async def test_retrieve_nonexistent_data(self, storage_agent):
        request = {
            "operation": "retrieve",
            "key": "nonexistent_key"
        }
        response = await storage_agent.handle_request(request)
        assert response["status"] == "success"
        assert response["value"] is None
        
    @pytest.mark.asyncio
    async def test_invalid_operation(self, storage_agent):
        request = {
            "operation": "invalid_op",
            "key": "test_key"
        }
        response = await storage_agent.handle_request(request)
        assert response["status"] == "error"
        assert "message" in response

class TestAgentMetadata:
    def test_metadata_initialization(self):
        metadata = AgentMetadata()
        assert metadata.reputation_score == 0.0
        assert metadata.total_transactions == 0
        assert metadata.successful_transactions == 0
        assert isinstance(metadata.created_at, datetime)
        assert isinstance(metadata.last_active, datetime)
        
    def test_metadata_update(self):
        metadata = AgentMetadata()
        initial_time = metadata.last_active
        metadata.last_active = datetime.now()
        assert metadata.last_active > initial_time