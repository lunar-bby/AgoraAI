from typing import Dict, Any, Optional
import yaml
import os
import logging
from pathlib import Path
import json

class ConfigManager:
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config.yaml"
        self.config: Dict[str, Any] = {
            "network": {
                "host": "localhost",
                "port": 8000,
                "protocol": "http",
                "max_connections": 100,
                "timeout": 30
            },
            "security": {
                "secret_key": os.urandom(32).hex(),
                "token_expiry": 86400,
                "min_password_length": 8,
                "max_login_attempts": 5,
                "lockout_duration": 300
            },
            "blockchain": {
                "difficulty": 4,
                "block_time": 10,
                "reward": 1.0,
                "min_transactions": 1,
                "max_transactions": 1000
            },
            "marketplace": {
                "min_reputation": 0.0,
                "transaction_fee": 0.001,
                "update_interval": 60,
                "min_stake": 100,
                "dispute_window": 7200
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "agoraai.log",
                "max_size": 10485760,  # 10MB
                "backup_count": 5
            }
        }
        
        self.load_config()
        
    def load_config(self) -> None:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    user_config = yaml.safe_load(f)
                    self._update_recursive(self.config, user_config)
            except Exception as e:
                logging.error(f"Error loading config file: {str(e)}")
                
        self._setup_logging()
        
    def save_config(self) -> None:
        try:
            config_dir = os.path.dirname(self.config_path)
            if config_dir:
                os.makedirs(config_dir, exist_ok=True)
                
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
        except Exception as e:
            logging.error(f"Error saving config file: {str(e)}")
            
    def get(self, key: str, default: Any = None) -> Any:
        parts = key.split('.')
        value = self.config
        try:
            for part in parts:
                value = value[part]
            return value
        except (KeyError, TypeError):
            return default
            
    def set(self, key: str, value: Any) -> None:
        parts = key.split('.')
        config = self.config
        
        for part in parts[:-1]:
            if part not in config:
                config[part] = {}
            config = config[part]
            
        config[parts[-1]] = value
        self.save_config()
        
    def _update_recursive(self, base: Dict[str, Any], update: Dict[str, Any]) -> None:
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._update_recursive(base[key], value)
            else:
                base[key] = value
                
    def _setup_logging(self) -> None:
        logging_config = self.config["logging"]
        logging.basicConfig(
            level=getattr(logging, logging_config["level"]),
            format=logging_config["format"],
            handlers=[
                logging.FileHandler(logging_config["file"]),
                logging.StreamHandler()
            ]
        )
        
    def to_json(self) -> str:
        return json.dumps(self.config, indent=2)
        
    def from_json(self, json_str: str) -> None:
        try:
            new_config = json.loads(json_str)
            self._update_recursive(self.config, new_config)
            self.save_config()
        except json.JSONDecodeError as e:
            logging.error(f"Error parsing JSON config: {str(e)}")
            
    def get_section(self, section: str) -> Dict[str, Any]:
        return self.config.get(section, {})
        
    def validate_config(self) -> bool:
        required_sections = ["network", "security", "blockchain", "marketplace", "logging"]
        return all(section in self.config for section in required_sections)