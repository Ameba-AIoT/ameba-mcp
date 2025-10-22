#!/usr/bin/env python3
"""
Minimal MCP Server Skeleton
Implements the Model Context Protocol without external dependencies.
Uses FastMCP-style @mcp.tool decorators for defining tools.
"""

import json
import sys
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class Tool:
    """Represents an MCP tool."""
    name: str
    description: str
    func: Callable
    input_schema: Dict[str, Any]


class MCPServer:
    """Minimal MCP Server implementation with decorator support."""
    
    def __init__(self, name: str = "mcp-server"):
        self.name = name
        self.tools: Dict[str, Tool] = {}
        self.request_id = 0
    
    def tool(self, func: Optional[Callable] = None, input_schema: Optional[Dict[str, Any]] = None):
        """
        Decorator to register a function as an MCP tool.
        
        Usage:
            @mcp.tool
            def my_tool(param1: str, param2: int) -> str:
                '''Does something useful'''
                return f"Result: {param1} {param2}"
        """
        def decorator(f: Callable) -> Callable:
            tool_name = f.__name__
            
            # Extract description from docstring
            description = (f.__doc__ or "").strip() or f"Tool: {tool_name}"
            
            # Generate default schema if not provided
            schema = input_schema or {
                "type": "object",
                "properties": {},
                "required": []
            }
            
            tool = Tool(
                name=tool_name,
                description=description,
                func=f,
                input_schema=schema
            )
            
            self.tools[tool_name] = tool
            return f
        
        # Support both @mcp.tool and @mcp.tool() syntax
        if func is not None:
            return decorator(func)
        return decorator
    
    def _send_response(self, response: Dict[str, Any]):
        """Send a JSON-RPC response to stdout."""
        json.dump(response, sys.stdout)
        sys.stdout.write('\n')
        sys.stdout.flush()
    
    def _send_error(self, request_id: Any, code: int, message: str):
        """Send a JSON-RPC error response."""
        self._send_response({
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        })
    
    def _handle_list_tools(self, request_id: Any):
        """Handle tools/list request."""
        tools_list = [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.input_schema
            }
            for tool in self.tools.values()
        ]
        
        self._send_response({
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": tools_list
            }
        })
    
    def _handle_call_tool(self, request_id: Any, params: Dict[str, Any]):
        """Handle tools/call request."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name not in self.tools:
            self._send_error(request_id, -32602, f"Unknown tool: {tool_name}")
            return
        
        tool = self.tools[tool_name]
        
        try:
            # Call the tool function with arguments
            result = tool.func(**arguments)
            
            # Format response
            self._send_response({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": str(result)
                        }
                    ]
                }
            })
        except Exception as e:
            self._send_error(request_id, -32603, f"Tool execution error: {str(e)}")
    
    def _handle_request(self, request: Dict[str, Any]):
        """Handle a single JSON-RPC request."""
        request_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})
        
        if method == "tools/list":
            self._handle_list_tools(request_id)
        elif method == "tools/call":
            self._handle_call_tool(request_id, params)
        elif method == "notifications/initialized":
            # Acknowledge initialization
            self._send_response({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {}
            })
        elif method == "initialize":
            # Acknowledge initialization
            self._send_response({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {
                        "logging": {},
                        "tools": {
                            "listChanged": "true"
                        }
                    },
                    "serverInfo": {
                        "name": self.name,
                        "version": "1.0.0"
                    },
                    "instructions": "This MCP server implements basic tool listing and calling functionality."
                }
            })
        else:
            self._send_error(request_id, -32601, f"Method not found: {method}")
    
    def run(self, transport=""):
        """Run the MCP server (reads from stdin, writes to stdout)."""
        if transport != "":
            print(f"Warning: transport '{transport}' is not supported. Defaulting to stdin/stdout.", file=sys.stderr)

        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            
            try:
                request = json.loads(line)
                self._handle_request(request)
            except json.JSONDecodeError as e:
                self._send_error(None, -32700, f"Parse error: {str(e)}")
            except Exception as e:
                self._send_error(None, -32603, f"Internal error: {str(e)}")