"""
CLI entry point for the MDP Language Server.

This module provides a command-line interface for starting the MDP Language Server.
"""

import argparse
import logging
import os
import sys

from .server import MDPLanguageServer
from .protocol import start_io_lang_server


def setup_logging(log_file: str = None, debug: bool = False) -> None:
    """
    Set up logging for the LSP server.
    
    Args:
        log_file: Path to the log file (if None, logs to ~/.mdp/lsp.log)
        debug: Whether to enable debug logging
    """
    if not log_file:
        # Ensure ~/.mdp directory exists
        mdp_dir = os.path.join(os.path.expanduser("~"), ".mdp")
        os.makedirs(mdp_dir, exist_ok=True)
        log_file = os.path.join(mdp_dir, "lsp.log")
    
    level = logging.DEBUG if debug else logging.INFO
    
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        filename=log_file,
        filemode="w"
    )
    
    # Also log to stderr if in debug mode
    if debug:
        console = logging.StreamHandler(sys.stderr)
        console.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(levelname)s: %(message)s")
        console.setFormatter(formatter)
        logging.getLogger().addHandler(console)
    
    # Log startup information
    logger = logging.getLogger("mdp-lsp")
    logger.info(f"Starting MDP Language Server, logging to {log_file}")
    if debug:
        logger.info("Debug logging enabled")


def create_parser() -> argparse.ArgumentParser:
    """
    Create the command-line argument parser.
    
    Returns:
        argparse.ArgumentParser: The argument parser
    """
    parser = argparse.ArgumentParser(
        description="MDP Language Server",
        prog="mdp-language-server"
    )
    
    parser.add_argument(
        "--log-file",
        help="Path to the log file (default: ~/.mdp/lsp.log)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    parser.add_argument(
        "--tcp",
        action="store_true",
        help="Use TCP server instead of stdio (not implemented yet)"
    )
    
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="TCP server host (default: 127.0.0.1)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=2087,
        help="TCP server port (default: 2087)"
    )
    
    return parser


def main(args=None) -> int:
    """
    Main entry point for the LSP server.
    
    Args:
        args: Command-line arguments (if None, uses sys.argv)
        
    Returns:
        int: Exit code
    """
    parser = create_parser()
    parsed_args = parser.parse_args(args)
    
    # Set up logging
    setup_logging(parsed_args.log_file, parsed_args.debug)
    
    try:
        # Create the server
        server = MDPLanguageServer()
        
        # Start the server
        if parsed_args.tcp:
            # TCP server (not implemented yet)
            logger = logging.getLogger("mdp-lsp")
            logger.error("TCP server not implemented yet")
            return 1
        else:
            # stdio server
            start_io_lang_server(server)
        
        return 0
    except Exception as e:
        logger = logging.getLogger("mdp-lsp")
        logger.exception(f"Error starting server: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 