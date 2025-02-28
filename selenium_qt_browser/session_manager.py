"""
Session Manager Module - Implements session management functionality

This module contains the SessionManager class which provides functionality
for saving and loading the last browser session, including chat logs, browsing history,
and notes.
"""

import os
import json
import datetime
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal

class SessionManager(QObject):
    """Manages saving and loading of the last browser session."""
    
    session_loaded = pyqtSignal(str)  # Signal emitted when a session is loaded
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.sessions_dir = Path.home() / ".selenium_qt_browser" / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.last_session_dir = self.sessions_dir / "last_session"
        self.last_session_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.last_session_dir / "chat_logs").mkdir(exist_ok=True)
        (self.last_session_dir / "notes").mkdir(exist_ok=True)
        (self.last_session_dir / "history").mkdir(exist_ok=True)
    
    def save_session(self, browser_window):
        """Save the current session."""
        # Save session data
        self._save_tabs(browser_window)
        self._save_chat_logs(browser_window)
        self._save_notes(browser_window)
        self._save_history(browser_window)
        
        # Update metadata
        self._update_metadata(browser_window)
        
        return True
    
    def load_last_session(self, browser_window):
        """Load the last session if it exists."""
        tabs_file = self.last_session_dir / "tabs.json"
        if not tabs_file.exists():
            return False
        
        try:
            self._load_tabs(browser_window)
            self._load_chat_logs(browser_window)
            self._load_notes(browser_window)
            self._load_history(browser_window)
            
            self.session_loaded.emit("last_session")
            return True
        except Exception as e:
            print(f"Error loading last session: {e}")
            return False
    
    def _save_tabs(self, browser_window):
        """Save the open tabs."""
        tabs = []
        
        # Iterate through all tabs
        for i in range(browser_window.tab_widget.count()):
            tab = browser_window.tab_widget.widget(i)
            tab_data = {
                "index": i,
                "title": browser_window.tab_widget.tabText(i)
            }
            
            # Save tab-specific data based on type
            if hasattr(tab, "tab_type"):
                tab_data["type"] = tab.tab_type.name
                
                if tab.tab_type.name == "BROWSER":
                    tab_data["url"] = tab.current_url()
                elif tab.tab_type.name == "NOTEPAGE":
                    # For NotePage, save the content to a separate file
                    note_file = f"note_{i}.txt"
                    with open(self.last_session_dir / "notes" / note_file, "w") as f:
                        f.write(tab.text_editor.toPlainText())
                    tab_data["note_file"] = note_file
                elif tab.tab_type.name == "NOTEPAGE_EXC":
                    # For NotePageExc, save the spreadsheet data to a separate file
                    sheet_file = f"sheet_{i}.json"
                    with open(self.last_session_dir / "notes" / sheet_file, "w") as f:
                        json.dump(tab.spreadsheet_model.data, f)
                    tab_data["sheet_file"] = sheet_file
            
            tabs.append(tab_data)
        
        # Save tabs data
        with open(self.last_session_dir / "tabs.json", "w") as f:
            json.dump(tabs, f, indent=2)
    
    def _save_chat_logs(self, browser_window):
        """Save the chat logs."""
        chat_logs = []
        
        # Iterate through all tabs to find chat tabs
        for i in range(browser_window.tab_widget.count()):
            tab = browser_window.tab_widget.widget(i)
            
            if hasattr(tab, "tab_type") and tab.tab_type.name == "CHAT":
                # Extract chat messages
                messages = []
                
                # This assumes the chat tab has a chat_layout with message widgets
                if hasattr(tab, "chat_layout"):
                    for j in range(tab.chat_layout.count()):
                        widget = tab.chat_layout.itemAt(j).widget()
                        if hasattr(widget, "sender_label") and hasattr(widget, "message_label"):
                            messages.append({
                                "sender": widget.sender_label.text(),
                                "message": widget.message_label.text(),
                                "timestamp": widget.timestamp.text()
                            })
                
                chat_logs.append({
                    "tab_index": i,
                    "messages": messages
                })
        
        # Save chat logs
        with open(self.last_session_dir / "chat_logs" / "chats.json", "w") as f:
            json.dump(chat_logs, f, indent=2)
    
    def _save_notes(self, browser_window):
        """Save the notes."""
        # Notes are saved in _save_tabs
        pass
    
    def _save_history(self, browser_window):
        """Save the browsing history."""
        history = []
        
        # Iterate through all tabs to find browser tabs
        for i in range(browser_window.tab_widget.count()):
            tab = browser_window.tab_widget.widget(i)
            
            if hasattr(tab, "tab_type") and tab.tab_type.name == "BROWSER":
                # Add current URL to history
                history.append({
                    "url": tab.current_url(),
                    "title": browser_window.tab_widget.tabText(i),
                    "timestamp": datetime.datetime.now().isoformat()
                })
        
        # Save history
        history_file = self.last_session_dir / "history" / "history.json"
        
        # Append to existing history if file exists
        if history_file.exists():
            try:
                with open(history_file, "r") as f:
                    existing_history = json.load(f)
                history = existing_history + history
            except Exception as e:
                print(f"Error loading existing history: {e}")
        
        with open(history_file, "w") as f:
            json.dump(history, f, indent=2)
    
    def _update_metadata(self, browser_window):
        """Update the session metadata."""
        metadata_file = self.last_session_dir / "metadata.json"
        
        try:
            with open(metadata_file, "r") as f:
                metadata = json.load(f)
        except Exception:
            # Create new metadata if file doesn't exist or is invalid
            metadata = {
                "name": "Last Session",
                "created": datetime.datetime.now().isoformat()
            }
        
        # Update metadata
        metadata["updated"] = datetime.datetime.now().isoformat()
        metadata["timestamp"] = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        metadata["tab_count"] = browser_window.tab_widget.count()
        
        # Count tab types
        tab_types = {}
        for i in range(browser_window.tab_widget.count()):
            tab = browser_window.tab_widget.widget(i)
            if hasattr(tab, "tab_type"):
                tab_type = tab.tab_type.name
                tab_types[tab_type] = tab_types.get(tab_type, 0) + 1
        
        metadata["tab_types"] = tab_types
        
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)
    
    def _load_tabs(self, browser_window):
        """Load the tabs from the last session."""
        tabs_file = self.last_session_dir / "tabs.json"
        if not tabs_file.exists():
            return
        
        try:
            with open(tabs_file, "r") as f:
                tabs_data = json.load(f)
            
            # Close all existing tabs
            while browser_window.tab_widget.count() > 0:
                browser_window.close_tab(0)
            
            # Create new tabs based on saved data
            for tab_data in tabs_data:
                tab_type = tab_data.get("type")
                
                if tab_type == "BROWSER":
                    tab = browser_window.add_new_tab(tab_data.get("url"))
                elif tab_type == "CHAT":
                    tab = browser_window.add_new_chat_tab()
                elif tab_type == "TERMINAL":
                    tab = browser_window.add_new_terminal_tab()
                elif tab_type == "NOTEPAGE":
                    tab = browser_window.add_new_notepage_tab()
                    # Load note content
                    note_file = tab_data.get("note_file")
                    if note_file:
                        note_path = self.last_session_dir / "notes" / note_file
                        if note_path.exists():
                            with open(note_path, "r") as f:
                                tab.text_editor.setPlainText(f.read())
                elif tab_type == "NOTEPAGE_EXC":
                    tab = browser_window.add_new_notepage_exc_tab()
                    # Load spreadsheet data
                    sheet_file = tab_data.get("sheet_file")
                    if sheet_file:
                        sheet_path = self.last_session_dir / "notes" / sheet_file
                        if sheet_path.exists():
                            with open(sheet_path, "r") as f:
                                # Convert string keys back to tuple keys
                                data = json.load(f)
                                converted_data = {}
                                for k, v in data.items():
                                    # Convert string key like "(0,1)" to tuple (0,1)
                                    if k.startswith("(") and k.endswith(")"):
                                        parts = k[1:-1].split(",")
                                        if len(parts) == 2:
                                            try:
                                                key = (int(parts[0]), int(parts[1]))
                                                converted_data[key] = v
                                            except ValueError:
                                                converted_data[k] = v
                                    else:
                                        converted_data[k] = v
                                tab.spreadsheet_model.data = converted_data
                                tab.spreadsheet_model.layoutChanged.emit()
        except Exception as e:
            print(f"Error loading tabs: {e}")
            raise
    
    def _load_chat_logs(self, browser_window):
        """Load the chat logs from the last session."""
        chat_logs_file = self.last_session_dir / "chat_logs" / "chats.json"
        if not chat_logs_file.exists():
            return
        
        try:
            with open(chat_logs_file, "r") as f:
                chat_logs = json.load(f)
            
            # Find chat tabs and populate with messages
            for chat_log in chat_logs:
                tab_index = chat_log.get("tab_index")
                messages = chat_log.get("messages", [])
                
                # Find or create a chat tab
                chat_tab = None
                
                # Check if there's already a chat tab at this index
                if tab_index < browser_window.tab_widget.count():
                    tab = browser_window.tab_widget.widget(tab_index)
                    if hasattr(tab, "tab_type") and tab.tab_type.name == "CHAT":
                        chat_tab = tab
                
                # If no chat tab found, create a new one
                if not chat_tab:
                    chat_tab = browser_window.add_new_chat_tab()
                
                # Clear existing messages
                if hasattr(chat_tab, "chat_layout"):
                    while chat_tab.chat_layout.count() > 0:
                        item = chat_tab.chat_layout.takeAt(0)
                        if item.widget():
                            item.widget().deleteLater()
                
                # Add messages
                for message in messages:
                    chat_tab.add_message(
                        message.get("sender", "Unknown"),
                        message.get("message", "")
                    )
        except Exception as e:
            print(f"Error loading chat logs: {e}")
    
    def _load_notes(self, browser_window):
        """Load the notes from the last session."""
        # Notes are loaded in _load_tabs
        pass
    
    def _load_history(self, browser_window):
        """Load the browsing history from the last session."""
        # History is loaded in _load_tabs (for open tabs)
        # We could also populate a history menu/list here if needed
        pass