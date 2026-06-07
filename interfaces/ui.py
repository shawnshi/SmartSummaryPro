"""
@Input:  User Clicks, Selected Book IDs
@Output: Async Jobs Dispatch, Review Dialog Presentation
@Pos:    interfaces / ui.py. Primary Gateway.

!!! Maintenance Protocol: If logic, dependencies, or output change, 
!!! update this header AND the parent directory's _DIR_META.md.
"""
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
            mw = self.gui
            menubar = mw.menuBar()
            found_menu = None
            for action in menubar.actions():
                if action.text() == "SmartSummary":
                    found_menu = action.menu()
                    break

            if found_menu:
                self.main_menu = found_menu
            else:
                self.main_menu = menubar.addMenu("SmartSummary")

            self.main_menu.addAction(self.qaction)
        except Exception as e:
            print(f"SmartSummary Pro: Failed to add to menu bar: {e}")

    def library_view_context_menu(self, menu, rows):
        if len(rows) > 0:
            menu.addAction(self.qaction)

    def show_dialog(self):
        rows = self.gui.library_view.selectionModel().selectedRows()
        if not rows: return
        book_ids = list(map(self.gui.library_view.model().id, rows))
        
        from calibre_plugins.smart_summary_pro.core.config import prefs
        if not prefs.get('api_configs'):
             error_dialog(self.gui, 'No API Configured', 'Please configure an AI model first.', show=True)
             return

        # Pre-extract metadata on the main thread (Thread Safety Fix)
        db = self.gui.current_db
        metadata_map = {}
        for book_id in book_ids:
            mi = db.get_metadata(book_id, index_is_id=True)
            authors = ", ".join(mi.authors) if getattr(mi, 'authors', None) else "Unknown"
            metadata_map[book_id] = {
                'title': getattr(mi, 'title', "Unknown"),
                'authors': authors,
                'publisher': getattr(mi, 'publisher', "Unknown") or "Unknown",
                'pubdate': str(getattr(mi, 'pubdate', "Unknown")) if getattr(mi, 'pubdate', None) else "Unknown",
                'series': getattr(mi, 'series', "None") or "None"
            }

        from calibre_plugins.smart_summary_pro.modules.worker import GenerationWorker
        system_prompt = prefs.get('system_prompt')
        user_prompt = prefs.get('user_prompt')
        
        # Instantiate pure worker without GUI object
        job = GenerationWorker(book_ids, metadata_map, system_prompt, user_prompt)
        
        import threading
        def run_in_background():
            try:
                job()
            except Exception as e:
                job.failed = True
                job.results['fatal_error'] = str(e)
        
        thread = threading.Thread(target=run_in_background, daemon=True)
        thread.start()
        
        try:
            from qt.core import QTimer
        except ImportError:
            from PyQt5.QtCore import QTimer
        
        def check_completion():
            if thread.is_alive():
                # Report progress dynamically
                self.gui.status_bar.showMessage(f"Generating summaries: {job.completed_count} / {job.total_count} completed...", 1000)
                QTimer.singleShot(500, check_completion)
            else:
                self.gui.status_bar.clearMessage()
                self.job_finished(job)
        
        QTimer.singleShot(500, check_completion)
        self.gui.status_bar.showMessage(f"Starting generation for {len(book_ids)} book(s)...", 1000)

    def job_finished(self, job):
        if job.failed:
            error_msg = job.results.get('fatal_error', 'Unknown error')
            error_dialog(self.gui, 'Generation Failed', error_msg, show=True)
            return

        results = job.results
        if 'fatal_error' in results:
             error_dialog(self.gui, 'Generation Error', results['fatal_error'], show=True)
             return

        from calibre_plugins.smart_summary_pro.interfaces.dialogs import BatchReviewDialog
        review_map = {}
        db = self.gui.current_db
        
        error_count = 0
        success_count = 0
        
        for book_id, res in results.items():
            if not isinstance(book_id, int): continue
            
            if not res['success']:
                print(f"Failed for {book_id}: {res.get('error', '')}")
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

        dlg = BatchReviewDialog(self.gui, review_map)
        if dlg.exec_():
            applied_count = 0
            decisions = dlg.decisions
            val_map = {}
            
            for book_id, decision in decisions.items():
                if decision == 'apply':
                    val_map[book_id] = review_map[book_id]['content']
                    applied_count += 1
            
            if val_map:
                try:
                    # Bulk DB update to avoid I/O storm
                    db.new_api.set_field('comments', val_map)
                except AttributeError:
                    # Fallback for very old calibre
                    for bid, new_summary in val_map.items():
                        mi = db.get_metadata(bid, index_is_id=True)
                        mi.comments = new_summary
                        db.set_metadata(bid, mi)
            
            self.gui.status_bar.showMessage(f"Updated summaries for {applied_count} books.", 3000)
            self.gui.library_view.model().refresh_ids(list(review_map.keys()))
