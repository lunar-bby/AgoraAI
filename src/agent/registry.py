from typing import Dict, List, Optional, Type
from .base import Agent
from .capabilities import Capability
import asyncio
from datetime import datetime, timedelta

class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, Agent] = {}
        self._capabilities: Dict[str, List[str]] = {}
        self._heartbeat_interval = 30
        asyncio.create_task(self._heartbeat_monitor())
        
    def register_agent(self, agent: Agent) -> None:
        self._agents[agent.id] = agent
        for cap in agent.get_capabilities():
            if cap not in self._capabilities:
                self._capabilities[cap] = []
            self._capabilities[cap].append(agent.id)
            
    def unregister_agent(self, agent_id: str) -> None:
        if agent_id in self._agents:
            agent = self._agents[agent_id]
            for cap in agent.get_capabilities():
                if cap in self._capabilities:
                    self._capabilities[cap].remove(agent_id)
            del self._agents[agent_id]
            
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        return self._agents.get(agent_id)
        
    def get_agents_by_capability(self, capability: str) -> List[Agent]:
        agent_ids = self._capabilities.get(capability, [])
        return [self._agents[aid] for aid in agent_ids if aid in self._agents]
        
    def get_all_agents(self) -> List[Agent]:
        return list(self._agents.values())
        
    def update_agent_status(self, agent_id: str) -> None:
        if agent_id in self._agents:
            self._agents[agent_id].metadata.last_active = datetime.now()
            
    async def _heartbeat_monitor(self) -> None:
        while True:
            await asyncio.sleep(self._heartbeat_interval)
            current_time = datetime.now()
            timeout = timedelta(seconds=self._heartbeat_interval * 2)
            
            inactive_agents = [
                agent_id for agent_id, agent in self._agents.items()
                if current_time - agent.metadata.last_active > timeout
            ]
            
            for agent_id in inactive_agents:
                self.unregister_agent(agent_id)

class AgentFactory:
    def __init__(self):
        self._agent_types: Dict[str, Type[Agent]] = {}
        
    def register_agent_type(self, name: str, agent_class: Type[Agent]) -> None:
        self._agent_types[name] = agent_class
        
    def create_agent(self, agent_type: str, name: str, capabilities: List[str]) -> Agent:
        if agent_type not in self._agent_types:
            raise ValueError(f"Unknown agent type: {agent_type}")
        return self._agent_types[agent_type](name, capabilities)