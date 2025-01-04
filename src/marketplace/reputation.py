from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import math

@dataclass
class Review:
    reviewer_id: str
    agent_id: str
    score: float
    timestamp: datetime
    transaction_id: str
    feedback: str

class ReputationSystem:
    def __init__(self):
        self.reviews: Dict[str, List[Review]] = {}
        self.weights = {
            "recent_activity": 0.4,
            "success_rate": 0.3,
            "review_score": 0.3
        }
        
    def add_review(self, review: Review) -> None:
        if review.agent_id not in self.reviews:
            self.reviews[review.agent_id] = []
        self.reviews[review.agent_id].append(review)
        
    def get_agent_reviews(self, agent_id: str) -> List[Review]:
        return self.reviews.get(agent_id, [])
        
    def calculate_reputation(
        self,
        agent_id: str,
        lookback_days: int = 30
    ) -> float:
        if agent_id not in self.reviews:
            return 0.0
            
        recent_reviews = self._get_recent_reviews(agent_id, lookback_days)
        if not recent_reviews:
            return 0.0
            
        recent_activity_score = self._calculate_recent_activity(recent_reviews)
        success_rate = self._calculate_success_rate(recent_reviews)
        review_score = self._calculate_review_score(recent_reviews)
        
        return (
            self.weights["recent_activity"] * recent_activity_score +
            self.weights["success_rate"] * success_rate +
            self.weights["review_score"] * review_score
        )
        
    def _get_recent_reviews(
        self,
        agent_id: str,
        lookback_days: int
    ) -> List[Review]:
        cutoff = datetime.now().timestamp() - (lookback_days * 24 * 3600)
        return [
            review for review in self.reviews[agent_id]
            if review.timestamp.timestamp() > cutoff
        ]
        
    def _calculate_recent_activity(self, reviews: List[Review]) -> float:
        if not reviews:
            return 0.0
            
        latest_review = max(reviews, key=lambda x: x.timestamp)
        days_since_latest = (
            datetime.now() - latest_review.timestamp
        ).total_seconds() / (24 * 3600)
        
        return math.exp(-0.1 * days_since_latest)
        
    def _calculate_success_rate(self, reviews: List[Review]) -> float:
        if not reviews:
            return 0.0
            
        successful_reviews = [
            review for review in reviews
            if review.score >= 3.0
        ]
        return len(successful_reviews) / len(reviews)
        
    def _calculate_review_score(self, reviews: List[Review]) -> float:
        if not reviews:
            return 0.0
            
        total_score = sum(review.score for review in reviews)
        weighted_score = total_score / len(reviews)
        
        return weighted_score / 5.0