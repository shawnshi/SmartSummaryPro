from calibre.gui2.actions import InterfaceAction
from calibre.gui2 import error_dialog

class SmartSummaryProAction(InterfaceAction):
    name = 'SmartSummary Pro'
    action_spec = ('SmartSummary Pro', 'search',
                   'Generate deep summaries for selected books', None)
    
    def show_dialog(self):
        rows = self.gui.library_view.selectionModel().selectedRows()
        if not rows:
            error_dialog(self.gui, 'No Selection',
                         'Please select at least one book to generate a summary.',
                         show=True)
            return

        # Confirm action
        from qt.core import QMessageBox
        book_ids = list(map(self.gui.library_view.model().id, rows))
        count = len(book_ids)
        
        # Check if API configured
        from calibre_plugins.smart_summary_pro.config import prefs
        if not prefs.get('api_configs'):
            error_dialog(self.gui, 'No API Configured',
                         'Please go to Preferences -> Plugins -> SmartSummary Pro and configure at least one AI model.',
                         show=True)
            return

        if not QMessageBox.question(self.gui, "Generate Summaries", 
                                    f"Generate deep summaries for {count} books?", 
                                    QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            return

        # Dispatch Job
        from calibre_plugins.smart_summary_pro.worker import GenerationWorker
        # Pass the prompt template from prefs
        template = prefs.get('prompt_template')
        
        worker = GenerationWorker(self.gui, book_ids, template)
        
        self.gui.job_manager.run_threaded_job(worker)
        # Connect signals for completion
        worker.notification.connect(self.job_completed)

    def job_completed(self, notification):
        # Notification is just a signal, we need the job result.
        # But ThreadedJob usage in Calibre is tricky. 
        # Usually we pass a "done" callback to run_threaded_job?
        # Actually in modern Calibre plugins, job_manager handles it.
        # Let's adjust: ThreadedJob typically doesn't return value via callback easily unless we use custom signal.
        # But let's check `worker.results` directly if the job object is passed back?
        # Calibre's job manager usually keeps the job alive? 
        # Actually, simpler pattern:
        # Pass `self.job_done` as argument to `run_threaded_job`?
        # Checking Calibre source: run_threaded_job(job, notification=cls.job_done)
        pass 
        # Wait, I need to restructure show_dialog to pass the callback.

    def genesis(self):
        self.qaction.triggered.connect(self.show_dialog)

    # Re-implementing show_dialog to pass callback correctly
    def show_dialog(self):
        rows = self.gui.library_view.selectionModel().selectedRows()
        if not rows: return
        book_ids = list(map(self.gui.library_view.model().id, rows))
        
        from .config import prefs
        if not prefs.get('api_configs'):
             error_dialog(self.gui, 'No API Configured', 'Please configure an AI model first.', show=True)
             return

        from .worker import GenerationWorker
        template = prefs.get('prompt_template')
        job = GenerationWorker(self.gui, book_ids, template)
        
        # Run background job
        self.gui.job_manager.run_threaded_job(job, notification=self.job_finished)

    def job_finished(self, job):
        # job is the GenerationWorker instance
        if job.failed:
            self.gui.job_exception(job, dialog_title='Generation Failed')
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
            self.gui.status_bar.show_message(f"Generation complete. Success: {success_count}, Failed: {error_count}", 5000)
        
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
            
            self.gui.status_bar.show_message(f"Updated summaries for {applied_count} books.", 3000)
            self.gui.library_view.model().refresh_ids(list(review_map.keys()))



