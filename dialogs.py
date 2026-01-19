try:
    from qt.core import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTextBrowser, QTextEdit, QPushButton, QSplitter, QWidget, Qt)
except ImportError:
    from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTextBrowser, QTextEdit, QPushButton, QSplitter, QWidget)
    from PyQt5.QtCore import Qt

class ReviewDialog(QDialog):
    def __init__(self, parent, book_title, old_summary, new_summary):
        super().__init__(parent)
        self.setWindowTitle(f"Review Summary: {book_title}")
        self.resize(1000, 600)
        
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        # Splitter for Side-by-Side
        splitter = QSplitter(Qt.Horizontal)
        
        # Left: Old
        left_widget = QWidget()
        l_layout = QVBoxLayout()
        left_widget.setLayout(l_layout)
        l_layout.addWidget(QLabel("<b>Current Summary</b>"))
        self.old_view = QTextBrowser()
        self.old_view.setMinimumHeight(400)
        self.old_view.setHtml(old_summary if old_summary else "<i>No existing summary.</i>")
        l_layout.addWidget(self.old_view)
        
        # Right: New (Editable)
        right_widget = QWidget()
        r_layout = QVBoxLayout()
        right_widget.setLayout(r_layout)
        r_layout.addWidget(QLabel("<b>New AI Summary (Editable)</b>"))
        self.new_view = QTextEdit()
        self.new_view.setMinimumHeight(400)
        self.new_view.setHtml(new_summary)
        r_layout.addWidget(self.new_view)
        
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        self.layout.addWidget(splitter)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.status_label = QLabel("")
        btn_layout.addWidget(self.status_label)
        btn_layout.addStretch()
        
        self.discard_btn = QPushButton("Discard")
        self.discard_btn.clicked.connect(self.reject)
        
        self.apply_btn = QPushButton("Apply to Book")
        self.apply_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(self.discard_btn)
        btn_layout.addWidget(self.apply_btn)
        
        self.layout.addLayout(btn_layout)

class BatchReviewDialog(QDialog):
    def __init__(self, parent, results_map):
        """
        :param results_map: Dict { book_id: {'title': str, 'content': str, 'old_content': str} }
        """
        super().__init__(parent)
        self.setWindowTitle(f"Review Summaries ({len(results_map)} books)")
        self.resize(1100, 700)
        self.results_map = results_map
        self.book_ids = list(results_map.keys())
        self.current_index = 0
        self.decisions = {} # { book_id: 'apply' | 'discard' } -> default 'apply'
        
        # Init decisions
        for bid in self.book_ids:
            self.decisions[bid] = 'apply'

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Top Navigation
        nav_layout = QHBoxLayout()
        self.prev_btn = QPushButton("<< Previous")
        self.prev_btn.clicked.connect(self.prev_book)
        self.next_btn = QPushButton("Next >>")
        self.next_btn.clicked.connect(self.next_book)
        self.counter_label = QLabel("1 / ?")
        self.counter_label.setAlignment(Qt.AlignCenter)
        
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.counter_label, 1)
        nav_layout.addWidget(self.next_btn)
        self.layout.addLayout(nav_layout)

        # Content Area (Reusing logic from ReviewDialog, but embedded)
        splitter = QSplitter(Qt.Horizontal)
        
        # Left: Old
        left_widget = QWidget()
        l_layout = QVBoxLayout()
        left_widget.setLayout(l_layout)
        l_layout.addWidget(QLabel("<b>Current Summary</b>"))
        self.old_view = QTextBrowser()
        self.old_view.setMinimumHeight(400)
        l_layout.addWidget(self.old_view)
        
        # Right: New (Editable)
        right_widget = QWidget()
        r_layout = QVBoxLayout()
        right_widget.setLayout(r_layout)
        r_layout.addWidget(QLabel("<b>New AI Summary (Editable)</b>"))
        self.new_view = QTextEdit()
        self.new_view.setMinimumHeight(400)
        r_layout.addWidget(self.new_view)
        
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        self.layout.addWidget(splitter)
        
        # Action Bar for Current Book
        action_layout = QHBoxLayout()
        action_layout.addWidget(QLabel("Action for this book:"))
        
        self.action_grp = QWidget()
        self.action_grp_layout = QHBoxLayout()
        self.action_grp.setLayout(self.action_grp_layout)
        
        self.apply_chk = QPushButton("Keep New Summary (Apply)")
        self.apply_chk.setCheckable(True)
        self.apply_chk.clicked.connect(lambda: self.set_decision('apply'))
        
        self.discard_chk = QPushButton("Discard Change")
        self.discard_chk.setCheckable(True)
        self.discard_chk.clicked.connect(lambda: self.set_decision('discard'))
        
        self.action_grp_layout.addWidget(self.apply_chk)
        self.action_grp_layout.addWidget(self.discard_chk)
        
        action_layout.addWidget(self.action_grp)
        action_layout.addStretch()
        self.layout.addLayout(action_layout)
        
        # Bottom Global Buttons
        self.layout.addStretch()
        bbox = QHBoxLayout()
        self.save_all_btn = QPushButton(f"Process All")
        self.save_all_btn.clicked.connect(self.accept)
        bbox.addStretch()
        bbox.addWidget(self.save_all_btn)
        self.layout.addLayout(bbox)
        
        self.update_view()

    def update_view(self):
        book_id = self.book_ids[self.current_index]
        data = self.results_map[book_id]
        
        self.setWindowTitle(f"Review: {data['title']}")
        self.counter_label.setText(f"{self.current_index + 1} / {len(self.book_ids)}")
        
        self.old_view.setHtml(data['old_content'] if data['old_content'] else "<i>No existing summary.</i>")
        self.new_view.setHtml(data['content'])
        
        # Update buttons state
        current_decision = self.decisions[book_id]
        if current_decision == 'apply':
            self.apply_chk.setChecked(True)
            self.apply_chk.setStyleSheet("background-color: #c8e6c9;") # Light Green
            self.discard_chk.setChecked(False)
            self.discard_chk.setStyleSheet("")
        else:
            self.apply_chk.setChecked(False)
            self.apply_chk.setStyleSheet("")
            self.discard_chk.setChecked(True)
            self.discard_chk.setStyleSheet("background-color: #ffcdd2;") # Light Red
            
        self.prev_btn.setEnabled(self.current_index > 0)
        self.next_btn.setEnabled(self.current_index < len(self.book_ids) - 1)

    def next_book(self):
        if self.current_index < len(self.book_ids) - 1:
            self.current_index += 1
            self.update_view()

    def prev_book(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.update_view()

    def set_decision(self, decision):
        book_id = self.book_ids[self.current_index]
        self.decisions[book_id] = decision
        self.update_view()
