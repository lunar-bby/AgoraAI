import pytest
import os
import json
import logging
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from agoraai.utils.config import ConfigManager
from agoraai.utils.logging import AgentLogger
from agoraai.utils.serialization import Serializer, CompactSerializer

@pytest.fixture
def config_manager(tmp_path):
    config_file = tmp_path / "config.yaml"
    return ConfigManager(str(config_file))

@pytest.fixture
def agent_logger(tmp_path):
    log_dir = tmp_path / "logs"
    return AgentLogger("test_agent", str(log_dir))

@pytest.fixture
def serializer():
    return Serializer()

class TestConfigManager:
    def test_default_config(self, config_manager):
        assert config_manager.get("network.host") == "localhost"
        assert config_manager.get("network.port") == 8000
        assert config_manager.get("nonexistent", "default") == "default"
        
    def test_config_update(self, config_manager):
        config_manager.set("network.host", "127.0.0.1")
        assert config_manager.get("network.host") == "127.0.0.1"
        
    def test_config_save_load(self, config_manager):
        config_manager.set("test.key", "value")
        config_manager.save_config()
        
        new_config = ConfigManager(config_manager.config_path)
        assert new_config.get("test.key") == "value"
        
    def test_json_conversion(self, config_manager):
        json_str = config_manager.to_json()
        assert isinstance(json_str, str)
        
        config_dict = json.loads(json_str)
        assert "network" in config_dict
        
        config_manager.from_json('{"test": {"key": "value"}}')
        assert config_manager.get("test.key") == "value"
        
    def test_validation(self, config_manager):
        assert config_manager.validate_config() is True
        
        # Remove required section
        del config_manager.config["network"]
        assert config_manager.validate_config() is False

class TestAgentLogger:
    def test_log_creation(self, agent_logger, tmp_path):
        agent_logger.info("Test message")
        
        log_file = tmp_path / "logs" / "test_agent.log"
        assert log_file.exists()
        
        with open(log_file) as f:
            content = f.read()
            assert "Test message" in content
            
    def test_log_levels(self, agent_logger):
        agent_logger.debug("Debug message")
        agent_logger.info("Info message")
        agent_logger.warning("Warning message")
        agent_logger.error("Error message")
        agent_logger.critical("Critical message")
        
        metrics = agent_logger.get_metrics()
        assert metrics["log_counts"]["debug"] == 1
        assert metrics["log_counts"]["critical"] == 1
        
    def test_structured_logging(self, agent_logger):
        agent_logger.info(
            "Structured message",
            user="test_user",
            action="test_action"
        )
        
        metrics = agent_logger.get_metrics()
        assert metrics["log_counts"]["info"] == 1
        
    def test_log_export(self, agent_logger):
        agent_logger.info("Test message")
        
        export_path = agent_logger.export_logs(
            level="INFO"
        )
        assert os.path.exists(export_path)
        
        with open(export_path) as f:
            content = f.read()
            assert "Test message" in content
            
    def test_cleanup(self, agent_logger):
        agent_logger.info("Test message")
        agent_logger.cleanup_old_logs(days=0)
        
        metrics = agent_logger.get_metrics()
        agent_logger.clear_metrics()
        
        new_metrics = agent_logger.get_metrics()
        assert new_metrics["log_counts"]["info"] == 0

class TestSerialization:
    @dataclass
    class TestData:
        id: str
        value: int
        timestamp: datetime
        
    class TestEnum(Enum):
        VALUE1 = 1
        VALUE2 = 2
        
    def test_basic_serialization(self, serializer):
        data = {"test": "value", "number": 42}
        serialized = serializer.serialize(data, format="json")
        deserialized = serializer.deserialize(serialized, format="json")
        assert deserialized == data
        
    def test_dataclass_serialization(self, serializer):
        data = self.TestData(
            id="test",
            value=42,
            timestamp=datetime.now()
        )
        
        serialized = serializer.serialize(data)
        deserialized = serializer.deserialize(
            serialized,
            target_type=self.TestData
        )
        
        assert isinstance(deserialized, self.TestData)
        assert deserialized.id == data.id
        assert deserialized.value == data.value
        
    def test_enum_serialization(self, serializer):
        data = {"enum": self.TestEnum.VALUE1}
        serialized = serializer.serialize(data)
        deserialized = serializer.deserialize(serialized)
        assert deserialized["enum"] == self.TestEnum.VALUE1.name
        
    def test_compact_serialization(self):
        serializer = CompactSerializer()
        data = {"large": "data" * 1000}
        
        normal = serializer.serialize(data, compress=False)
        compressed = serializer.serialize(data, compress=True)
        
        assert len(compressed) < len(normal)
        
        decompressed = serializer.deserialize(
            compressed,
            compressed=True
        )
        assert decompressed == data
        
    def test_custom_type_handling(self, serializer):
        class CustomType:
            def __init__(self, value):
                self.value = value
                
        serializer.register_custom_type(
            CustomType,
            lambda x: x.value,
            lambda x: CustomType(x)
        )
        
        data = {"custom": CustomType(42)}
        serialized = serializer.serialize(data)
        deserialized = serializer.deserialize(serialized)
        
        assert deserialized["custom"] == 42