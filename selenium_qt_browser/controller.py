"""
Controller Module - Provides direct programmatic access to the browser

This module allows scripts to directly control the browser, terminal, and chat
functionality without using an HTTP API.
"""

import os
import sys
import time
import json
from typing import Dict, List, Any, Optional, Tuple, Union, Callable

from PyQt6.QtCore import QObject, QTimer, QEventLoop, Qt
from PyQt6.QtWidgets import QApplication, QLabel
from PyQt6.QtWebEngineCore import QWebEngineScript

# Import TabType directly since it doesn't create circular imports
from selenium_qt_browser.tab_types import TabType

# Use lazy imports for browser to avoid circular imports
# from selenium_qt_browser.browser import BrowserWindow, BrowserTab


class BrowserController:
    """Controller for direct programmatic access to the browser."""
    
    def __init__(self, browser_window):
        """Initialize the controller with a browser window."""
        self.browser_window = browser_window
        self.callbacks = {}
    
    def register_callback(self, event_type: str, callback: Callable):
        """Register a callback for a specific event type."""
        if event_type not in self.callbacks:
            self.callbacks[event_type] = []
        self.callbacks[event_type].append(callback)
    
    def trigger_callback(self, event_type: str, data: Any = None):
        """Trigger callbacks for a specific event type."""
        if event_type in self.callbacks:
            for callback in self.callbacks[event_type]:
                callback(data)
    
    def get_tabs_info(self) -> Dict[str, Any]:
        """Get information about all tabs."""
        tabs = []
        
        for i in range(self.browser_window.tab_widget.count()):
            tab = self.browser_window.tab_widget.widget(i)
            tab_type = "unknown"
            
            if hasattr(tab, 'tab_type'):
                tab_type = tab.tab_type.name
            
            tab_info = {
                "index": i,
                "title": self.browser_window.tab_widget.tabText(i),
                "type": tab_type
            }
            
            # Add type-specific information
            if hasattr(tab, 'tab_type'):
                if tab.tab_type == TabType.BROWSER and hasattr(tab, 'current_url'):
                    tab_info["url"] = tab.current_url()
            
            tabs.append(tab_info)
        
        return {
            "current_tab": self.browser_window.tab_widget.currentIndex(),
            "tabs": tabs
        }
    
    def switch_to_tab(self, tab_index: int) -> Dict[str, Any]:
        """Switch to a specific tab."""
        if tab_index < 0 or tab_index >= self.browser_window.tab_widget.count():
            return {"error": f"Tab index {tab_index} out of range"}
        
        self.browser_window.tab_widget.setCurrentIndex(tab_index)
        
        current_tab = self.browser_window.current_tab()
        tab_type = "unknown"
        
        if hasattr(current_tab, 'tab_type'):
            tab_type = current_tab.tab_type.name
        
        self.trigger_callback("tab_switched", {
            "tab_index": tab_index,
            "tab_type": tab_type
        })
        
        return {
            "tab_index": tab_index,
            "tab_type": tab_type
        }
    
    def create_tab(self, tab_type: str, url: str = None) -> Dict[str, Any]:
        """Create a new tab of the specified type."""
        if tab_type.lower() == "browser":
            tab = self.browser_window.add_new_tab(url)
            result = {
                "tab_index": self.browser_window.tab_widget.indexOf(tab),
                "tab_type": "BROWSER",
                "url": url or self.browser_window.start_url
            }
        elif tab_type.lower() == "chat":
            tab = self.browser_window.add_new_chat_tab()
            result = {"tab_index": self.browser_window.tab_widget.indexOf(tab), "tab_type": "CHAT"}
        elif tab_type.lower() == "terminal":
            tab = self.browser_window.add_new_terminal_tab()
            result = {"tab_index": self.browser_window.tab_widget.indexOf(tab), "tab_type": "TERMINAL"}
        else:
            return {"error": f"Unknown tab type: {tab_type}"}
        
        self.trigger_callback("tab_created", result)
        return result
    
    def close_tab(self, tab_index: int) -> Dict[str, Any]:
        """Close a specific tab."""
        if tab_index < 0 or tab_index >= self.browser_window.tab_widget.count():
            return {"error": f"Tab index {tab_index} out of range"}
        
        self.browser_window.close_tab(tab_index)
        
        result = {
            "closed_tab_index": tab_index,
            "remaining_tabs": self.browser_window.tab_widget.count()
        }
        
        self.trigger_callback("tab_closed", result)
        return result
    
    def _get_current_browser_tab(self):
        """Get the current browser tab if it's a web browser tab."""
        current_tab = self.browser_window.current_tab()
        if hasattr(current_tab, 'tab_type') and current_tab.tab_type == TabType.BROWSER:
            return current_tab
        return None
    
    def _execute_js(self, script: str) -> Any:
        """Execute JavaScript in the current browser tab and return the result."""
        tab = self._get_current_browser_tab()
        if not tab:
            return None
        
        result = None
        loop = QEventLoop()
        
        def callback(r):
            nonlocal result
            result = r
            loop.quit()
        
        tab.current_page().runJavaScript(script, 0, callback)
        loop.exec()
        
        return result
    
    def get_page_info(self) -> Dict[str, Any]:
        """Get information about the current webpage."""
        tab = self._get_current_browser_tab()
        if not tab:
            return {"error": "No browser tab is currently active"}
        
        # JavaScript for extracting page information
        extract_elements_script = """
        (function() {
            function getElementInfo(element) {
                const rect = element.getBoundingClientRect();
                const computedStyle = window.getComputedStyle(element);
                const isVisible = computedStyle.display !== 'none' && 
                                 computedStyle.visibility !== 'hidden' && 
                                 rect.width > 0 && rect.height > 0;
                
                // Get all attributes
                const attributes = {};
                for (let i = 0; i < element.attributes.length; i++) {
                    const attr = element.attributes[i];
                    attributes[attr.name] = attr.value;
                }
                
                return {
                    id: element.id || '',
                    tagName: element.tagName.toLowerCase(),
                    type: element.type || '',
                    text: element.textContent.trim(),
                    value: element.value || '',
                    attributes: attributes,
                    position: [rect.left, rect.top],
                    size: [rect.width, rect.height],
                    isVisible: isVisible
                };
            }
            
            // Get all interactive elements
            const interactiveElements = document.querySelectorAll(
                'button, a, input, textarea, select, [role="button"], [onclick]'
            );
            
            const elements = [];
            interactiveElements.forEach(element => {
                elements.push(getElementInfo(element));
            });
            
            // Get page title and URL
            const pageInfo = {
                title: document.title,
                url: window.location.href
            };
            
            return {
                pageInfo: pageInfo,
                elements: elements
            };
        })();
        """
        
        result = self._execute_js(extract_elements_script)
        if not result:
            return {"error": "Failed to extract page information"}
        
        # Process elements
        elements = []
        for elem_data in result.get("elements", []):
            element_type = elem_data.get("tagName", "").lower()
            
            element = {
                "id": elem_data.get("id", ""),
                "type": element_type,
                "text": elem_data.get("text", ""),
                "attributes": elem_data.get("attributes", {}),
                "position": tuple(elem_data.get("position", [0, 0])),
                "size": tuple(elem_data.get("size", [0, 0])),
                "is_visible": elem_data.get("isVisible", False)
            }
            elements.append(element)
        
        page_info = result.get("pageInfo", {})
        
        response = {
            "title": page_info.get("title", ""),
            "url": page_info.get("url", ""),
            "elements": elements
        }
        
        self.trigger_callback("page_info_retrieved", response)
        return response
    
    def click_element(self, element_id: str = None, selector: str = None, 
                     position: Tuple[int, int] = None) -> Dict[str, Any]:
        """Click an element on the webpage."""
        tab = self._get_current_browser_tab()
        if not tab:
            return {"error": "No browser tab is currently active"}
        
        if element_id:
            script = f"""
            (function() {{
                const element = document.getElementById('{element_id}');
                if (element) {{
                    element.click();
                    return true;
                }}
                return false;
            }})();
            """
        elif selector:
            script = f"""
            (function() {{
                const element = document.querySelector('{selector}');
                if (element) {{
                    element.click();
                    return true;
                }}
                return false;
            }})();
            """
        elif position:
            x, y = position
            script = f"""
            (function() {{
                const element = document.elementFromPoint({x}, {y});
                if (element) {{
                    element.click();
                    return true;
                }}
                return false;
            }})();
            """
        else:
            return {"error": "Must provide element_id, selector, or position"}
        
        result = self._execute_js(script)
        
        if result:
            # Wait a moment for the page to update
            time.sleep(0.5)
            # Get updated page info
            page_info = self.get_page_info()
            self.trigger_callback("element_clicked", {
                "element_id": element_id,
                "selector": selector,
                "position": position,
                "page_info": page_info
            })
            return page_info
        else:
            return {"error": "Element not found or not clickable"}
    
    def fill_input(self, text: str, element_id: str = None, 
                  selector: str = None) -> Dict[str, Any]:
        """Fill a text input field."""
        tab = self._get_current_browser_tab()
        if not tab:
            return {"error": "No browser tab is currently active"}
        
        if element_id:
            script = f"""
            (function() {{
                const element = document.getElementById('{element_id}');
                if (element && (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA')) {{
                    element.value = '{text}';
                    // Trigger input event
                    const event = new Event('input', {{ bubbles: true }});
                    element.dispatchEvent(event);
                    return true;
                }}
                return false;
            }})();
            """
        elif selector:
            script = f"""
            (function() {{
                const element = document.querySelector('{selector}');
                if (element && (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA')) {{
                    element.value = '{text}';
                    // Trigger input event
                    const event = new Event('input', {{ bubbles: true }});
                    element.dispatchEvent(event);
                    return true;
                }}
                return false;
            }})();
            """
        else:
            return {"error": "Must provide element_id or selector"}
        
        result = self._execute_js(script)
        
        if result:
            page_info = self.get_page_info()
            self.trigger_callback("input_filled", {
                "element_id": element_id,
                "selector": selector,
                "text": text,
                "page_info": page_info
            })
            return page_info
        else:
            return {"error": "Input element not found"}
    
    def navigate(self, url: str) -> Dict[str, Any]:
        """Navigate to a URL."""
        tab = self._get_current_browser_tab()
        if not tab:
            return {"error": "No browser tab is currently active"}
        
        tab.navigate_to(url)
        
        # Wait for page to load
        time.sleep(1)
        
        page_info = self.get_page_info()
        self.trigger_callback("navigated", {
            "url": url,
            "page_info": page_info
        })
        return page_info
    
    def go_back(self) -> Dict[str, Any]:
        """Navigate back in history."""
        tab = self._get_current_browser_tab()
        if not tab:
            return {"error": "No browser tab is currently active"}
        
        tab.web_view.back()
        
        # Wait for page to load
        time.sleep(1)
        
        page_info = self.get_page_info()
        self.trigger_callback("navigated_back", {
            "page_info": page_info
        })
        return page_info
    
    def go_forward(self) -> Dict[str, Any]:
        """Navigate forward in history."""
        tab = self._get_current_browser_tab()
        if not tab:
            return {"error": "No browser tab is currently active"}
        
        tab.web_view.forward()
        
        # Wait for page to load
        time.sleep(1)
        
        page_info = self.get_page_info()
        self.trigger_callback("navigated_forward", {
            "page_info": page_info
        })
        return page_info
    
    def refresh(self) -> Dict[str, Any]:
        """Refresh the current page."""
        tab = self._get_current_browser_tab()
        if not tab:
            return {"error": "No browser tab is currently active"}
        
        tab.web_view.reload()
        
        # Wait for page to load
        time.sleep(1)
        
        page_info = self.get_page_info()
        self.trigger_callback("page_refreshed", {
            "page_info": page_info
        })
        return page_info
    
    def _get_current_terminal_tab(self):
        """Get the current terminal tab if it's a terminal tab."""
        current_tab = self.browser_window.current_tab()
        if hasattr(current_tab, 'tab_type') and current_tab.tab_type == TabType.TERMINAL:
            return current_tab
        return None
    
    def execute_terminal_command(self, command: str) -> Dict[str, Any]:
        """Execute a command in the terminal."""
        tab = self._get_current_terminal_tab()
        if not tab:
            return {"error": "No terminal tab is currently active"}
        
        # Clear the previous output
        previous_output = tab.terminal_output.toPlainText()
        
        # Execute the command
        tab.execute_command(command)
        
        # Wait for command to complete and output to be updated
        time.sleep(0.5)
        
        # Get the new output
        current_output = tab.terminal_output.toPlainText()
        
        # Extract only the new output
        if current_output.startswith(previous_output):
            new_output = current_output[len(previous_output):].strip()
        else:
            new_output = current_output
        
        result = {
            "command": command,
            "output": new_output
        }
        
        self.trigger_callback("terminal_command_executed", result)
        return result
    
    def get_current_directory(self) -> Dict[str, Any]:
        """Get the current working directory of the terminal."""
        tab = self._get_current_terminal_tab()
        if not tab:
            return {"error": "No terminal tab is currently active"}
        
        # Execute pwd command
        result = self.execute_terminal_command("pwd")
        
        if "error" in result:
            return result
        
        directory_result = {
            "current_directory": result["output"].strip()
        }
        
        self.trigger_callback("current_directory_retrieved", directory_result)
        return directory_result
    
    def _get_current_chat_tab(self):
        """Get the current chat tab if it's a chat tab."""
        current_tab = self.browser_window.current_tab()
        if hasattr(current_tab, 'tab_type') and current_tab.tab_type == TabType.CHAT:
            return current_tab
        return None
    
    def send_chat_message(self, message: str, ai: str = "Both AIs") -> Dict[str, Any]:
        """Send a message to the AI chat."""
        tab = self._get_current_chat_tab()
        if not tab:
            return {"error": "No chat tab is currently active"}
        
        # Set the AI selector
        if ai in ["Both AIs", "AI 1", "AI 2"]:
            tab.ai_selector.setCurrentText(ai)
        
        # Set the message
        tab.message_input.setText(message)
        
        # Send the message
        tab.send_message()
        
        # Wait for AI responses
        time.sleep(1.5)
        
        # Get all messages
        messages = []
        for i in range(tab.chat_layout.count()):
            widget = tab.chat_layout.itemAt(i).widget()
            if widget:
                # Extract sender and message from the widget
                sender_label = widget.findChild(QLabel)
                if sender_label:
                    sender = sender_label.text().replace("<b>", "").replace("</b>", "")
                    
                message_label = None
                for child in widget.findChildren(QLabel):
                    if child != sender_label:
                        message_label = child
                        break
                
                if message_label:
                    message_text = message_label.text()
                    messages.append({
                        "sender": sender,
                        "message": message_text
                    })
        
        result = {
            "sent_message": message,
            "ai": ai,
            "messages": messages
        }
        
        self.trigger_callback("chat_message_sent", result)
        return result


# Global controller instance
_controller = None

def get_controller(browser_window=None):
    """Get the global controller instance."""
    global _controller
    if _controller is None and browser_window is not None:
        # Create a new controller instance
        _controller = BrowserController(browser_window)
    return _controller

def execute_script_file(script_file, browser_window=None):
    """Execute a JavaScript file in the browser.
    
    Args:
        script_file: Path to the JavaScript file to execute
        browser_window: Optional browser window instance
        
    Returns:
        The result of the script execution
    """
    # Get the controller
    controller = get_controller(browser_window)
    if controller is None:
        print("Error: Browser controller not available")
        return None
    
    # Read the script file
    try:
        with open(script_file, 'r') as f:
            script = f.read()
    except Exception as e:
        print(f"Error reading script file: {str(e)}")
        return None
    
    # Create a new browser tab
    tab = controller.create_tab("browser")
    tab_index = tab.get("tab_index")
    
    # Switch to the new tab
    controller.switch_to_tab(tab_index)
    
    # Execute the script
    return controller._execute_js(script)