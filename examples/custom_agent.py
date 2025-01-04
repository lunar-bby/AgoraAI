from agoraai.agent import Agent
from agoraai.agent.capabilities import Capability, CapabilityType
from agoraai.marketplace import Marketplace
from agoraai.communication import MessageHandler, MessageBroker
from typing import Dict, Any, List
import asyncio
import numpy as np

class MLAgent(Agent):
    def __init__(self, name: str, model_type: str = "classifier"):
        capabilities = [
            "model_training",
            "prediction",
            "model_evaluation"
        ]
        super().__init__(name, "MLAgent", capabilities)
        self.model_type = model_type
        self.model_state = {}
        self.message_handler = None
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        operation = request.get("operation")
        
        if operation == "train":
            return await self._handle_training(request)
        elif operation == "predict":
            return await self._handle_prediction(request)
        elif operation == "evaluate":
            return await self._handle_evaluation(request)
        else:
            return {"status": "error", "message": "Unknown operation"}
    
    async def _handle_training(self, request: Dict[str, Any]) -> Dict[str, Any]:
        data = np.array(request.get("data", []))
        labels = np.array(request.get("labels", []))
        
        if len(data) == 0 or len(labels) == 0:
            return {"status": "error", "message": "No data provided"}
        
        # Simple example: calculate mean and std for each feature
        self.model_state["feature_means"] = data.mean(axis=0)
        self.model_state["feature_stds"] = data.std(axis=0)
        self.model_state["trained"] = True
        
        return {
            "status": "success",
            "message": "Model trained successfully",
            "metrics": {
                "samples": len(data),
                "features": data.shape[1],
                "classes": len(np.unique(labels))
            }
        }
    
    async def _handle_prediction(self, request: Dict[str, Any]) -> Dict[str, Any]:
        if not self.model_state.get("trained"):
            return {"status": "error", "message": "Model not trained"}
        
        data = np.array(request.get("data", []))
        if len(data) == 0:
            return {"status": "error", "message": "No data provided"}
        
        # Simple example: standardize data using trained means and stds
        standardized = (data - self.model_state["feature_means"]) / self.model_state["feature_stds"]
        
        return {
            "status": "success",
            "predictions": standardized.tolist()
        }
    
    async def _handle_evaluation(self, request: Dict[str, Any]) -> Dict[str, Any]:
        if not self.model_state.get("trained"):
            return {"status": "error", "message": "Model not trained"}
        
        data = np.array(request.get("data", []))
        true_labels = np.array(request.get("labels", []))
        
        if len(data) == 0 or len(true_labels) == 0:
            return {"status": "error", "message": "No data provided"}
        
        # Simple example: calculate basic metrics
        predictions = await self._handle_prediction({"data": data})
        
        return {
            "status": "success",
            "metrics": {
                "samples_evaluated": len(data),
                "prediction_mean": np.mean(predictions["predictions"]),
                "prediction_std": np.std(predictions["predictions"])
            }
        }

async def main():
    # Create ML agent
    ml_agent = MLAgent("MLAgent1")
    
    # Example training data
    training_data = np.random.randn(100, 4)
    training_labels = np.random.randint(0, 2, 100)
    
    # Train the model
    train_result = await ml_agent.handle_request({
        "operation": "train",
        "data": training_data.tolist(),
        "labels": training_labels.tolist()
    })
    print("Training result:", train_result)
    
    # Make predictions
    test_data = np.random.randn(10, 4)
    predict_result = await ml_agent.handle_request({
        "operation": "predict",
        "data": test_data.tolist()
    })
    print("Prediction result:", predict_result)
    
    # Evaluate model
    eval_result = await ml_agent.handle_request({
        "operation": "evaluate",
        "data": test_data.tolist(),
        "labels": np.random.randint(0, 2, 10).tolist()
    })
    print("Evaluation result:", eval_result)

if __name__ == "__main__":
    asyncio.run(main())