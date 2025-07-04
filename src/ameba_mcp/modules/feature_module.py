from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol
from .connection_manager import ConnectionManager
from mcp.types import Tool

class FeatureModule(ABC):
    """Base class for all feature modules"""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.conn = connection_manager
    
    @abstractmethod
    def get_tools(self) -> List[Tool]:
        """Return list of tools provided by this module"""
        pass
    
    @abstractmethod
    async def handle_tool(self, name: str, arguments: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Handle tool calls for this module"""
        pass
    
    @property
    @abstractmethod
    def module_name(self) -> str:
        """Return the name of this module"""
        pass