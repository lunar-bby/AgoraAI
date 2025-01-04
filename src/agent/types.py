from typing import Dict, List, Any
from .base import Agent

class DataProcessingAgent(Agent):
    def __init__(self, name: str, capabilities: List[str]):
        super().__init__(name, "DataProcessing", capabilities)
        
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        return await self.execute_task(request)
        
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        data = task.get("data", [])
        operation = task.get("operation", "process")
        return {"status": "success", "result": data}

class StorageAgent(Agent):
    def __init__(self, name: str, capabilities: List[str]):
        super().__init__(name, "Storage", capabilities)
        self.storage: Dict[str, Any] = {}
        
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        return await self.execute_task(request)
        
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        operation = task.get("operation")
        key = task.get("key")
        value = task.get("value")
        
        if operation == "store":
            self.storage[key] = value
            return {"status": "success", "operation": "store"}
        elif operation == "retrieve":
            return {"status": "success", "value": self.storage.get(key)}
        
        return {"status": "error", "message": "Invalid operation"}

class AnalysisAgent(Agent):
    def __init__(self, name: str, capabilities: List[str]):
        super().__init__(name, "Analysis", capabilities)
        
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        return await self.execute_task(request)
        
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        data = task.get("data", [])
        analysis_type = task.get("analysis_type", "basic")
        return {"status": "success", "result": data}

class ComputeAgent(Agent):
    def __init__(self, name: str, capabilities: List[str]):
        super().__init__(name, "Compute", capabilities)
        
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        return await self.execute_task(request)
        
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        operation = task.get("operation", "compute")
        data = task.get("data", [])
        return {"status": "success", "result": data}

class TrainingAgent(Agent):
    def __init__(self, name: str, capabilities: List[str]):
        super().__init__(name, "Training", capabilities)
        self.model_state = {}
        
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        return await self.execute_task(request)
        
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        data = task.get("data", [])
        model_type = task.get("model_type", "default")
        return {"status": "success", "result": data}