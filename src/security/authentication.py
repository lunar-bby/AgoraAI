from typing import Dict, Optional, Any
import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from dataclasses import dataclass

@dataclass
class AgentCredentials:
    agent_id: str
    public_key: str
    private_key: str
    access_token: Optional[str] = None
    token_expiry: Optional[datetime] = None

class AuthenticationManager:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.credentials: Dict[str, AgentCredentials] = {}
        self.token_validity = timedelta(hours=24)
        self.blacklisted_tokens: set = set()
    
    def register_agent(self, agent_id: str) -> AgentCredentials:
        private_key = secrets.token_hex(32)
        public_key = hashlib.sha256(private_key.encode()).hexdigest()
        
        credentials = AgentCredentials(
            agent_id=agent_id,
            public_key=public_key,
            private_key=private_key
        )
        
        self.credentials[agent_id] = credentials
        return credentials
    
    def authenticate_agent(
        self,
        agent_id: str,
        private_key: str
    ) -> Optional[str]:
        if agent_id not in self.credentials:
            return None
            
        credentials = self.credentials[agent_id]
        if credentials.private_key != private_key:
            return None
            
        return self.generate_token(agent_id)
    
    def generate_token(self, agent_id: str) -> str:
        expiry = datetime.now() + self.token_validity
        token_data = {
            "agent_id": agent_id,
            "exp": expiry.timestamp(),
            "iat": datetime.now().timestamp()
        }
        
        token = jwt.encode(
            token_data,
            self.secret_key,
            algorithm="HS256"
        )
        
        self.credentials[agent_id].access_token = token
        self.credentials[agent_id].token_expiry = expiry
        
        return token
    
    def validate_token(self, token: str) -> Optional[str]:
        if token in self.blacklisted_tokens:
            return None
            
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=["HS256"]
            )
            
            agent_id = payload.get("agent_id")
            if not agent_id or agent_id not in self.credentials:
                return None
                
            credentials = self.credentials[agent_id]
            if (not credentials.access_token or 
                credentials.access_token != token or
                datetime.now() > credentials.token_expiry):
                return None
                
            return agent_id
            
        except jwt.InvalidTokenError:
            return None
    
    def revoke_token(self, token: str) -> None:
        self.blacklisted_tokens.add(token)
        
        for credentials in self.credentials.values():
            if credentials.access_token == token:
                credentials.access_token = None
                credentials.token_expiry = None
    
    def rotate_keys(self, agent_id: str) -> Optional[AgentCredentials]:
        if agent_id not in self.credentials:
            return None
            
        new_private_key = secrets.token_hex(32)
        new_public_key = hashlib.sha256(new_private_key.encode()).hexdigest()
        
        credentials = self.credentials[agent_id]
        old_token = credentials.access_token
        
        if old_token:
            self.revoke_token(old_token)
        
        credentials.private_key = new_private_key
        credentials.public_key = new_public_key
        credentials.access_token = None
        credentials.token_expiry = None
        
        return credentials
    
    def cleanup_expired_tokens(self) -> None:
        current_time = datetime.now()
        for credentials in self.credentials.values():
            if (credentials.token_expiry and 
                current_time > credentials.token_expiry):
                if credentials.access_token:
                    self.revoke_token(credentials.access_token)

class SessionManager:
    def __init__(self, auth_manager: AuthenticationManager):
        self.auth_manager = auth_manager
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.session_timeout = timedelta(hours=1)
    
    def create_session(self, agent_id: str) -> Optional[str]:
        if not self.auth_manager.credentials.get(agent_id):
            return None
            
        session_id = secrets.token_urlsafe(32)
        self.active_sessions[session_id] = {
            "agent_id": agent_id,
            "created_at": datetime.now(),
            "last_accessed": datetime.now(),
            "metadata": {}
        }
        
        return session_id
    
    def validate_session(self, session_id: str) -> bool:
        if session_id not in self.active_sessions:
            return False
            
        session = self.active_sessions[session_id]
        current_time = datetime.now()
        
        if current_time - session["last_accessed"] > self.session_timeout:
            self.end_session(session_id)
            return False
            
        session["last_accessed"] = current_time
        return True
    
    def end_session(self, session_id: str) -> None:
        self.active_sessions.pop(session_id, None)
    
    def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        if not self.validate_session(session_id):
            return None
        return self.active_sessions[session_id].copy()
    
    def update_session_metadata(
        self,
        session_id: str,
        metadata: Dict[str, Any]
    ) -> bool:
        if not self.validate_session(session_id):
            return False
            
        self.active_sessions[session_id]["metadata"].update(metadata)
        return True
    
    def cleanup_expired_sessions(self) -> None:
        current_time = datetime.now()
        expired_sessions = [
            session_id for session_id, session in self.active_sessions.items()
            if current_time - session["last_accessed"] > self.session_timeout
        ]
        
        for session_id in expired_sessions:
            self.end_session(session_id)