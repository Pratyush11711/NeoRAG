import json
from datetime import datetime
from typing import Any

def default_json_serializer(obj: Any) -> Any:
    if isinstance(obj, datetime):
        return obj.isoformat()
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return str(obj)

def safe_json_dumps(data: Any, indent: int = 2) -> str:
    return json.dumps(data, default=default_json_serializer, indent=indent)

def safe_json_loads(data_str: str) -> Any:
    return json.loads(data_str)
