"""
Server Module - Implements HTTP server for the browser API

This module provides an HTTP server that exposes the browser API to external clients,
allowing them to control the browser and terminal through HTTP requests.
"""

import os
import sys
import json
import threading
import logging
from typing import Dict, Any, Optional

from flask import Flask, request, jsonify
from flask_cors import CORS

from selenium_qt_browser.api import BrowserController


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('selenium_qt_browser.server')


class APIServer:
    """HTTP server for the browser API."""
    
    def __init__(self, browser_controller: BrowserController, host: str = '127.0.0.1', port: int = 5000):
        self.browser_controller = browser_controller
        self.host = host
        self.port = port
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for all routes
        
        # Register routes
        self.register_routes()
        
        self.server_thread = None
        self.is_running = False
    
    def register_routes(self):
        """Register the API routes."""
        
        @self.app.route('/api/status', methods=['GET'])
        def status():
            """Get the server status."""
            return jsonify({
                "status": "running",
                "tabs": self.browser_controller.get_tabs_info()
            })
        
        @self.app.route('/api/command', methods=['POST'])
        def execute_command():
            """Execute a command."""
            try:
                data = request.json
                if not data:
                    return jsonify({"error": "No JSON data provided"}), 400
                
                command_type = data.get('type')
                command = data.get('command')
                args = data.get('args', {})
                
                if not command_type or not command:
                    return jsonify({"error": "Missing 'type' or 'command' field"}), 400
                
                result = self.browser_controller.execute_command(command_type, command, **args)
                return jsonify(result)
            
            except Exception as e:
                logger.exception("Error executing command")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/tabs', methods=['GET'])
        def get_tabs():
            """Get information about all tabs."""
            return jsonify(self.browser_controller.get_tabs_info())
        
        @self.app.route('/api/tabs/switch/<int:tab_index>', methods=['POST'])
        def switch_tab(tab_index):
            """Switch to a specific tab."""
            return jsonify(self.browser_controller.switch_to_tab(tab_index))
        
        @self.app.route('/api/tabs/create', methods=['POST'])
        def create_tab():
            """Create a new tab."""
            data = request.json or {}
            tab_type = data.get('tab_type', 'browser')
            return jsonify(self.browser_controller.create_tab(tab_type))
        
        @self.app.route('/api/tabs/close/<int:tab_index>', methods=['POST'])
        def close_tab(tab_index):
            """Close a specific tab."""
            return jsonify(self.browser_controller.close_tab(tab_index))
        
        @self.app.route('/api/browser/info', methods=['GET'])
        def get_page_info():
            """Get information about the current webpage."""
            return jsonify(self.browser_controller.execute_browser_command('get_page_info'))
        
        @self.app.route('/api/browser/navigate', methods=['POST'])
        def navigate():
            """Navigate to a URL."""
            data = request.json or {}
            url = data.get('url')
            if not url:
                return jsonify({"error": "Missing 'url' field"}), 400
            return jsonify(self.browser_controller.execute_browser_command('navigate', url=url))
        
        @self.app.route('/api/browser/click', methods=['POST'])
        def click_element():
            """Click an element on the webpage."""
            data = request.json or {}
            element_id = data.get('element_id')
            selector = data.get('selector')
            position = data.get('position')
            
            if not any([element_id, selector, position]):
                return jsonify({"error": "Must provide element_id, selector, or position"}), 400
            
            return jsonify(self.browser_controller.execute_browser_command(
                'click_element', 
                element_id=element_id, 
                selector=selector, 
                position=position
            ))
        
        @self.app.route('/api/browser/fill', methods=['POST'])
        def fill_input():
            """Fill a text input field."""
            data = request.json or {}
            text = data.get('text')
            element_id = data.get('element_id')
            selector = data.get('selector')
            
            if not text:
                return jsonify({"error": "Missing 'text' field"}), 400
            
            if not any([element_id, selector]):
                return jsonify({"error": "Must provide element_id or selector"}), 400
            
            return jsonify(self.browser_controller.execute_browser_command(
                'fill_input', 
                text=text, 
                element_id=element_id, 
                selector=selector
            ))
        
        @self.app.route('/api/browser/back', methods=['POST'])
        def go_back():
            """Navigate back in history."""
            return jsonify(self.browser_controller.execute_browser_command('go_back'))
        
        @self.app.route('/api/browser/forward', methods=['POST'])
        def go_forward():
            """Navigate forward in history."""
            return jsonify(self.browser_controller.execute_browser_command('go_forward'))
        
        @self.app.route('/api/browser/refresh', methods=['POST'])
        def refresh():
            """Refresh the current page."""
            return jsonify(self.browser_controller.execute_browser_command('refresh'))
        
        @self.app.route('/api/terminal/execute', methods=['POST'])
        def execute_terminal_command():
            """Execute a command in the terminal."""
            data = request.json or {}
            command = data.get('command')
            
            if not command:
                return jsonify({"error": "Missing 'command' field"}), 400
            
            return jsonify(self.browser_controller.execute_terminal_command(
                'execute_command', 
                command=command
            ))
        
        @self.app.route('/api/terminal/directory', methods=['GET'])
        def get_current_directory():
            """Get the current working directory of the terminal."""
            return jsonify(self.browser_controller.execute_terminal_command('get_current_directory'))
        
        @self.app.route('/api/chat/send', methods=['POST'])
        def send_chat_message():
            """Send a message to the AI chat."""
            data = request.json or {}
            message = data.get('message')
            ai = data.get('ai', 'Both AIs')
            
            if not message:
                return jsonify({"error": "Missing 'message' field"}), 400
            
            return jsonify(self.browser_controller.execute_chat_command(
                'send_message', 
                message=message, 
                ai=ai
            ))
    
    def start(self):
        """Start the server in a separate thread."""
        if self.is_running:
            logger.warning("Server is already running")
            return
        
        def run_server():
            logger.info(f"Starting API server on {self.host}:{self.port}")
            self.app.run(host=self.host, port=self.port, debug=False, use_reloader=False)
        
        self.server_thread = threading.Thread(target=run_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        self.is_running = True
        
        logger.info(f"API server started on http://{self.host}:{self.port}")
    
    def stop(self):
        """Stop the server."""
        if not self.is_running:
            logger.warning("Server is not running")
            return
        
        # Flask doesn't provide a clean way to stop the server from another thread
        # In a production environment, you would use a more robust server like gunicorn
        # For now, we'll just set the flag and let the thread die when the application exits
        self.is_running = False
        logger.info("API server stopping")


def create_server(browser_controller: BrowserController, host: str = '127.0.0.1', port: int = 5000) -> APIServer:
    """Create and start an API server."""
    server = APIServer(browser_controller, host, port)
    server.start()
    return server