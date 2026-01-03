from calibre.gui2.threaded import ThreadedJob
from .api_manager import APIManager

class GenerationWorker(ThreadedJob):
    def __init__(self, gui, book_ids, prompt_template):
        # Initialize generic job
        super().__init__(gui)
        self.book_ids = book_ids
        self.prompt_template = prompt_template
        self.api_manager = APIManager()
        
        # Results storage: { book_id: summary_text or error_msg }
        self.results = {}
        
        # Signal to UI
        self.current_book_title = ""

    def run(self):
        """
        Main execution loop in background thread.
        """
        try:
            db = self.gui.current_db
            total = len(self.book_ids)
            
            for index, book_id in enumerate(self.book_ids):
                # Update progress
                self.update_progress(index / total)
                
                # 1. Get Metadata
                # We need to access DB safely. ThreadedJob allows access to db usually 
                # but better to minimize read time.
                # NOTE: Accessing gui.current_db from thread is generally safe for reads in Calibre 
                # but writes must be on main thread.
                mi = db.get_metadata(book_id, index_is_id=True)
                title = mi.title
                self.current_book_title = title
                self.description = f"Processing: {title}"
                
                # 2. Format Prompt
                # Simple format for now
                authors = ", ".join(mi.authors)
                prompt = self.prompt_template.format(
                    title=title, 
                    authors=authors, 
                    publisher=mi.publisher,
                    pubdate=mi.pubdate,
                    series=mi.series
                )
                
                # 3. Call API
                try:
                    summary = self.api_manager.generate_summary(prompt)
                    self.results[book_id] = {'success': True, 'content': summary, 'title': title}
                except Exception as e:
                    self.results[book_id] = {'success': False, 'error': str(e), 'title': title}
            
            self.update_progress(1.0)
            
        except Exception as e:
            # Fatal error
            self.results['fatal_error'] = str(e)

    def description(self):
        return "SmartSummary Pro: Generating Book Summaries..."
