from typing import Dict, List, Optional, Set, Any
from ..agent.base import Agent
from ..agent.capabilities import Capability
import asyncio
from datetime import datetime

class ServiceDiscovery:
    def __init__(self):
        self.services: Dict[str, Set[str]] = {}
        self.capabilities: Dict[str, List[Capability]] = {}
        self.agent_info: Dict[str, Dict[str, Any]] = {}
        self._update_interval = 60
        asyncio.create_task(self._periodic_cleanup())
        
    def register_service(
        self,
        agent_id: str,
        service_types: List[str],
        capabilities: List[Capability]
    ) -> None:
        for service_type in service_types:
            if service_type not in self.services:
                self.services[service_type] = set()
            self.services[service_type].add(agent_id)
            
        self.capabilities[agent_id] = capabilities
        self.agent_info[agent_id] = {
            "last_seen": datetime.now(),
            "service_types": service_types
        }
        
    def unregister_service(self, agent_id: str) -> None:
        if agent_id in self.agent_info:
            service_types = self.agent_info[agent_id]["service_types"]
            for service_type in service_types:
                if service_type in self.services:
                    self.services[service_type].discard(agent_id)
                    
            self.capabilities.pop(agent_id, None)
            self.agent_info.pop(agent_id, None)
            
    def discover_services(
        self,
        service_type: str,
        required_capabilities: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        if service_type not in self.services:
            return []
            
        matching_agents = list(self.services[service_type])
        
        if required_capabilities:
            matching_agents = [
                agent_id for agent_id in matching_agents
                if self._has_required_capabilities(agent_id, required_capabilities)
            ]
            
        if filters:
            matching_agents = [
                agent_id for agent_id in matching_agents
                if self._matches_filters(agent_id, filters)
            ]
            
        return matching_agents
        
    def get_service_types(self) -> List[str]:
        return list(self.services.keys())
        
    def get_agent_capabilities(self, agent_id: str) -> List[Capability]:
        return self.capabilities.get(agent_id, [])
        
    def update_last_seen(self, agent_id: str) -> None:
        if agent_id in self.agent_info:
            self.agent_info[agent_id]["last_seen"] = datetime.now()
            
    def _has_required_capabilities(
        self,
        agent_id: str,
        required_capabilities: List[str]
    ) -> bool:
        agent_capabilities = {cap.name for cap in self.capabilities.get(agent_id, [])}
        return all(cap in agent_capabilities for cap in required_capabilities)
        
    def _matches_filters(
        self,
        agent_id: str,
        filters: Dict[str, Any]
    ) -> bool:
        if agent_id not in self.agent_info:
            return False
            
        agent_data = self.agent_info[agent_id]
        return all(
            key in agent_data and agent_data[key] == value
            for key, value in filters.items()
        )
        
    async def _periodic_cleanup(self) -> None:
        while True:
            await asyncio.sleep(self._update_interval)
            current_time = datetime.now()
            
            inactive_agents = [
                agent_id for agent_id, info in self.agent_info.items()
                if (current_time - info["last_seen"]).total_seconds() > self._update_interval * 2
            ]
            
            for agent_id in inactive_agents:
                self.unregister_service(agent_id)