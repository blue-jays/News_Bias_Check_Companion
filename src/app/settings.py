from __future__ import annotations
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Dict, List, Optional
import os, copy, yaml


# function to load the yaml file safely.
def _load_yaml(path:str) -> Dict[str, Any]:
    """Takes the path of the yaml file.
    It returns a dictionary, the key is string. 
    Value could be Any: int, float, str
    """
    with open( path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        return data or {}
    
# merge 2 dictionaries into 1.
def _deep_merge(a: Dict[str,Any], b: Dict[str, Any]) -> Dict[str:Any]:
    ""
    dc = copy.deepcopy(a)
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(dc.get(k), dict):
            dc[k] = _deep_merge(dc[k], v)
        else:
            dc[k] = copy.deepcopy(v)
    return dc


# declare the dataclasses.
@dataclass
class ServerConfig: