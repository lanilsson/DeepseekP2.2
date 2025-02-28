"""
AI Browser Middleware - Connects the r1-1776 model to the browser controller

This module provides a middleware component that allows the r1-1776 model
to receive webpage information and send control commands to the browser.
"""

import os
import sys
import json
import time
import threading
import logging
from typing import Dict, List, Any, Optional, Tuple, Union, Callable

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# Import TabType directly since it doesn't create circular imports
from selenium_qt_browser.tab_types import TabType

# We'll use lazy imports for controller to avoid circular imports
# from selenium_qt_browser.controller import BrowserController, get_controller

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class AIBrowserMiddleware:
    """Middleware component that connects the r1-1776 model to the browser controller."""
    
    def __init__(self, controller=None, model_path: Optional[str] = None):
        """Initialize the middleware with a browser controller and model path."""
        # Import controller here to avoid circular imports
        if controller is None:
            # Lazy import get_controller
            from selenium_qt_browser.controller import get_controller
            controller = get_controller()
        
        self.controller = controller
        if not self.controller:
            raise ValueError("Browser controller not available")
        
        # Default model path
        self.model_path = model_path or os.path.join(os.path.expanduser("~"), ".cache", "r1-1776")
        
        # Initialize model and tokenizer to None (will be loaded on demand)
        self.model = None
        self.tokenizer = None
        self.model_loaded = False
        
        # Register callbacks for browser events
        self.register_callbacks()
        
        # Queue for browser events
        self.event_queue = []
        self.event_lock = threading.Lock()
        
        # Context window for the AI model
        self.context = {
            "page_info": {},
            "history": [],
            "current_tab": None,
            "tabs": []
        }
        
        # Maximum number of events to keep in history
        self.max_history_length = 10
        
        # Flag to control the AI processing loop
        self.running = False
        self.processing_thread = None
    
    def register_callbacks(self):
        """Register callbacks for browser events."""
        # Register callbacks for various browser events
        self.controller.register_callback("page_info_retrieved", self.on_page_info_retrieved)
        self.controller.register_callback("element_clicked", self.on_element_clicked)
        self.controller.register_callback("input_filled", self.on_input_filled)
        self.controller.register_callback("navigated", self.on_navigated)
        self.controller.register_callback("navigated_back", self.on_navigated_back)
        self.controller.register_callback("navigated_forward", self.on_navigated_forward)
        self.controller.register_callback("page_refreshed", self.on_page_refreshed)
        self.controller.register_callback("tab_switched", self.on_tab_switched)
        self.controller.register_callback("tab_created", self.on_tab_created)
        self.controller.register_callback("tab_closed", self.on_tab_closed)
        self.controller.register_callback("terminal_command_executed", self.on_terminal_command_executed)
        self.controller.register_callback("chat_message_sent", self.on_chat_message_sent)
    
    def load_model(self, force_config: Optional[Dict[str, Any]] = None):
        """Load the r1-1776 model."""
        if self.model_loaded:
            logger.info("Model already loaded")
            return
        
        try:
            # Check if r1_1776_utils.py exists and is importable
            try:
                from r1_1776_utils import load_model
                
                logger.info(f"Loading model from {self.model_path} using r1_1776_utils...")
                self.tokenizer, self.model = load_model(
                    model_dir=self.model_path,
                    force_config=force_config,
                    verbose=True
                )
                self.model_loaded = True
                logger.info("Model loaded successfully using r1_1776_utils")
                
            except ImportError:
                # Fall back to basic loading if r1_1776_utils is not available
                logger.info(f"Loading model from {self.model_path} using basic configuration...")
                
                # Basic configuration
                config = {
                    "torch_dtype": torch.float16,
                    "device_map": "auto",
                }
                
                # Apply force_config if provided
                if force_config:
                    config.update(force_config)
                
                # Load tokenizer and model
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_path,
                    **config
                )
                self.model_loaded = True
                logger.info("Model loaded successfully using basic configuration")
        
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def unload_model(self):
        """Unload the r1-1776 model."""
        if not self.model_loaded:
            logger.info("Model not loaded")
            return
        
        try:
            # Clear model and tokenizer
            self.model = None
            self.tokenizer = None
            
            # Run garbage collection
            import gc
            gc.collect()
            
            # Clear CUDA cache if available
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            self.model_loaded = False
            logger.info("Model unloaded successfully")
            
        except Exception as e:
            logger.error(f"Error unloading model: {e}")
            raise
    
    def start(self):
        """Start the AI processing loop."""
        if self.running:
            logger.info("AI processing loop already running")
            return
        
        # Load the model if not already loaded
        if not self.model_loaded:
            self.load_model()
        
        # Start the processing thread
        self.running = True
        self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.processing_thread.start()
        logger.info("AI processing loop started")
    
    def stop(self):
        """Stop the AI processing loop."""
        if not self.running:
            logger.info("AI processing loop not running")
            return
        
        # Stop the processing thread
        self.running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=2.0)
            self.processing_thread = None
        
        logger.info("AI processing loop stopped")
    
    def _processing_loop(self):
        """Main AI processing loop."""
        while self.running:
            # Process any events in the queue
            events = self._get_events()
            if events:
                for event in events:
                    self._process_event(event)
            
            # Update context with current browser state
            self._update_context()
            
            # Generate AI actions based on context
            actions = self._generate_actions()
            
            # Execute AI actions
            if actions:
                for action in actions:
                    self._execute_action(action)
            
            # Sleep to avoid high CPU usage
            time.sleep(0.5)
    
    def _get_events(self) -> List[Dict[str, Any]]:
        """Get events from the queue."""
        with self.event_lock:
            events = self.event_queue.copy()
            self.event_queue = []
            return events
    
    def _add_event(self, event_type: str, data: Any):
        """Add an event to the queue."""
        event = {
            "type": event_type,
            "data": data,
            "timestamp": time.time()
        }
        
        with self.event_lock:
            self.event_queue.append(event)
            
            # Add to history
            self.context["history"].append(event)
            
            # Trim history if it gets too long
            if len(self.context["history"]) > self.max_history_length:
                self.context["history"] = self.context["history"][-self.max_history_length:]
    
    def _update_context(self):
        """Update the context with current browser state."""
        try:
            # Get tabs info
            tabs_info = self.controller.get_tabs_info()
            self.context["current_tab"] = tabs_info.get("current_tab")
            self.context["tabs"] = tabs_info.get("tabs", [])
            
            # Get page info for the current tab
            current_tab = self.controller.browser_window.current_tab()
            if hasattr(current_tab, 'tab_type') and current_tab.tab_type == TabType.BROWSER:
                page_info = self.controller.get_page_info()
                self.context["page_info"] = page_info
        
        except Exception as e:
            logger.error(f"Error updating context: {e}")
    
    def _generate_actions(self) -> List[Dict[str, Any]]:
        """Generate AI actions based on context."""
        if not self.model_loaded:
            return []
        
        try:
            # Convert context to a prompt for the AI model
            prompt = self._context_to_prompt()
            
            # Generate actions using the AI model
            actions = self._generate_from_prompt(prompt)
            
            return actions
        
        except Exception as e:
            logger.error(f"Error generating actions: {e}")
            return []
    
    def _context_to_prompt(self) -> str:
        """Convert context to a prompt for the AI model."""
        # Create a structured prompt with the current context
        prompt = "You are an AI assistant that can control a web browser. "
        prompt += "Here is the current state of the browser:\n\n"
        
        # Add current tab information
        current_tab_idx = self.context.get("current_tab")
        if current_tab_idx is not None and self.context.get("tabs"):
            tabs = self.context.get("tabs", [])
            if 0 <= current_tab_idx < len(tabs):
                current_tab = tabs[current_tab_idx]
                prompt += f"Current Tab: {current_tab.get('title')} (Type: {current_tab.get('type')})\n"
                if current_tab.get('type') == 'BROWSER' and current_tab.get('url'):
                    prompt += f"URL: {current_tab.get('url')}\n"
        
        # Add page information for browser tabs
        page_info = self.context.get("page_info", {})
        if page_info and page_info.get("title") and page_info.get("url"):
            prompt += f"\nPage Title: {page_info.get('title')}\n"
            prompt += f"Page URL: {page_info.get('url')}\n"
            
            # Add interactive elements
            elements = page_info.get("elements", [])
            if elements:
                prompt += "\nInteractive Elements:\n"
                for i, elem in enumerate(elements[:10]):  # Limit to 10 elements to avoid token overflow
                    elem_type = elem.get("type", "")
                    elem_text = elem.get("text", "")
                    elem_id = elem.get("id", "")
                    
                    elem_desc = f"{i+1}. {elem_type}"
                    if elem_id:
                        elem_desc += f" (id='{elem_id}')"
                    if elem_text:
                        # Truncate text if it's too long
                        text = elem_text[:50] + "..." if len(elem_text) > 50 else elem_text
                        elem_desc += f": '{text}'"
                    
                    prompt += elem_desc + "\n"
                
                if len(elements) > 10:
                    prompt += f"... and {len(elements) - 10} more elements\n"
        
        # Add recent history
        history = self.context.get("history", [])
        if history:
            prompt += "\nRecent Actions:\n"
            for event in history[-5:]:  # Show only the last 5 events
                event_type = event.get("type", "")
                event_data = event.get("data", {})
                
                if event_type == "navigated":
                    prompt += f"- Navigated to: {event_data.get('url')}\n"
                elif event_type == "element_clicked":
                    elem_id = event_data.get("element_id", "")
                    selector = event_data.get("selector", "")
                    if elem_id:
                        prompt += f"- Clicked element with id: '{elem_id}'\n"
                    elif selector:
                        prompt += f"- Clicked element with selector: '{selector}'\n"
                    else:
                        prompt += "- Clicked element\n"
                elif event_type == "input_filled":
                    elem_id = event_data.get("element_id", "")
                    selector = event_data.get("selector", "")
                    text = event_data.get("text", "")
                    if elem_id:
                        prompt += f"- Filled input with id '{elem_id}' with text: '{text}'\n"
                    elif selector:
                        prompt += f"- Filled input with selector '{selector}' with text: '{text}'\n"
                    else:
                        prompt += f"- Filled input with text: '{text}'\n"
        
        # Add instructions for the AI
        prompt += "\nBased on the current state of the browser, what action would you like to take? "
        prompt += "You can navigate to a URL, click on elements, fill input fields, etc. "
        prompt += "Please respond with a JSON object containing the action you want to take. "
        prompt += "For example:\n\n"
        prompt += '{"action": "navigate", "url": "https://www.example.com"}\n'
        prompt += '{"action": "click", "selector": "#search-button"}\n'
        prompt += '{"action": "fill", "selector": "#search-input", "text": "example search"}\n\n'
        prompt += "Your response (JSON only):"
        
        return prompt
    
    def _generate_from_prompt(self, prompt: str) -> List[Dict[str, Any]]:
        """Generate actions from a prompt using the AI model."""
        try:
            # Tokenize the prompt
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
            
            # Generate a response
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs["input_ids"],
                    max_new_tokens=200,
                    temperature=0.7,
                    do_sample=True,
                    top_p=0.95,
                    repetition_penalty=1.1
                )
            
            # Decode the response
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract the JSON part of the response
            json_str = response[len(prompt):]
            
            # Try to parse the JSON
            try:
                # Clean up the JSON string
                json_str = json_str.strip()
                
                # If the response contains multiple JSON objects, take the first one
                if json_str.startswith("{") and "}" in json_str:
                    json_str = json_str[:json_str.find("}") + 1]
                
                # Parse the JSON
                action = json.loads(json_str)
                
                # Return as a list of actions
                return [action]
            
            except json.JSONDecodeError:
                logger.error(f"Error parsing JSON from model response: {json_str}")
                return []
        
        except Exception as e:
            logger.error(f"Error generating from prompt: {e}")
            return []
    
    def _execute_action(self, action: Dict[str, Any]):
        """Execute an AI action."""
        try:
            action_type = action.get("action", "").lower()
            
            if action_type == "navigate":
                url = action.get("url", "")
                if url:
                    logger.info(f"AI action: Navigate to {url}")
                    self.controller.navigate(url)
            
            elif action_type == "click":
                element_id = action.get("element_id", "")
                selector = action.get("selector", "")
                position = action.get("position", None)
                
                if element_id:
                    logger.info(f"AI action: Click element with id '{element_id}'")
                    self.controller.click_element(element_id=element_id)
                elif selector:
                    logger.info(f"AI action: Click element with selector '{selector}'")
                    self.controller.click_element(selector=selector)
                elif position:
                    logger.info(f"AI action: Click at position {position}")
                    self.controller.click_element(position=position)
            
            elif action_type == "fill":
                element_id = action.get("element_id", "")
                selector = action.get("selector", "")
                text = action.get("text", "")
                
                if text and (element_id or selector):
                    if element_id:
                        logger.info(f"AI action: Fill input with id '{element_id}' with text '{text}'")
                        self.controller.fill_input(text, element_id=element_id)
                    elif selector:
                        logger.info(f"AI action: Fill input with selector '{selector}' with text '{text}'")
                        self.controller.fill_input(text, selector=selector)
            
            elif action_type == "back":
                logger.info("AI action: Go back")
                self.controller.go_back()
            
            elif action_type == "forward":
                logger.info("AI action: Go forward")
                self.controller.go_forward()
            
            elif action_type == "refresh":
                logger.info("AI action: Refresh page")
                self.controller.refresh()
            
            elif action_type == "switch_tab":
                tab_index = action.get("tab_index", -1)
                if tab_index >= 0:
                    logger.info(f"AI action: Switch to tab {tab_index}")
                    self.controller.switch_to_tab(tab_index)
            
            elif action_type == "create_tab":
                tab_type = action.get("tab_type", "browser")
                url = action.get("url", None)
                logger.info(f"AI action: Create new {tab_type} tab")
                self.controller.create_tab(tab_type, url)
            
            elif action_type == "close_tab":
                tab_index = action.get("tab_index", -1)
                if tab_index >= 0:
                    logger.info(f"AI action: Close tab {tab_index}")
                    self.controller.close_tab(tab_index)
            
            elif action_type == "terminal":
                command = action.get("command", "")
                if command:
                    logger.info(f"AI action: Execute terminal command '{command}'")
                    self.controller.execute_terminal_command(command)
            
            elif action_type == "chat":
                message = action.get("message", "")
                ai = action.get("ai", "Both AIs")
                if message:
                    logger.info(f"AI action: Send chat message '{message}' to {ai}")
                    self.controller.send_chat_message(message, ai)
            
            else:
                logger.warning(f"Unknown action type: {action_type}")
        
        except Exception as e:
            logger.error(f"Error executing action: {e}")
    
    # Event handlers
    
    def on_page_info_retrieved(self, data):
        """Handle page_info_retrieved event."""
        self._add_event("page_info_retrieved", data)
    
    def on_element_clicked(self, data):
        """Handle element_clicked event."""
        self._add_event("element_clicked", data)
    
    def on_input_filled(self, data):
        """Handle input_filled event."""
        self._add_event("input_filled", data)
    
    def on_navigated(self, data):
        """Handle navigated event."""
        self._add_event("navigated", data)
    
    def on_navigated_back(self, data):
        """Handle navigated_back event."""
        self._add_event("navigated_back", data)
    
    def on_navigated_forward(self, data):
        """Handle navigated_forward event."""
        self._add_event("navigated_forward", data)
    
    def on_page_refreshed(self, data):
        """Handle page_refreshed event."""
        self._add_event("page_refreshed", data)
    
    def on_tab_switched(self, data):
        """Handle tab_switched event."""
        self._add_event("tab_switched", data)
    
    def on_tab_created(self, data):
        """Handle tab_created event."""
        self._add_event("tab_created", data)
    
    def on_tab_closed(self, data):
        """Handle tab_closed event."""
        self._add_event("tab_closed", data)
    
    def on_terminal_command_executed(self, data):
        """Handle terminal_command_executed event."""
        self._add_event("terminal_command_executed", data)
    
    def on_chat_message_sent(self, data):
        """Handle chat_message_sent event."""
        self._add_event("chat_message_sent", data)


# Global middleware instance
_middleware = None

def get_middleware(controller=None, model_path=None):
    """Get the global middleware instance."""
    global _middleware
    if _middleware is None:
        # No need to import controller here since AIBrowserMiddleware handles it internally
        _middleware = AIBrowserMiddleware(controller, model_path)
    return _middleware