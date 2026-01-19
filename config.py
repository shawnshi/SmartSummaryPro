try:
    from qt.core import (QWidget, QVBoxLayout, QLabel, QTextEdit, QTabWidget, 
                         QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, 
                         QDialog, QFormLayout, QLineEdit, QComboBox, QMessageBox,
                         QAbstractItemView, QHeaderView, Qt)
except ImportError:
    # Fallback for very old Calibre or external testing
    from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTextEdit, QTabWidget, 
                                 QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, 
                                 QDialog, QFormLayout, QLineEdit, QComboBox, QMessageBox,
                                 QAbstractItemView, QHeaderView)
    from PyQt5.QtCore import Qt
from calibre.utils.config import JSONConfig

prefs = JSONConfig('plugins/SmartSummaryPro')

# Ensure defaults
if 'api_configs' not in prefs:
    prefs['api_configs'] = []
if 'max_tokens' not in prefs:
    prefs.defaults['max_tokens'] = 4096
if 'system_prompt' not in prefs:
    prefs.defaults['system_prompt'] = """You are a senior literary critic, book publisher, and cultural scholar. You specialize in in-depth analysis of books from multiple dimensions: macro historical context, meso literary value, and micro narrative techniques.
# Task
Based on the book information I provide, write an insightful, thoughtful, and engaging book introduction. This introduction should not merely be a plot summary or table of contents listing, but should reveal the core logic behind the book, its significance to the era, and its enlightenment to readers."""
if 'user_prompt' not in prefs:
    prefs.defaults['user_prompt'] = """# Book Information
Title: {title}
Authors: {authors}
Publisher: {publisher}
Publication Date: {pubdate}
Series: {series}

# Writing Framework
Please structure your writing as follows:
1. Opening: Era Background & Core Thesis - Briefly describe the historical/academic context in which this book was born and what core questions it attempts to answer.
2. Core Insights: Deep Thought Analysis - Analyze the book's core viewpoints, philosophical thinking, or narrative framework.
3. Author's Style & Unique Value - Evaluate the author's writing style and the book's unique/pioneering position among similar works.
4. Social Impact & Reading Significance - Discuss the value of this book for contemporary readers.

# Tone & Style
Tone: Professional, elegant, insightful. Avoid hollow marketing terms.
Word count: 500-800 words.
Output language: Please write in the same language as the book title."""

def obfuscate_key(key):
    # Simple XOR obfuscation to avoid plain text storage
    # Not high security, but prevents casual reading
    if not key: return ""
    chars = []
    secret = 42
    for c in key:
        chars.append(chr(ord(c) ^ secret))
    return "".join(chars)

def deobfuscate_key(key):
    return obfuscate_key(key) # XOR is symmetric

class ModelEditDialog(QDialog):
    def __init__(self, parent=None, model_data=None):
        super().__init__(parent)
        self.setWindowTitle("Configure AI Model")
        self.layout = QFormLayout()
        self.setLayout(self.layout)
        
        self.name_edit = QLineEdit(model_data.get('name', '') if model_data else '')
        self.provider_edit = QComboBox()
        self.provider_edit.addItems(["OpenAI", "DeepSeek", "Anthropic", "Gemini", "Custom"])
        self.provider_edit.currentTextChanged.connect(self.on_provider_changed)
        
        if model_data:
            self.provider_edit.setCurrentText(model_data.get('provider', 'OpenAI'))
            
        self.key_edit = QLineEdit()
        if model_data:
            enc_key = model_data.get('api_key', '')
            # Try to determine if key is raw or encrypted. 
            # For back-compat or Phase 1 keys, they might be plain.
            # Simple heuristic: if it starts with 'sk-' and is long, it's plain.
            # If it looks like garbage, might be encrypted.
            # Or better: we assume all keys in storage are encrypted from now on.
            try:
                dec = deobfuscate_key(enc_key)
                # Check if it looks valid? If not, maybe it was plain text.
                # Actually, self-correction: let's just use a prefix marker like "ENC:"
                if enc_key.startswith("ENC:"):
                    self.key_edit.setText(deobfuscate_key(enc_key[4:]))
                else:
                    self.key_edit.setText(enc_key) # Assume plain legacy
            except:
                self.key_edit.setText(enc_key)
        
        self.key_edit.setEchoMode(QLineEdit.Password)
        
        self.endpoint_edit = QLineEdit(model_data.get('endpoint', 'https://api.openai.com/v1/chat/completions') if model_data else 'https://api.openai.com/v1/chat/completions')
        self.model_name_edit = QLineEdit(model_data.get('model_name', 'gpt-3.5-turbo') if model_data else 'gpt-3.5-turbo')
        self.limit_edit = QLineEdit(str(model_data.get('daily_limit', 10)) if model_data else '10')

        self.layout.addRow("Friendly Name:", self.name_edit)
        self.layout.addRow("Provider:", self.provider_edit)
        self.layout.addRow("API Key:", self.key_edit)
        self.layout.addRow("Endpoint URL:", self.endpoint_edit)
        self.layout.addRow("Model String (e.g. gpt-4):", self.model_name_edit)
        self.layout.addRow("Daily Request Limit:", self.limit_edit)
        
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.accept)
    def on_provider_changed(self, provider):
        defaults = {
            "OpenAI": "https://api.openai.com/v1/chat/completions",
            "DeepSeek": "https://api.deepseek.com/chat/completions",
            "Gemini": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
        }
        
        # Only overwrite if current is empty or matches a known default
        current = self.endpoint_edit.text().strip()
        known_defaults = list(defaults.values()) + ["https://api.openai.com/v1/chat/completions"]
        
        if not current or current in known_defaults:
            if provider in defaults:
                self.endpoint_edit.setText(defaults[provider])

        self.layout.addRow(self.save_btn)

    def get_data(self):
        import uuid
        
        raw_key = self.key_edit.text()
        # Save as "ENC:" + obfuscated
        enc_key = "ENC:" + obfuscate_key(raw_key)
        
        return {
            'id': str(uuid.uuid4()), 
            'name': self.name_edit.text(),
            'provider': self.provider_edit.currentText(),
            'api_key': enc_key,
            'endpoint': self.endpoint_edit.text(),
            'model_name': self.model_name_edit.text(),
            'daily_limit': int(self.limit_edit.text())
        }

class ConfigWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)
        
        self.setup_models_tab()
        self.setup_prompt_tab()

    def setup_models_tab(self):
        self.models_tab = QWidget()
        l = QVBoxLayout()
        self.models_tab.setLayout(l)
        
        self.model_table = QTableWidget()
        self.model_table.setColumnCount(4)
        self.model_table.setHorizontalHeaderLabels(["Priority", "Name", "Provider", "Daily Limit"])
        
        # Handle PyQt6 compatibility for QHeaderView.Stretch
        # In PyQt6 it is QHeaderView.ResizeMode.Stretch, in PyQt5 it is QHeaderView.Stretch
        # Both map to integer 1 usually.
        try:
            stretch_mode = QHeaderView.Stretch
        except AttributeError:
             # Likely PyQt6
             try:
                 stretch_mode = QHeaderView.ResizeMode.Stretch
             except AttributeError:
                 # Fallback
                 stretch_mode = 1

        self.model_table.horizontalHeader().setSectionResizeMode(1, stretch_mode)
        self.model_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.model_table.setSelectionMode(QAbstractItemView.SingleSelection)
        l.addWidget(self.model_table)
        
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add Model")
        add_btn.clicked.connect(self.add_model)
        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self.edit_model)
        del_btn = QPushButton("Remove")
        del_btn.clicked.connect(self.delete_model)
        up_btn = QPushButton("Move Up")
        up_btn.clicked.connect(lambda: self.move_row(-1))
        down_btn = QPushButton("Move Down")
        down_btn.clicked.connect(lambda: self.move_row(1))
        
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addWidget(up_btn)
        btn_layout.addWidget(down_btn)
        l.addLayout(btn_layout)
        
        self.tabs.addTab(self.models_tab, "Model Management")
        self.refresh_table()

    def setup_prompt_tab(self):
        self.prompt_tab = QWidget()
        l = QVBoxLayout()
        self.prompt_tab.setLayout(l)
        
        # System Prompt (Role definition)
        l.addWidget(QLabel("<b>System Prompt</b> (AI role and task definition):"))
        self.system_prompt_edit = QTextEdit()
        self.system_prompt_edit.setPlainText(prefs.get('system_prompt', ''))
        self.system_prompt_edit.setMaximumHeight(150)
        l.addWidget(self.system_prompt_edit)
        
        # User Prompt (Book info template)
        l.addWidget(QLabel("<b>User Prompt</b> (Template with {title}, {authors}, {publisher}, {pubdate}, {series}):"))
        self.user_prompt_edit = QTextEdit()
        self.user_prompt_edit.setPlainText(prefs.get('user_prompt', ''))
        l.addWidget(self.user_prompt_edit)
        
        self.tabs.addTab(self.prompt_tab, "Prompt Template")

    def refresh_table(self):
        self.model_table.setRowCount(0)
        configs = prefs.get('api_configs', [])
        for i, conf in enumerate(configs):
            self.model_table.insertRow(i)
            self.model_table.setItem(i, 0, QTableWidgetItem(str(i+1)))
            self.model_table.setItem(i, 1, QTableWidgetItem(conf.get('name', '')))
            self.model_table.setItem(i, 2, QTableWidgetItem(conf.get('provider', '')))
            self.model_table.setItem(i, 3, QTableWidgetItem(str(conf.get('daily_limit', 0))))

    def add_model(self):
        dlg = ModelEditDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            new_data = dlg.get_data()
            configs = prefs.get('api_configs', [])
            configs.append(new_data)
            prefs['api_configs'] = configs
            self.refresh_table()

    def edit_model(self):
        row = self.model_table.currentRow()
        if row < 0: return
        configs = prefs.get('api_configs', [])
        data = configs[row]
        
        dlg = ModelEditDialog(self, data)
        if dlg.exec_() == QDialog.Accepted:
            updated_data = dlg.get_data()
            updated_data['id'] = data.get('id', updated_data['id']) # Preserve ID
            configs[row] = updated_data
            prefs['api_configs'] = configs
            self.refresh_table()

    def delete_model(self):
        row = self.model_table.currentRow()
        if row < 0: return
        configs = prefs.get('api_configs', [])
        del configs[row]
        prefs['api_configs'] = configs
        self.refresh_table()

    def move_row(self, direction):
        row = self.model_table.currentRow()
        if row < 0: return
        new_row = row + direction
        configs = prefs.get('api_configs', [])
        if 0 <= new_row < len(configs):
            configs[row], configs[new_row] = configs[new_row], configs[row]
            prefs['api_configs'] = configs
            self.refresh_table()
            self.model_table.selectRow(new_row)

    def save_settings(self):
        prefs['system_prompt'] = self.system_prompt_edit.toPlainText()
        prefs['user_prompt'] = self.user_prompt_edit.toPlainText()
