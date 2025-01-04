from typing import Optional, Dict, Any
import logging
import logging.handlers
import json
import os
import time
from datetime import datetime
from pathlib import Path

class AgentLogger:
    def __init__(
        self,
        name: str,
        log_dir: str = "logs",
        max_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5
    ):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # File handler for all logs
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / f"{name}.log",
            maxBytes=max_size,
            backupCount=backup_count
        )
        file_handler.setLevel(logging.DEBUG)
        
        # File handler for errors only
        error_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / f"{name}_error.log",
            maxBytes=max_size,
            backupCount=backup_count
        )
        error_handler.setLevel(logging.ERROR)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        error_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console_handler)
        
        self.metrics: Dict[str, Any] = {
            "start_time": time.time(),
            "log_counts": {
                "debug": 0,
                "info": 0,
                "warning": 0,
                "error": 0,
                "critical": 0
            }
        }
    
    def debug(self, message: str, **kwargs) -> None:
        self.metrics["log_counts"]["debug"] += 1
        self.logger.debug(self._format_message(message, **kwargs))
        
    def info(self, message: str, **kwargs) -> None:
        self.metrics["log_counts"]["info"] += 1
        self.logger.info(self._format_message(message, **kwargs))
        
    def warning(self, message: str, **kwargs) -> None:
        self.metrics["log_counts"]["warning"] += 1
        self.logger.warning(self._format_message(message, **kwargs))
        
    def error(self, message: str, **kwargs) -> None:
        self.metrics["log_counts"]["error"] += 1
        self.logger.error(self._format_message(message, **kwargs))
        
    def critical(self, message: str, **kwargs) -> None:
        self.metrics["log_counts"]["critical"] += 1
        self.logger.critical(self._format_message(message, **kwargs))
        
    def _format_message(self, message: str, **kwargs) -> str:
        if kwargs:
            try:
                message_dict = {"message": message, "data": kwargs}
                return json.dumps(message_dict)
            except Exception:
                return f"{message} - {kwargs}"
        return message
        
    def get_metrics(self) -> Dict[str, Any]:
        uptime = time.time() - self.metrics["start_time"]
        return {
            "uptime": uptime,
            "log_counts": self.metrics["log_counts"],
            "logs_per_second": sum(self.metrics["log_counts"].values()) / uptime
        }
        
    def clear_metrics(self) -> None:
        self.metrics["start_time"] = time.time()
        for key in self.metrics["log_counts"]:
            self.metrics["log_counts"][key] = 0
            
    def export_logs(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        level: str = "DEBUG"
    ) -> str:
        export_path = self.log_dir / f"{self.name}_export_{int(time.time())}.log"
        
        with open(self.log_dir / f"{self.name}.log", 'r') as source:
            with open(export_path, 'w') as target:
                for line in source:
                    try:
                        log_time_str = line.split(' - ')[0].strip()
                        log_time = datetime.strptime(log_time_str, '%Y-%m-%d %H:%M:%S,%f')
                        
                        if start_time and log_time < start_time:
                            continue
                        if end_time and log_time > end_time:
                            continue
                            
                        log_level = line.split(' - ')[2].strip()
                        if getattr(logging, level) <= getattr(logging, log_level):
                            target.write(line)
                            
                    except (IndexError, ValueError):
                        continue
                        
        return str(export_path)
        
    def cleanup_old_logs(self, days: int = 30) -> None:
        cutoff_time = time.time() - (days * 24 * 3600)
        
        for log_file in self.log_dir.glob(f"{self.name}*.log"):
            if log_file.stat().st_mtime < cutoff_time:
                try:
                    log_file.unlink()
                except OSError as e:
                    self.error(f"Failed to delete old log file {log_file}: {e}")