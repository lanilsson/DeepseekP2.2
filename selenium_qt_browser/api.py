"""
API Module - Implements backend API for controlling the browser and terminal

This module provides a programmatic interface for controlling web pages and terminals,
retrieving webpage information, and executing commands.
"""

import os
import json
import time
from typing import Dict, List, Any, Optional, Tuple, Union
from enum import Enum

from PyQt6.QtCore import QObject, pyqtSignal, QTimer, Qt, QEventLoop
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWebEngineCore import QWebEngineScript

from selenium_qt_browser.browser import BrowserWindow, TabType, BrowserTab


class ElementType(Enum):
    """Types of HTML elements that can be interacted with."""
    BUTTON = "button"
    LINK = "a"
    INPUT = "input"
    TEXTAREA = "textarea"
    SELECT = "select"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    DIV = "div"
    SPAN = "span"
    IMAGE = "img"
    OTHER = "other"


class WebElement:
    """Represents a web element with its properties."""
    
    def __init__(self, element_id: str, element_type: ElementType, text: str, 
                 attributes: Dict[str, str], position: Tuple[int, int], 
                 size: Tuple[int, int], is_visible: bool):
        self.id = element_id
        self.type = element_type
        self.text = text
        self.attributes = attributes
        self.position = position
        self.size = size
        self.is_visible = is_visible
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the element to a dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "text": self.text,
            "attributes": self.attributes,
            "position": self.position,
            "size": self.size,
            "is_visible": self.is_visible
        }


class BrowserAPI:
    """API for controlling the browser and retrieving webpage information."""
    
    def __init__(self, browser_window: BrowserWindow):
        self.browser_window = browser_window
        self.last_response = {}
        
        # JavaScript for extracting page information
        self.extract_elements_script = """
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
    
    def _get_current_browser_tab(self) -> Optional[BrowserTab]:
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
        
        result = self._execute_js(self.extract_elements_script)
        if not result:
            return {"error": "Failed to extract page information"}
        
        # Process elements
        elements = []
        for elem_data in result.get("elements", []):
            element_type = ElementType.OTHER
            tag_name = elem_data.get("tagName", "").lower()
            elem_type = elem_data.get("type", "").lower()
            
            if tag_name == "button" or elem_data.get("attributes", {}).get("role") == "button":
                element_type = ElementType.BUTTON
            elif tag_name == "a":
                element_type = ElementType.LINK
            elif tag_name == "input":
                if elem_type in ["checkbox"]:
                    element_type = ElementType.CHECKBOX
                elif elem_type in ["radio"]:
                    element_type = ElementType.RADIO
                else:
                    element_type = ElementType.INPUT
            elif tag_name == "textarea":
                element_type = ElementType.TEXTAREA
            elif tag_name == "select":
                element_type = ElementType.SELECT
            elif tag_name == "div":
                element_type = ElementType.DIV
            elif tag_name == "span":
                element_type = ElementType.SPAN
            elif tag_name == "img":
                element_type = ElementType.IMAGE
            
            element = WebElement(
                element_id=elem_data.get("id", ""),
                element_type=element_type,
                text=elem_data.get("text", ""),
                attributes=elem_data.get("attributes", {}),
                position=tuple(elem_data.get("position", [0, 0])),
                size=tuple(elem_data.get("size", [0, 0])),
                is_visible=elem_data.get("isVisible", False)
            )
            elements.append(element.to_dict())
        
        page_info = result.get("pageInfo", {})
        
        response = {
            "title": page_info.get("title", ""),
            "url": page_info.get("url", ""),
            "elements": elements
        }
        
        self.last_response = response
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
            return self.get_page_info()
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
            return self.get_page_info()
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
        
        return self.get_page_info()
    
    def go_back(self) -> Dict[str, Any]:
        """Navigate back in history."""
        tab = self._get_current_browser_tab()
        if not tab:
            return {"error": "No browser tab is currently active"}
        
        tab.web_view.back()
        
        # Wait for page to load
        time.sleep(1)
        
        return self.get_page_info()
    
    def go_forward(self) -> Dict[str, Any]:
        """Navigate forward in history."""
        tab = self._get_current_browser_tab()
        if not tab:
            return {"error": "No browser tab is currently active"}
        
        tab.web_view.forward()
        
        # Wait for page to load
        time.sleep(1)
        
        return self.get_page_info()
    
    def refresh(self) -> Dict[str, Any]:
        """Refresh the current page."""
        tab = self._get_current_browser_tab()
        if not tab:
            return {"error": "No browser tab is currently active"}
        
        tab.web_view.reload()
        
        # Wait for page to load
        time.sleep(1)
        
        return self.get_page_info()


class TerminalAPI:
    """API for controlling the terminal and retrieving terminal output."""
    
    def __init__(self, browser_window: BrowserWindow):
        self.browser_window = browser_window
        self.last_output = ""
    
    def _get_current_terminal_tab(self):
        """Get the current terminal tab if it's a terminal tab."""
        current_tab = self.browser_window.current_tab()
        if hasattr(current_tab, 'tab_type') and current_tab.tab_type == TabType.TERMINAL:
            return current_tab
        return None
    
    def execute_command(self, command: str) -> Dict[str, Any]:
        """Execute a command in the terminal."""
        tab = self._get_current_terminal_tab()
        if not tab:
            return {"error": "No terminal tab is currently active"}
        
        # Clear the previous output
        previous_output = tab.terminal_output.toPlainText()
        
        # Execute the command
        tab.execute_command(command)
        
        # Wait for command to complete and output to be updated
        # This is a simple approach - in a real implementation, you might want to
        # use signals/slots to wait for the command to complete
        time.sleep(0.5)
        
        # Get the new output
        current_output = tab.terminal_output.toPlainText()
        
        # Extract only the new output
        if current_output.startswith(previous_output):
            new_output = current_output[len(previous_output):].strip()
        else:
            new_output = current_output
        
        self.last_output = new_output
        
        return {
            "command": command,
            "output": new_output
        }
    
    def get_current_directory(self) -> Dict[str, Any]:
        """Get the current working directory of the terminal."""
        tab = self._get_current_terminal_tab()
        if not tab:
            return {"error": "No terminal tab is currently active"}
        
        # Execute pwd command
        result = self.execute_command("pwd")
        
        if "error" in result:
            return result
        
        return {
            "current_directory": result["output"].strip()
        }


class ChatAPI:
    """API for interacting with the AI chat."""
    
    def __init__(self, browser_window: BrowserWindow):
        self.browser_window = browser_window
    
    def _get_current_chat_tab(self):
        """Get the current chat tab if it's a chat tab."""
        current_tab = self.browser_window.current_tab()
        if hasattr(current_tab, 'tab_type') and current_tab.tab_type == TabType.CHAT:
            return current_tab
        return None
    
    def send_message(self, message: str, ai: str = "Both AIs") -> Dict[str, Any]:
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
        
        return {
            "sent_message": message,
            "ai": ai,
            "messages": messages
        }


class BrowserController:
    """Main controller for the browser API."""
    
    def __init__(self, browser_window: BrowserWindow):
        self.browser_window = browser_window
        self.browser_api = BrowserAPI(browser_window)
        self.terminal_api = TerminalAPI(browser_window)
        self.chat_api = ChatAPI(browser_window)
    
    def switch_to_tab(self, tab_index: int) -> Dict[str, Any]:
        """Switch to a specific tab."""
        if tab_index < 0 or tab_index >= self.browser_window.tab_widget.count():
            return {"error": f"Tab index {tab_index} out of range"}
        
        self.browser_window.tab_widget.setCurrentIndex(tab_index)
        
        current_tab = self.browser_window.current_tab()
        tab_type = "unknown"
        
        if hasattr(current_tab, 'tab_type'):
            tab_type = current_tab.tab_type.name
        
        return {
            "tab_index": tab_index,
            "tab_type": tab_type
        }
    
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
    
    def create_tab(self, tab_type: str) -> Dict[str, Any]:
        """Create a new tab of the specified type."""
        if tab_type.lower() == "browser":
            tab = self.browser_window.add_new_tab()
            return {"tab_index": self.browser_window.tab_widget.indexOf(tab), "tab_type": "BROWSER"}
        elif tab_type.lower() == "chat":
            tab = self.browser_window.add_new_chat_tab()
            return {"tab_index": self.browser_window.tab_widget.indexOf(tab), "tab_type": "CHAT"}
        elif tab_type.lower() == "terminal":
            tab = self.browser_window.add_new_terminal_tab()
            return {"tab_index": self.browser_window.tab_widget.indexOf(tab), "tab_type": "TERMINAL"}
        else:
            return {"error": f"Unknown tab type: {tab_type}"}
    
    def close_tab(self, tab_index: int) -> Dict[str, Any]:
        """Close a specific tab."""
        if tab_index < 0 or tab_index >= self.browser_window.tab_widget.count():
            return {"error": f"Tab index {tab_index} out of range"}
        
        self.browser_window.close_tab(tab_index)
        
        return {
            "closed_tab_index": tab_index,
            "remaining_tabs": self.browser_window.tab_widget.count()
        }
    
    def execute_browser_command(self, command: str, **kwargs) -> Dict[str, Any]:
        """Execute a browser command."""
        if command == "get_page_info":
            return self.browser_api.get_page_info()
        elif command == "click_element":
            return self.browser_api.click_element(**kwargs)
        elif command == "fill_input":
            return self.browser_api.fill_input(**kwargs)
        elif command == "navigate":
            return self.browser_api.navigate(**kwargs)
        elif command == "go_back":
            return self.browser_api.go_back()
        elif command == "go_forward":
            return self.browser_api.go_forward()
        elif command == "refresh":
            return self.browser_api.refresh()
        else:
            return {"error": f"Unknown browser command: {command}"}
    
    def execute_terminal_command(self, command: str, **kwargs) -> Dict[str, Any]:
        """Execute a terminal command."""
        if command == "execute_command":
            return self.terminal_api.execute_command(**kwargs)
        elif command == "get_current_directory":
            return self.terminal_api.get_current_directory()
        else:
            return {"error": f"Unknown terminal command: {command}"}
    
    def execute_chat_command(self, command: str, **kwargs) -> Dict[str, Any]:
        """Execute a chat command."""
        if command == "send_message":
            return self.chat_api.send_message(**kwargs)
        else:
            return {"error": f"Unknown chat command: {command}"}
    
    def execute_command(self, command_type: str, command: str, **kwargs) -> Dict[str, Any]:
        """Execute a command of the specified type."""
        if command_type == "browser":
            return self.execute_browser_command(command, **kwargs)
        elif command_type == "terminal":
            return self.execute_terminal_command(command, **kwargs)
        elif command_type == "chat":
            return self.execute_chat_command(command, **kwargs)
        elif command_type == "tab":
            if command == "switch":
                return self.switch_to_tab(kwargs.get("tab_index", 0))
            elif command == "create":
                return self.create_tab(kwargs.get("tab_type", "browser"))
            elif command == "close":
                return self.close_tab(kwargs.get("tab_index", 0))
            elif command == "get_info":
                return self.get_tabs_info()
            else:
                return {"error": f"Unknown tab command: {command}"}
        else:
            return {"error": f"Unknown command type: {command_type}"}