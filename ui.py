from calibre.gui2.actions import InterfaceAction
from calibre.gui2 import error_dialog

class SmartSummaryProAction(InterfaceAction):
    name = 'SmartSummary Pro'
    action_spec = ('SmartSummary Pro', 'images/icon.png',
                   'Generate deep summaries for selected books', None)
    
    def genesis(self):
        self.qaction.triggered.connect(self.show_dialog)
        print("SmartSummary Pro: genesis called")

    def initialization_complete(self):
        print("SmartSummary Pro: initialization_complete called")
        self.add_to_menu_bar()

    def add_to_menu_bar(self):
        try:
            # Attempt to add to the main menu bar to ensure visibility
            mw = self.gui
            menubar = mw.menuBar()

            # Check if "SmartSummary" menu already exists to avoid duplication
            # This is a simple check based on title
            found_menu = None
            for action in menubar.actions():
                if action.text() == "SmartSummary":
                    found_menu = action.menu()
                    break

            if found_menu:
                self.main_menu = found_menu
            else:
                self.main_menu = menubar.addMenu("SmartSummary")

            # Add our action to the menu
            self.main_menu.addAction(self.qaction)
        except Exception as e:
            print(f"SmartSummary Pro: Failed to add to menu bar: {e}")

    def library_view_context_menu(self, menu, rows):
        if len(rows) > 0:
            menu.addAction(self.qaction)

    def show_dialog(self):
        base_plugin_object = self.interface_action_base_plugin
        do_user_config = base_plugin_object.do_user_config
        rows = self.gui.library_view.selectionModel().selectedRows()
        if not rows: return
        book_ids = list(map(self.gui.library_view.model().id, rows))
        
        from .config import prefs
        if not prefs.get('api_configs'):
             error_dialog(self.gui, 'No API Configured', 'Please configure an AI model first.', show=True)
             return

        from .worker import GenerationWorker
        system_prompt = prefs.get('system_prompt')
        user_prompt = prefs.get('user_prompt')
        job = GenerationWorker(self.gui, book_ids, system_prompt, user_prompt)
        
        # Run background job using threading instead of JobManager
        # This avoids compatibility issues with different Calibre versions
        import threading
        
        def run_in_background():
            try:
                job()  # Execute the callable
            except Exception as e:
                job.failed = True
                job.results['fatal_error'] = str(e)
        
        # Start thread
        thread = threading.Thread(target=run_in_background, daemon=True)
        thread.start()
        
        # Monitor completion using QTimer
        try:
            from qt.core import QTimer
        except ImportError:
            from PyQt5.QtCore import QTimer
        
        def check_completion():
            if thread.is_alive():
                # Still running, check again later
                QTimer.singleShot(500, check_completion)
            else:
                # Job finished, process results
                self.job_finished(job)
        
        # Start monitoring
        QTimer.singleShot(500, check_completion)
        
        # Show status message
        self.gui.status_bar.showMessage(f"Generating summaries for {len(book_ids)} book(s)...", 3000)

    def job_finished(self, job):
        # job is the GenerationWorker instance
        if job.failed:
            error_msg = job.results.get('fatal_error', 'Unknown error')
            error_dialog(self.gui, 'Generation Failed', error_msg, show=True)
            return

        results = job.results
        if 'fatal_error' in results:
             error_dialog(self.gui, 'Generation Error', results['fatal_error'], show=True)
             return

        # Process results
        from .dialogs import BatchReviewDialog
        
        # Build map for dialog { book_id: {'title':..., 'content':..., 'old_content':...} }
        review_map = {}
        db = self.gui.current_db
        
        error_count = 0
        success_count = 0
        
        for book_id, res in results.items():
            if not isinstance(book_id, int): continue
            
            if not res['success']:
                print(f"Failed for {book_id}: {res['error']}")
                error_count += 1
                continue
            
            success_count += 1
            mi = db.get_metadata(book_id, index_is_id=True)
            review_map[book_id] = {
                'title': res['title'],
                'content': res['content'],
                'old_content': mi.comments
            }
        
        if error_count > 0:
            self.gui.status_bar.showMessage(f"Generation complete. Success: {success_count}, Failed: {error_count}", 5000)
        
        if not review_map:
            if error_count > 0:
                error_dialog(self.gui, 'Generation Failed', 'All attempts failed. Check logs.', show=True)
            return

        # Show Batch Dialog
        dlg = BatchReviewDialog(self.gui, review_map)
        if dlg.exec_():
            # Apply decisions
            applied_count = 0
            decisions = dlg.decisions
            
            for book_id, decision in decisions.items():
                if decision == 'apply':
                    new_summary = review_map[book_id]['content']
                    mi = db.get_metadata(book_id, index_is_id=True)
                    mi.comments = new_summary
                    db.set_metadata(book_id, mi)
                    applied_count += 1
            
            self.gui.status_bar.showMessage(f"Updated summaries for {applied_count} books.", 3000)
            self.gui.library_view.model().refresh_ids(list(review_map.keys()))
