from .api_manager import APIManager

class GenerationWorker:
    """
    Background worker for generating book summaries.
    Compatible with Calibre 8.x job_manager.run_threaded_job() API.
    """
    def __init__(self, gui, book_ids, prompt_template):
        self.gui = gui
        self.book_ids = book_ids
        self.prompt_template = prompt_template
        self.api_manager = APIManager()
        
        # Results storage: { book_id: summary_text or error_msg }
        self.results = {}
        
        # Job status
        self.failed = False
        self.was_aborted = False
        
    def __call__(self):
        """
        Main execution method called by job_manager in background thread.
        This replaces the old ThreadedJob.run() method.
        """
        try:
            db = self.gui.current_db
            total = len(self.book_ids)
            
            for index, book_id in enumerate(self.book_ids):
                # Check if job was cancelled
                if getattr(self, 'was_aborted', False):
                    break
                
                # 1. Get Metadata
                # Accessing gui.current_db from thread is safe for reads in Calibre
                # but writes must be on main thread.
                mi = db.get_metadata(book_id, index_is_id=True)
                title = mi.title
                
                # 2. Format Prompt
                authors = ", ".join(mi.authors) if mi.authors else "Unknown"
                
                # Prepare template variables
                template_vars = {
                    'title': title,
                    'authors': authors,
                    'publisher': mi.publisher or "Unknown",
                    'pubdate': str(mi.pubdate) if mi.pubdate else "Unknown",
                    'series': mi.series or "None"
                }
                
                # Safe formatting - only use variables that exist in template
                try:
                    prompt = self.prompt_template.format(**template_vars)
                except KeyError as e:
                    # If template has a key that doesn't exist, provide helpful error
                    raise Exception(f"Template variable {e} not found. Available variables: {', '.join(template_vars.keys())}")
                
                # 3. Call API
                try:
                    summary = self.api_manager.generate_summary(prompt)
                    self.results[book_id] = {
                        'success': True, 
                        'content': summary, 
                        'title': title
                    }
                except Exception as e:
                    self.results[book_id] = {
                        'success': False, 
                        'error': str(e), 
                        'title': title
                    }
            
        except Exception as e:
            # Fatal error
            self.failed = True
            self.results['fatal_error'] = str(e)

