from calibre.gui2.actions import InterfaceAction
from calibre.gui2 import error_dialog

class SmartSummaryProAction(InterfaceAction):
    name = 'SmartSummary Pro'
    action_spec = ('SmartSummary Pro', 'search',
                   'Generate deep summaries for selected books', None)
    
    def genesis(self):
        self.qaction.triggered.connect(self.show_dialog)

    def library_view_context_menu(self, menu, rows):
        if len(rows) > 0:
            menu.addAction(self.qaction)

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
