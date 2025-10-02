from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
import logging
import json
import sys
import asyncio

# JSON-RPC 2.0 Data Classes
@dataclass
class JsonRpcRequest:
    jsonrpc: str
    method: str
    id: Optional[Union[str, int]] = None
    params: Optional[Dict[str, Any]] = None


@dataclass
class JsonRpcResponse:
    jsonrpc: str
    id: Optional[Union[str, int]]
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None

    @staticmethod
    def dict_factory(x):
        exclude_fields = ("error", )
        return {k: v for (k, v) in x if ((v is not None) and (k not in exclude_fields))}


@dataclass
class JsonRpcError:
    code: int
    message: str
    data: Optional[Any] = None


# MCP Protocol Data Classes
@dataclass
class Tool:
    name: str
    description: str
    inputSchema: Dict[str, Any]


@dataclass
class Resource:
    uri: str
    name: str
    description: Optional[str] = None
    mimeType: Optional[str] = None


@dataclass
class Prompt:
    name: str
    description: str
    arguments: Optional[List[Dict[str, Any]]] = None


class MCPServer:
    """
    Model Context Protocol Server Implementation
    Handles JSON-RPC 2.0 communication and MCP-specific methods
    """
    
    def __init__(self, name: str = "mcp-server", version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.tools: Dict[str, Tool] = {}
        self.resources: Dict[str, Resource] = {}
        self.prompts: Dict[str, Prompt] = {}
        self.logger = self._setup_logging()
        
        # Register default MCP methods
        self._register_default_methods()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the server"""
        logger = logging.getLogger(f"mcp-server-{self.name}")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stderr)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _register_default_methods(self):
        """Register default MCP protocol methods"""
        self.methods = {
            "initialize": self._handle_initialize,
            "tools/list": self._handle_tools_list,
            "tools/call": self._handle_tools_call,
            "resources/list": self._handle_resources_list,
            "resources/read": self._handle_resources_read,
            "prompts/list": self._handle_prompts_list,
            "prompts/get": self._handle_prompts_get,
            "notifications/initialized": self._handle_notifications_initialized,
        }
    
    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialization request"""
        protocol_version = params.get("protocolVersion", "2024-11-05")
        client_info = params.get("clientInfo", {})
        
        self.logger.info(f"Initializing with client: {client_info}")
        
        return {
            "protocolVersion": protocol_version,
            "capabilities": {
                "tools": {"listChanged": True},
                #"resources": {"subscribe": True, "listChanged": True},
                #"prompts": {"listChanged": True}
            },
            "serverInfo": {
                "name": self.name,
                "version": self.version
            }
        }
    
    async def _handle_tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List available tools"""
        return {
            "tools": [asdict(tool) for tool in self.tools.values()]
        }
    
    async def _handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific tool"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name not in self.tools:
            raise JsonRpcError(-32602, f"Tool '{tool_name}' not found")
        
        # Override this method to implement tool execution
        result = await self._execute_tool(tool_name, arguments)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": str(result)
                }
            ]
        }
    
    async def _handle_resources_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List available resources"""
        return {
            "resources": [asdict(resource) for resource in self.resources.values()]
        }
    
    async def _handle_resources_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Read a specific resource"""
        uri = params.get("uri")
        
        if uri not in self.resources:
            raise JsonRpcError(-32602, f"Resource '{uri}' not found")
        
        # Override this method to implement resource reading
        content = await self._read_resource(uri)
        
        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": self.resources[uri].mimeType or "text/plain",
                    "text": content
                }
            ]
        }
    
    async def _handle_prompts_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List available prompts"""
        return {
            "prompts": [asdict(prompt) for prompt in self.prompts.values()]
        }
    
    async def _handle_prompts_get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get a specific prompt"""
        prompt_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if prompt_name not in self.prompts:
            raise JsonRpcError(-32602, f"Prompt '{prompt_name}' not found")
        
        # Override this method to implement prompt generation
        messages = await self._get_prompt(prompt_name, arguments)
        
        return {
            "description": self.prompts[prompt_name].description,
            "messages": messages
        }
    
    async def _handle_notifications_initialized(self, params: Dict[str, Any]) -> None:
        """Handle client initialized notification"""
        self.logger.info("Client has been initialized")

    # Override these methods in your implementation
    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool - override this method"""
        return f"Tool '{tool_name}' executed with arguments: {arguments}"
    
    async def _read_resource(self, uri: str) -> str:
        """Read a resource - override this method"""
        return f"Content of resource: {uri}"
    
    async def _get_prompt(self, prompt_name: str, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get prompt messages - override this method"""
        return [
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": f"Prompt '{prompt_name}' with arguments: {arguments}"
                }
            }
        ]
    
    # Registration methods
    def register_tool(self, tool: Tool):
        """Register a new tool"""
        self.tools[tool.name] = tool
        self.logger.info(f"Registered tool: {tool.name}")
    
    def register_resource(self, resource: Resource):
        """Register a new resource"""
        self.resources[resource.uri] = resource
        self.logger.info(f"Registered resource: {resource.uri}")
    
    def register_prompt(self, prompt: Prompt):
        """Register a new prompt"""
        self.prompts[prompt.name] = prompt
        self.logger.info(f"Registered prompt: {prompt.name}")
    
    # JSON-RPC 2.0 Protocol Handler
    async def handle_request(self, request_data: str) -> str:
        """Handle incoming JSON-RPC request"""
        try:
            request_json = json.loads(request_data)
            
            # Handle batch requests
            if isinstance(request_json, list):
                responses = []
                for req in request_json:
                    response = await self._process_single_request(req)
                    if response:  # Don't include notifications in batch response
                        responses.append(response)
                return json.dumps(responses) if responses else ""
            else:
                response = await self._process_single_request(request_json)
                if response is not None:
                    x = json.dumps(asdict(response, dict_factory=JsonRpcResponse.dict_factory))
                    print(f"Response: {x}", file=sys.stderr)
                return json.dumps(asdict(response, dict_factory=JsonRpcResponse.dict_factory)) if response else ""
                
        except json.JSONDecodeError as e:
            error_response = JsonRpcResponse(
                jsonrpc="2.0",
                id=None,
                error=asdict(JsonRpcError(-32700, "Parse error"))
            )
            return json.dumps(asdict(error_response))
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            error_response = JsonRpcResponse(
                jsonrpc="2.0",
                id=None,
                error=asdict(JsonRpcError(-32603, "Internal error"))
            )
            return json.dumps(asdict(error_response))
    
    async def _process_single_request(self, request_json: Dict[str, Any]) -> Optional[JsonRpcResponse]:
        """Process a single JSON-RPC request"""
        try:
            # Validate JSON-RPC structure
            if request_json.get("jsonrpc") != "2.0":
                return JsonRpcResponse(
                    jsonrpc="2.0",
                    id=request_json.get("id"),
                    error=asdict(JsonRpcError(-32600, "Invalid Request"))
                )
            
            method = request_json.get("method")
            params = request_json.get("params", {})
            request_id = request_json.get("id")
            
            # Notification (no id) - don't return response
            if request_id is None:
                if method in self.methods:
                    await self.methods[method](params)
                return None
            
            # Regular request
            if method not in self.methods:
                return JsonRpcResponse(
                    jsonrpc="2.0",
                    id=request_id,
                    error=asdict(JsonRpcError(-32601, "Method not found"))
                )
            
            result = await self.methods[method](params)
            response = JsonRpcResponse(
                jsonrpc="2.0",
                id=request_id,
                result=result
            )
            return response
            
        except JsonRpcError as e:
            return JsonRpcResponse(
                jsonrpc="2.0",
                id=request_json.get("id"),
                error=asdict(e)
            )
        except Exception as e:
            self.logger.error(f"Error processing request: {e}")
            return JsonRpcResponse(
                jsonrpc="2.0",
                id=request_json.get("id"),
                error=asdict(JsonRpcError(-32603, "Internal error"))
            )
    
    async def run(self):
        """Main server loop - reads from stdin, writes to stdout"""
        self.logger.info(f"Starting MCP Server: {self.name} v{self.version}")
        
        try:
            while True:
                # Read from stdin
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )
                
                if not line:  # EOF
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                # Process request
                response = await self.handle_request(line)
                
                # Write response to stdout
                if response != "":
                    print(response, flush=True)
                    
        except KeyboardInterrupt:
            self.logger.info("Server shutting down...")
        except Exception as e:
            self.logger.error(f"Server error: {e}")
