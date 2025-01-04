
from typing import Dict, List, Optional, Any
from ..agent.base import Agent
from dataclasses import dataclass
from datetime import datetime
import asyncio

@dataclass
class ServiceRequest:
    requester_id: str
    service_type: str
    requirements: Dict[str, Any]
    priority: int
    max_price: float
    deadline: Optional[datetime]

@dataclass
class ServiceOffer:
    provider_id: str
    service_type: str
    capabilities: Dict[str, Any]
    price: float
    availability: float

class ServiceMatcher:
    def __init__(self):
        self.pending_requests: List[ServiceRequest] = []
        self.active_offers: List[ServiceOffer] = []
        
    def add_request(self, request: ServiceRequest) -> None:
        self.pending_requests.append(request)
        self._sort_requests()
        
    def add_offer(self, offer: ServiceOffer) -> None:
        self.active_offers.append(offer)
        
    def remove_request(self, requester_id: str) -> None:
        self.pending_requests = [
            req for req in self.pending_requests
            if req.requester_id != requester_id
        ]
        
    def remove_offer(self, provider_id: str) -> None:
        self.active_offers = [
            offer for offer in self.active_offers
            if offer.provider_id != provider_id
        ]
        
    def find_match(
        self,
        request: ServiceRequest
    ) -> Optional[ServiceOffer]:
        matching_offers = [
            offer for offer in self.active_offers
            if self._is_compatible(request, offer)
        ]
        
        if not matching_offers:
            return None
            
        return min(matching_offers, key=lambda x: x.price)
        
    def find_matches(
        self,
        max_matches: int = 10
    ) -> List[tuple[ServiceRequest, ServiceOffer]]:
        matches = []
        processed_requests = set()
        
        for request in self.pending_requests:
            if len(matches) >= max_matches:
                break
                
            if request.requester_id in processed_requests:
                continue
                
            offer = self.find_match(request)
            if offer:
                matches.append((request, offer))
                processed_requests.add(request.requester_id)
                
        return matches
        
    def _is_compatible(
        self,
        request: ServiceRequest,
        offer: ServiceOffer
    ) -> bool:
        if request.service_type != offer.service_type:
            return False
            
        if offer.price > request.max_price:
            return False
            
        if request.deadline and datetime.now() > request.deadline:
            return False
            
        for req_key, req_value in request.requirements.items():
            if req_key not in offer.capabilities:
                return False
            if offer.capabilities[req_key] < req_value:
                return False
                
        return True
        
    def _sort_requests(self) -> None:
        self.pending_requests.sort(key=lambda x: (-x.priority, x.deadline or datetime.max))