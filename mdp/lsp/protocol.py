"""
LSP protocol implementation for MDP.

This module provides the core protocol handling for the MDP Language Server Protocol
implementation, including request/response handling and JSON-RPC communication.
"""

import json
import logging
import os
import sys
from typing import Any, Dict, Optional, List, Union, Callable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename=os.path.join(os.path.expanduser("~"), ".mdp", "lsp.log"),
    filemode="w"
)
logger = logging.getLogger("mdp-lsp")

# Constants
EOL = "\r\n"
ENCODING = "utf-8"


def read_message():
    """
    Read a JSON-RPC message from stdin following the LSP protocol.
    
    Returns:
        Dict: The parsed JSON message
    """
    content_length = 0
    while True:
        header = sys.stdin.readline().strip()
        if not header:
            break
        
        if header.startswith("Content-Length:"):
            content_length = int(header.split("Content-Length:")[1].strip())
    
    if content_length > 0:
        content = sys.stdin.read(content_length)
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON: {content}")
            return {}
    
    return {}


def write_message(message: Dict[str, Any]):
    """
    Write a JSON-RPC message to stdout following the LSP protocol.
    
    Args:
        message: The message to write
    """
    content = json.dumps(message)
    content_length = len(content)
    response = f"Content-Length: {content_length}{EOL}{EOL}{content}"
    sys.stdout.write(response)
    sys.stdout.flush()


def create_response(request_id: Union[str, int], result: Any) -> Dict[str, Any]:
    """
    Create a JSON-RPC response.
    
    Args:
        request_id: The ID of the request being responded to
        result: The result of the request
    
    Returns:
        Dict: The response message
    """
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": result
    }


def create_error_response(request_id: Union[str, int], code: int, message: str) -> Dict[str, Any]:
    """
    Create a JSON-RPC error response.
    
    Args:
        request_id: The ID of the request being responded to
        code: The error code
        message: The error message
    
    Returns:
        Dict: The error response message
    """
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {
            "code": code,
            "message": message
        }
    }


def create_notification(method: str, params: Any) -> Dict[str, Any]:
    """
    Create a JSON-RPC notification.
    
    Args:
        method: The notification method
        params: The notification parameters
    
    Returns:
        Dict: The notification message
    """
    return {
        "jsonrpc": "2.0",
        "method": method,
        "params": params
    }


def start_io_lang_server(server):
    """
    Start the language server using stdin/stdout for communication.
    
    Args:
        server: The language server instance
    """
    logger.info("Starting MDP Language Server")
    
    while True:
        try:
            request = read_message()
            if not request:
                continue
            
            method = request.get("method")
            if not method:
                continue
            
            request_id = request.get("id")
            params = request.get("params", {})
            
            # Handle shutdown and exit
            if method == "exit":
                break
            
            # Forward to server method
            try:
                handler = getattr(server, f"on_{method.replace('/', '_')}")
                if request_id is not None:
                    # This is a request
                    result = handler(params)
                    response = create_response(request_id, result)
                    write_message(response)
                else:
                    # This is a notification
                    handler(params)
            except AttributeError:
                logger.warning(f"No handler for {method}")
                if request_id is not None:
                    response = create_error_response(
                        request_id, 
                        -32601, 
                        f"Method not found: {method}"
                    )
                    write_message(response)
            except Exception as e:
                logger.error(f"Error handling {method}: {e}")
                if request_id is not None:
                    response = create_error_response(
                        request_id, 
                        -32603, 
                        f"Internal error: {str(e)}"
                    )
                    write_message(response)
            
        except Exception as e:
            logger.error(f"Error reading request: {e}")
            # Continue server operation despite errors

    logger.info("MDP Language Server stopped") 