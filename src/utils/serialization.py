from typing import Any, Dict, Optional, Type, TypeVar, Union
import json
import pickle
import base64
from datetime import datetime
import uuid
from dataclasses import asdict, is_dataclass, fields
from enum import Enum

T = TypeVar('T')

class SerializationError(Exception):
    pass

class Serializer:
    def __init__(self):
        self.serializers = {
            "json": self.json_serializer,
            "pickle": self.pickle_serializer,
            "base64": self.base64_serializer
        }
        
        self.custom_type_handlers = {
            datetime: self._serialize_datetime,
            uuid.UUID: str,
            Enum: lambda x: x.name
        }
        
    def serialize(
        self,
        data: Any,
        format: str = "json",
        **kwargs
    ) -> bytes:
        if format not in self.serializers:
            raise SerializationError(f"Unsupported format: {format}")
            
        try:
            return self.serializers[format](data, **kwargs)
        except Exception as e:
            raise SerializationError(f"Serialization failed: {str(e)}")
            
    def deserialize(
        self,
        data: bytes,
        format: str = "json",
        target_type: Optional[Type[T]] = None,
        **kwargs
    ) -> Any:
        if format not in self.serializers:
            raise SerializationError(f"Unsupported format: {format}")
            
        try:
            result = self._deserialize_data(data, format, **kwargs)
            if target_type:
                return self._convert_to_type(result, target_type)
            return result
        except Exception as e:
            raise SerializationError(f"Deserialization failed: {str(e)}")
            
    def json_serializer(self, data: Any, **kwargs) -> bytes:
        return json.dumps(
            self._prepare_for_serialization(data),
            default=self._handle_custom_types,
            **kwargs
        ).encode()
        
    def pickle_serializer(self, data: Any, **kwargs) -> bytes:
        return pickle.dumps(data, **kwargs)
        
    def base64_serializer(self, data: Any, **kwargs) -> bytes:
        if isinstance(data, str):
            data = data.encode()
        return base64.b64encode(data)
        
    def _deserialize_data(
        self,
        data: bytes,
        format: str,
        **kwargs
    ) -> Any:
        if format == "json":
            return json.loads(data.decode(), **kwargs)
        elif format == "pickle":
            return pickle.loads(data)
        elif format == "base64":
            return base64.b64decode(data)
        
    def _prepare_for_serialization(self, data: Any) -> Any:
        if is_dataclass(data):
            return asdict(data)
        elif isinstance(data, dict):
            return {
                key: self._prepare_for_serialization(value)
                for key, value in data.items()
            }
        elif isinstance(data, (list, tuple, set)):
            return [self._prepare_for_serialization(item) for item in data]
        elif isinstance(data, bytes):
            return base64.b64encode(data).decode()
        elif type(data) in self.custom_type_handlers:
            return self.custom_type_handlers[type(data)](data)
        return data
        
    def _handle_custom_types(self, obj: Any) -> Any:
        for type_, handler in self.custom_type_handlers.items():
            if isinstance(obj, type_):
                return handler(obj)
        return str(obj)
        
    def _serialize_datetime(self, dt: datetime) -> str:
        return dt.isoformat()
        
    def _deserialize_datetime(self, dt_str: str) -> datetime:
        return datetime.fromisoformat(dt_str)
        
    def _convert_to_type(self, data: Any, target_type: Type[T]) -> T:
        if is_dataclass(target_type):
            field_types = {f.name: f.type for f in fields(target_type)}
            converted_data = {}
            
            for key, value in data.items():
                if key in field_types:
                    field_type = field_types[key]
                    if field_type == datetime:
                        converted_data[key] = self._deserialize_datetime(value)
                    elif issubclass(field_type, Enum):
                        converted_data[key] = field_type[value]
                    else:
                        converted_data[key] = value
                        
            return target_type(**converted_data)
        
        return target_type(data)
    
    def register_custom_type(
        self,
        type_: Type,
        serializer: callable,
        deserializer: Optional[callable] = None
    ) -> None:
        self.custom_type_handlers[type_] = serializer
        if deserializer:
            self.custom_type_handlers[f"{type_.__name__}_deserialize"] = deserializer
            
    def remove_custom_type(self, type_: Type) -> None:
        self.custom_type_handlers.pop(type_, None)
        self.custom_type_handlers.pop(f"{type_.__name__}_deserialize", None)

class CompactSerializer(Serializer):
    def __init__(self):
        super().__init__()
        self.compression_enabled = True
        
    def serialize(
        self,
        data: Any,
        format: str = "json",
        compress: bool = True,
        **kwargs
    ) -> bytes:
        serialized_data = super().serialize(data, format, **kwargs)
        if compress and self.compression_enabled:
            import zlib
            return zlib.compress(serialized_data)
        return serialized_data
        
    def deserialize(
        self,
        data: bytes,
        format: str = "json",
        compressed: bool = True,
        **kwargs
    ) -> Any:
        if compressed and self.compression_enabled:
            import zlib
            data = zlib.decompress(data)
        return super().deserialize(data, format, **kwargs)