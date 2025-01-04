from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum, auto

class CapabilityType(Enum):
    DATA_PROCESSING = auto()
    STORAGE = auto()
    ANALYSIS = auto()
    COMPUTE = auto()
    TRAINING = auto()

@dataclass
class Capability:
    type: CapabilityType
    name: str
    description: str
    parameters: Dict[str, Any]
    requirements: Dict[str, Any]

class CapabilityRegistry:
    def __init__(self):
        self.capabilities: Dict[str, Capability] = {}
        
    def register_capability(self, capability: Capability) -> None:
        self.capabilities[capability.name] = capability
        
    def get_capability(self, name: str) -> Capability:
        return self.capabilities.get(name)
        
    def list_capabilities(self) -> List[str]:
        return list(self.capabilities.keys())
        
    def get_capabilities_by_type(self, type: CapabilityType) -> List[Capability]:
        return [cap for cap in self.capabilities.values() if cap.type == type]

STANDARD_CAPABILITIES = {
    "data_processing": Capability(
        type=CapabilityType.DATA_PROCESSING,
        name="data_processing",
        description="Process and transform data",
        parameters={"format": str, "operations": List[str]},
        requirements={"cpu": "1", "memory": "512M"}
    ),
    "data_storage": Capability(
        type=CapabilityType.STORAGE,
        name="data_storage",
        description="Store and retrieve data",
        parameters={"format": str, "size": int},
        requirements={"storage": "1G"}
    ),
    "data_analysis": Capability(
        type=CapabilityType.ANALYSIS,
        name="data_analysis",
        description="Analyze data and generate insights",
        parameters={"type": str, "metrics": List[str]},
        requirements={"cpu": "2", "memory": "1G"}
    ),
    "model_training": Capability(
        type=CapabilityType.TRAINING,
        name="model_training",
        description="Train machine learning models",
        parameters={"model_type": str, "dataset_size": int},
        requirements={"gpu": "1", "memory": "2G"}
    ),
    "computation": Capability(
        type=CapabilityType.COMPUTE,
        name="computation",
        description="Perform complex computations",
        parameters={"type": str, "complexity": str},
        requirements={"cpu": "4", "memory": "2G"}
    )
}