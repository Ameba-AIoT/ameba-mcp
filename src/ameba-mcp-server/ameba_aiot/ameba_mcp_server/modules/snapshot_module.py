from .connection_manager import ConnectionManager
from .connection_module import ConnectionModule
from .feature_module import FeatureModule
from typing import Any, Dict, List, Optional, Protocol
from mcp.types import Tool
import asyncio
import json
from pathlib import Path
import re
import urllib.request
import urllib.error
import os

class SnapshotModule(FeatureModule):
    """Module for snapshot capture and download functionality"""
    
    def __init__(self, connection_manager: ConnectionManager, connection_module: ConnectionModule):
        super().__init__(connection_manager)
        self.connection_module = connection_module
    
    @property
    def module_name(self) -> str:
        return "snapshot"
    
    def get_tools(self) -> List[Tool]:
        return [
            Tool(
                name="snapshot_capture",
                description="Capture a snapshot image on device using SNAP=SNAPS command",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "connection": {
                            "type": "string",
                            "description": "Connection to use: 'serial' or 'tcp' (default: auto-detect)",
                            "enum": ["serial", "tcp"]
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="snapshot_download",
                description="Download a snapshot image from device HTTP server and save locally",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "filename": {"type": "string", "description": "Image filename on device (e.g., 'snapshot_001.jpg')"},
                        "device_ip": {"type": "string", "description": "IP address of device"},
                        "save_path": {"type": "string", "description": "Local path to save the image (optional)"}
                    },
                    "required": ["filename", "device_ip"]
                }
            ),
            Tool(
                name="snapshot_download_all",
                description="Download all snapshot images from device HTTP server (0.jpg, 1.jpg, etc.)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device_ip": {"type": "string", "description": "IP address of device"},
                        "save_path": {"type": "string", "description": "Local path to save images (optional)"},
                        "max_files": {"type": "integer", "description": "Maximum number of files to try (optional, defaults to 100)"}
                    },
                    "required": ["device_ip"]
                }
            )
        ]
    
    async def handle_tool(self, name: str, arguments: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if name == "snapshot_capture":
            connection = arguments.get("connection", None)
            return await self.snapshot_capture(connection=connection)
        elif name == "snapshot_download":
            filename = arguments.get("filename")
            device_ip = arguments.get("device_ip")
            save_path = arguments.get("save_path", "./downloads/")
            return await self.snapshot_download(filename, device_ip, save_path)
        elif name == "snapshot_download_all":
            device_ip = arguments.get("device_ip")
            save_path = arguments.get("save_path", "./downloads/")
            max_files = arguments.get("max_files", 100)
            return await self.snapshot_download_all(device_ip, save_path, max_files)
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    async def snapshot_capture(self, connection: str = None) -> Dict[str, Any]:
        """Capture a snapshot
        
        Args:
            connection: 'serial', 'tcp', or None (auto-detect)
        """
        try:
            # Use the connection module's send_command method which handles both serial and TCP
            result = await self.connection_module.send_command("SNAP=SNAPS", connection=connection)
            
            if result["status"] == "success":
                response = result["response"]
                
                filename = None
                captured = False
                
                if "capture_snapshot_cb" in response:
                    captured = True
                    
                    filename_match = re.search(r'jpeg\s+sd:/IMAGE/(\d+\.jpg)', response)
                    if filename_match:
                        filename = filename_match.group(1)
                    else:
                        filename_match = re.search(r'sd:/IMAGE/(\d+\.jpg)', response)
                        if filename_match:
                            filename = filename_match.group(1)
                
                if captured:
                    return {
                        "status": "success",
                        "message": "Snapshot captured successfully",
                        "filename": filename,
                        "response": response,
                        "captured": True,
                        "connection": result.get("connection", "unknown"),  # Include which connection was used
                        "note": f"Image saved as {filename} on device. Use snapshot_download('{filename}', device_ip) to retrieve it"
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Snapshot command sent but capture not confirmed",
                        "response": response,
                        "captured": False,
                        "connection": result.get("connection", "unknown")
                    }
            else:
                return result
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def snapshot_download(self, filename: str, device_ip: str, save_path: str = "./downloads/") -> Dict[str, Any]:
        """Download snapshot image"""
        try:
            Path(save_path).mkdir(parents=True, exist_ok=True)
            
            url = f"http://{device_ip}/image_get.jpg?filename={filename}"
            
            try:
                with urllib.request.urlopen(url, timeout=30) as response:
                    content = response.read()
                    
                    local_filename = os.path.join(save_path, filename)
                    
                    with open(local_filename, 'wb') as f:
                        f.write(content)
                    
                    file_size = len(content)
                    
                    return {
                        "status": "success",
                        "message": f"Image downloaded successfully",
                        "filename": filename,
                        "local_path": os.path.abspath(local_filename),
                        "file_size": file_size,
                        "url": url,
                        "note": f"Image saved to {local_filename}. You can now use extract_image_from_file with this path."
                    }
                    
            except urllib.error.HTTPError as e:
                return {
                    "status": "error",
                    "error": f"HTTP {e.code}: {e.reason}",
                    "url": url
                }
            except urllib.error.URLError as e:
                return {
                    "status": "error",
                    "error": f"URL Error: {str(e)}",
                    "url": url
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "url": url if 'url' in locals() else None
            }
    
    async def snapshot_download_all(self, device_ip: str, save_path: str = "./downloads/", max_files: int = 100) -> Dict[str, Any]:
        """Download all snapshot images"""
        try:
            Path(save_path).mkdir(parents=True, exist_ok=True)
            
            index_url = f"http://{device_ip}/index.htm"
            image_files = []
            
            try:
                with urllib.request.urlopen(index_url, timeout=10) as response:
                    html_content = response.read().decode('utf-8', errors='ignore')
                    
                    jpg_pattern = re.findall(r'(\d+\.jpg)', html_content)
                    image_files = sorted(list(set(jpg_pattern)), key=lambda x: int(x.split('.')[0]))
                    
                    print(f"Found {len(image_files)} image files in index: {image_files}")
                    
            except Exception as e:
                return {
                    "status": "error",
                    "error": f"Failed to fetch file list from {index_url}: {str(e)}"
                }
            
            if not image_files:
                return {
                    "status": "success",
                    "message": "No image files found on device",
                    "downloaded_files": [],
                    "total_downloaded": 0,
                    "device_ip": device_ip,
                    "index_url": index_url
                }
            
            downloaded_files = []
            failed_files = []
            
            for filename in image_files:
                url = f"http://{device_ip}/image_get.jpg?filename={filename}"
                
                try:
                    with urllib.request.urlopen(url, timeout=10) as response:
                        content = response.read()
                        
                        if len(content) > 1000:
                            local_filename = os.path.join(save_path, filename)
                            
                            with open(local_filename, 'wb') as f:
                                f.write(content)
                            
                            downloaded_files.append({
                                "filename": filename,
                                "local_path": os.path.abspath(local_filename),
                                "size": len(content)
                            })
                            
                            print(f"Downloaded {filename} ({len(content)} bytes)")
                        else:
                            failed_files.append(filename)
                            
                except (urllib.error.HTTPError, urllib.error.URLError) as e:
                    failed_files.append(filename)
                    
                except Exception as e:
                    failed_files.append(filename)
                
                await asyncio.sleep(0.1)
            
            return {
                "status": "success",
                "message": f"Downloaded {len(downloaded_files)} out of {len(image_files)} images",
                "downloaded_files": downloaded_files,
                "failed_files": failed_files,
                "total_found": len(image_files),
                "total_downloaded": len(downloaded_files),
                "total_failed": len(failed_files),
                "save_path": os.path.abspath(save_path),
                "device_ip": device_ip,
                "note": "Images saved successfully. You can now use extract_image_from_file on any of them." if downloaded_files else "No images were downloaded"
            }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "downloaded_files": downloaded_files if 'downloaded_files' in locals() else [],
                "device_ip": device_ip
            }